from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from database.conectiondb import blacklisted_tokens, users
from utilities.common import convert_object_id_to_string
from models.user_model import (UserLoginSchema, UserRegistrationSchema, Token, TokenData, BlacklistedToken,
                               UserEditSchema, ForgotPasswordSchema, ResetPasswordSchema, Message, VerifyEmailSchema,
                               ResendCodeRequest)
from validations.user_validations import validate_user, validate_update_user
from utilities.mail_verification import send_verification_email, generate_verification_code
from datetime import timedelta, datetime
from jose import jwt, JWTError
from starlette.responses import JSONResponse, Response
import bcrypt
from bson import ObjectId
# descomentar para cuando se soluciones el error con .env y decouple
from decouple import config
import smtplib
from email.mime.text import MIMEText
import secrets

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# por el momento no se puede exportar desde el .env, queda pendiente revisar el error que da
SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(config('ACCESS_TOKEN_EXPIRE_MINUTES'))
EMAIL = config("EMAIL")
PASSWORD_GMAIL = config("PASSWORD_GMAIL")


def is_token_blacklisted(token: str):
    query = {"token": token}
    token_in_blacklist = blacklisted_tokens.find_one(query)
    return token_in_blacklist is not None


# Función para crear un token JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "role": data.get("role"), "user_id": data.get("user_id")})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Función para obtener el usuario actual desde el token JWT
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if is_token_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: str = payload.get("user_id")
        if username is None or role is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, username=username, role=role)
    except JWTError:
        raise credentials_exception
    return token_data


def get_users_list():
    users_cursor = users.find()
    users_list = list(users_cursor)

    for user in users_list:
        convert_object_id_to_string(user, "user_id")  # Especificamos que queremos "user_id"

    return users_list


@router.get("/finance/users")
async def get_users(current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user and current_user.role == "admin":
            user_list = get_users_list()
            return JSONResponse(content=jsonable_encoder(user_list))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as e:

        return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/finance/users/me")
async def get_user(current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user and current_user.role == "admin":
            user = users.find_one({"_id": ObjectId(current_user.user_id)})
            convert_object_id_to_string(user, "_id")
            return JSONResponse(content=jsonable_encoder(user))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as e:

        return JSONResponse(content={"detail": e.detail}, status_code=e.status_code)

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/finance/register", response_model=Message)
async def register_user(user: UserRegistrationSchema):
    try:
        validate_user(user.dict())

        existing_user = users.find_one({"$or": [{"username": user.username}, {"email": user.email}]})
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")

        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

        verification_code = generate_verification_code()
        verification_code_expires_at = datetime.utcnow() + timedelta(minutes=3)
        new_user = {
            "username": user.username,
            "name": user.name,
            "lastname": user.lastname,
            "password": hashed_password.decode('utf-8'),
            "email": user.email,
            "role": user.role,
            "verification_code": verification_code,
            "verification_code_expires_at": verification_code_expires_at,
            "is_verified": False,
            "send_reports": True,
            "subscription_status": False,
            "subscription_plan": "free"
        }
        print(new_user)
        users.insert_one(new_user)

        result = send_verification_email(user.email, verification_code)
        print(result)
        return {"message": "Please check your email for the verification code."}

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/finance/login")
async def login_user(user_credentials: UserLoginSchema, response: Response):
    try:
        user = users.find_one({"email": user_credentials.email})
        if user is None or not bcrypt.checkpw(user_credentials.password.encode('utf-8'),
                                              user['password'].encode('utf-8')):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.get("is_verified"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

        # Genera un token JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"], "user_id": str(user["_id"])},
            expires_delta=access_token_expires,
        )

        return {"message": "Login successful", "access_token": access_token, "user_name": user["name"]}

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/finance/logout")
async def logout_user(token: str = Depends(oauth2_scheme)):
    # Eliminar la cookie del token JWT
    blacklisted_token = BlacklistedToken(token=token)
    blacklisted_tokens.insert_one(blacklisted_token.dict())

    return {"message": "Logout successful"}


@router.put("/finance/users/edit", response_model=dict)
async def user_edit(updated_user: UserEditSchema, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            exist_user = users.find_one({"username": current_user.username})
            if exist_user and exist_user["_id"] != ObjectId(current_user.user_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="User name already exists")
            print(updated_user)

            update_user = {
                "name": updated_user.name,
                "lastname": updated_user.lastname,
            }
            print(update_user)
            # validate_update_user(update_user)

            users.update_one({"_id": ObjectId(current_user.user_id)},
                             {"$set": update_user})

            return {"message": "User updated successfully"}

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def send_recovery_email(email_to: str, link: str):
    sender = EMAIL
    password = PASSWORD_GMAIL
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)

    message = MIMEText(f"Please use the following link to reset your password: {link}")
    message['From'] = sender
    message['To'] = email_to
    message['Subject'] = "Reset Your Password"

    server.sendmail(sender, email_to, message.as_string())
    server.quit()


@router.post("/finance/forgot-password")
async def forgot_password(request_body: ForgotPasswordSchema):
    try:
        email = request_body.email
        user = users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        reset_token = secrets.token_urlsafe()
        # reset_link = f"http://localhost:3000/finance/reset-password?token={reset_token}"
        reset_link = f"http://localhost:3000/gg/resetearcontraseña?token={reset_token}"

        # Store the token in the database with an expiration time
        users.update_one({"_id": user["_id"]}, {
            "$set": {"reset_token": reset_token, "token_expires": datetime.utcnow() + timedelta(hours=1)}})

        send_recovery_email(email, reset_link)
        return {
            "message": "Si el correo existe en la base de datos, se ha enviado un enlace para restablecer su contraseña"}

    except HTTPException as http_error:

        raise http_error

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/finance/reset-password")
async def reset_password(body: ResetPasswordSchema):
    try:
        user = users.find_one({"reset_token": body.token, "token_expires": {"$gt": datetime.utcnow()}})
        if not user:
            raise HTTPException(status_code=404, detail="Token is invalid or has expired")

        new_hashed_password = bcrypt.hashpw(body.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        users.update_one({"_id": user["_id"]},
                         {"$set": {"password": new_hashed_password, "reset_token": None, "token_expires": None}})
        return {"message": "Tu conteña se ha restablecido correctamente"}

    except HTTPException as http_error:

        raise http_error

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/finance/verify-email", response_model=Message)
async def verify_email(verify_data: VerifyEmailSchema):
    print(f"Received data: {verify_data}")
    user = users.find_one({"email": verify_data.email})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    current_time = datetime.utcnow()
    if user.get("verification_code") == verify_data.code:
        if user.get("verification_code_expires_at") > current_time:
            print(user.get("verification_code"), verify_data.code)
            users.update_one({"email": verify_data.email}, {"$set": {"is_verified": True}})
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")


@router.post("/finance/resend-verification-code", response_model=Message)
async def resend_verification_code(request: ResendCodeRequest):
    email = request.email
    print(f"Email: {email}")
    try:
        user = users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.get("is_verified"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
        verification_code = generate_verification_code()
        verification_code_espires = datetime.utcnow() + timedelta(minutes=3)

        users.update_one({"email": email}, {"$set": {"verification_code": verification_code,
                                                     "verification_code_expires_at": verification_code_espires}})

        result = send_verification_email(email, verification_code)
        print(result)
        return {"message": "Verification code sent successfully"}

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
