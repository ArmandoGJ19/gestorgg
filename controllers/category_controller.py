from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder

from database.conectiondb import category
from database.conectiondb import transactions
from models.category_model import CategoryCreate, CategoryEdit, CategoryDelete
from models.user_model import TokenData
from controllers.user_controller import get_current_user
from utilities.common import convert_object_id_to_string
from validations.category_validations import validate_category,validate_update_category

router = APIRouter()


# view categorias
def get_user_categories_list(user_id):
    categories_cursor = category.find({"user_id": user_id})
    categories_list = list(categories_cursor)

    for categories in categories_list:
        convert_object_id_to_string(categories, "category_id")

    return categories_list


@router.get("/finance/category")
async def get_user_categories(
    current_user: TokenData = Depends(get_current_user)
):
    try:
        # Verificar si el usuario está autenticado y si el user_id del token coincide con el user_id proporcionado en el cuerpo
        if current_user:
            user_categories = get_user_categories_list(current_user.user_id)
            # if user_categories:
            return jsonable_encoder(user_categories)
            # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="the user has no registered categories")

        # Si no cumple las condiciones anteriores, lanzar una excepción de autorización
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# add categorias
@router.post("/finance/category/add", response_model=dict)
async def create_category(category_data: CategoryCreate, current_user: TokenData = Depends(get_current_user)):
    try:
        # Verificar si el usuario está autenticado
        if current_user:
            existing_category = category.find_one(
                {"category_name": category_data.category_name,
                 "user_id": current_user.user_id}
            )

            if existing_category:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="category_name already exists for this user")

            new_category = {
                "category_name": category_data.category_name,
                "type": category_data.type,
                "user_id": current_user.user_id
            }
            validate_category(new_category)
            inserted_category = category.insert_one(new_category)
            if inserted_category:
                # Obtener el _id generado por MongoDB y agregarlo al diccionario
                new_category["_id"] = str(inserted_category.inserted_id)
                return {"message": "Category created successfully"}

            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create category")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# edit categorias
@router.put("/finance/category/edit/{category_id}", response_model=dict)
async def edit_category(category_id: str, updated_category: CategoryEdit, current_user: TokenData = Depends(get_current_user)):
    try:
        # Verificar si el usuario está autenticado
        if current_user:
            # Buscar otras categorías con el mismo nombre y usuario
            existing_category = category.find_one(
                {"category_name": updated_category.category_name, "username": current_user.username}
            )

            # Verificar si la categoría ya existe
            if existing_category and str(existing_category["_id"]) != category_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="category_name already exists for this user")

            # Actualizar solo el nombre de la categoría con la nueva información

            updated_category = {
                "category_name": updated_category.category_name,
                "type": updated_category.type
            }
            validate_update_category(updated_category)

            # Actualizar solo el nombre de la categoría con la nueva información
            category.update_one(
                {"_id": ObjectId(category_id)},
                {"$set": updated_category})

            return {"message": "Category updated successfully"}

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# delete categorias
@router.delete("/finance/category/delete/{category_id}", response_model=dict)
async def delete_category(category_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        # Verificar si el usuario está autenticado
        if current_user:
            # Convertir el category_id a ObjectId
            category_id_object = ObjectId(category_id)

            # Verificar si la categoría existe y pertenece al usuario actual
            existing_category = category.find_one({"_id": category_id_object, "user_id": current_user.user_id})

            if not existing_category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

            # Verificar si la categoría tiene una transacción
            exist_cat_transaccion = transactions.find_one({"category_id": category_id})
            if exist_cat_transaccion:
                transactions_id = ObjectId(exist_cat_transaccion.get("_id"))
                print('se elimino la transaccion: ', transactions_id)
                transactions.delete_one({"_id": transactions_id})

            # Eliminar la categoría
            category.delete_one({"_id": category_id_object})

            return {"message": "Category deleted successfully"}

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
