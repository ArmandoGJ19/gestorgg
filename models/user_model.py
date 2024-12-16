from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class UserRegistrationSchema(BaseModel):
    username: str = Field(...)
    name: str = Field(...)
    lastname: str = Field(...)
    password: str = Field(...)
    email: str = Field(...)
    role: str = Field(...)
    reset_token: str = Field(default=None)
    verification_code: str = Field(default=None)
    is_verified: bool = Field(default=False)
    verification_code_expires_at: datetime = Field(default=None)
    send_reports: bool = Field(default=True)
    # subscription_status: bool = Field(default=False)
    # subscription_plan: str = Field(...)
    # user_picture: str = Field(default=None)


class UserEditSchema(BaseModel):
    name: str = Field(...)
    lastname: str = Field(...)


# class UserEditPictureSchema(BaseModel):
#     user_picture: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str
    username: str = None
    role: str


class UserLoginSchema(BaseModel):
    email: str
    password: str


class BlacklistedToken(BaseModel):
    token: str


class ForgotPasswordSchema(BaseModel):
    email: str


class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str


class Message(BaseModel):
    message: str


class VerifyEmailSchema(BaseModel):
    email: EmailStr
    code: str


class ResendCodeRequest(BaseModel):
    email: EmailStr

class SendReports(BaseModel):
    send_reports: bool

# class SuscriptionUser(BaseModel):
#     subscription_status: bool = Field(default=False)
#     subscription_plan: str = Field(...)
#     payment_method: str = Field(...)
#     start_date: datetime = Field(default_factory=datetime.now)
#     end_date: datetime = Field(default=None)
#     last_payment_date: datetime = Field(default_factory=datetime.now)