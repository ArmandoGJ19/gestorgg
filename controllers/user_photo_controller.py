from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from models.user_model import TokenData
from controllers.user_controller import get_current_user
from database.conectiondb import users
from bson import ObjectId
import cloudinary
import cloudinary.uploader as up
import os
import uuid
from decouple import config
# Configuración Cloudinary
cloudinary.config(
    cloud_name=config('CLOUD_NAME'),
    api_key=config('API_KEY'),
    api_secret=config('API_SECRET')
)

router = APIRouter()


async def upload_photo(photo_user: UploadFile, current_user: TokenData):
    if not photo_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File not found")

    # Validar que exista el campo de photo en la bd
    exist_user = users.find_one({"username": current_user.username})
    file_content = await photo_user.read()
    uploadImg = up.upload(file_content, folder="users_photos")

    return exist_user, uploadImg


async def update_photo(photo_user: UploadFile, current_user: TokenData):
    exist_user, uploadImg = await upload_photo(photo_user, current_user)

    # Si el usuario no tiene el campo foto, sube la imagen
    if not exist_user.get("photo"):
        if uploadImg:
            unique_filename = uploadImg['public_id']
            users.update_one({"_id": ObjectId(current_user.user_id)},
                             {"$set": {"photo": unique_filename}})
            return {"message": "Photo Created successfully"}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File not found")

    # Si el usuario ya tiene la foto, actualiza la imagen
    if exist_user.get("photo"):
        old_photo = exist_user.get("photo")
        if old_photo:
            delete = up.destroy(old_photo)
            if delete:
                # Sube la imagen
                if uploadImg:
                    unique_filename = uploadImg['public_id']
                    users.update_one({"_id": ObjectId(current_user.user_id)},
                                     {"$set": {"photo": unique_filename}})
                    return {"message": "Photo updated successfully"}
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File not found")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File not found")


# Función para subir la foto del usuario
@router.post("/finance/user/photo", response_model=dict)
async def user_photo_add(photo_user: UploadFile = File(...), current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            if not photo_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File not found")
            return await update_photo(photo_user, current_user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Función para eliminar la foto del usuario
@router.delete("/finance/user/photo-delete", response_model=dict)
async def user_photo_delete(current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            exist_user = users.find_one({"username": current_user.username})
            exist_img = exist_user.get("photo")
            if exist_img:
                up.destroy(exist_img)
                users.update_one({"_id": ObjectId(current_user.user_id)}, {"$unset": {"photo": ""}})
                return {"message": "Photo deleted successfully"}
            return {"photo": None}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Función para ver la foto del usuario
@router.get("/finance/user/photo", response_model=dict)
async def user_photo(current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            exist_user = users.find_one({"username": current_user.username})
            exist_img = exist_user.get("photo")
            if exist_img:
                user_cloudinary = config("CLOUD_NAME")
                url = f"https://res.cloudinary.com/{user_cloudinary}/image/upload/{exist_img}"
                return {"photo": url}
            return {"photo": None}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))