from bson import ObjectId
from fastapi import HTTPException, Depends, APIRouter, status, Path
from models.transactions_model import TransactionSchema,GraficTransaction
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from models.user_model import TokenData
from controllers.user_controller import get_current_user
from database.conectiondb import transactions, db
from database.conectiondb import category
from utilities.common import get_item_by_id
from typing import List
from utilities.common import convert_object_id_to_string
from bson.errors import InvalidId
from datetime import datetime
from dateutil import relativedelta
import dateutil
router = APIRouter()


def get_total_spent_by_category_month(user_id):
    hoy_grafica = datetime.now()
    inicio_mes = hoy_grafica.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin_mes = (inicio_mes + dateutil.relativedelta.relativedelta(months=1, days=-1)).replace(hour=23, minute=59,
                                                                                             second=59,
                                                                                             microsecond=999999)
    inicio_mes_str = inicio_mes.strftime("%Y-%m-%d")
    fin_mes_str = fin_mes.strftime("%Y-%m-%d")
    pipeline = [
        {"$match": {"user_id": user_id, "fecha": {"$gte": inicio_mes_str, "$lte": fin_mes_str}}},
        {"$addFields": {"converted_category_id": {"$toObjectId": "$category_id"}}},
        {"$lookup": {
            "from": "category",
            "localField": "converted_category_id",
            "foreignField": "_id",
            "as": "category_info"
        }},
        {"$unwind": "$category_info"},
        {"$group": {
            "_id": "$category_info.category_name",
            "total": {"$sum": "$monto"}
        }},
        {"$sort": {"total": -1}}
    ]
    consulta = list(db.transactions.aggregate(pipeline))
    return consulta


def get_total_spent_by_category_v(user_id):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$addFields": {"converted_category_id": {"$toObjectId": "$category_id"}}},
        {"$lookup": {
            "from": "category",
            "localField": "converted_category_id",
            "foreignField": "_id",
            "as": "category_info"
        }},
        {"$unwind": "$category_info"},
        {"$group": {
            "_id": "$category_info.category_name",
            "total": {"$sum": "$monto"}
        }},
        {"$sort": {"total": -1}}
    ]
    consulta = list(db.transactions.aggregate(pipeline))
    return consulta


def get_transactions_list(current_id):
    transactions_cursor = transactions.find({"user_id": current_id})
    transactions_list = list(transactions_cursor)

    for transaction in transactions_list:
        category_id = transaction.get("category_id")
        cat = category.find_one({"_id": ObjectId(category_id)})

        if cat:
            transaction["category_name"] = cat["category_name"]
        else:
            transaction["category_name"] = "Categoría no encontrada"
        convert_object_id_to_string(transaction, "transaction_id")

    return transactions_list


from bson import ObjectId


def get_last_transactions_list(current_id, is_income):
    # Determina el tipo de transacción basado en el valor de is_income
    transaction_type = "ingreso" if is_income else "gasto"

    # Busca las transacciones del usuario actual, filtrando por tipo y ordenando por fecha en orden descendente
    transactions_cursor = transactions.find({"user_id": current_id, "type": transaction_type}).sort("date", -1).limit(5)

    # Convierte el cursor a una lista
    transactions_list = list(transactions_cursor)

    for transaction in transactions_list:
        # Obtiene el ID de la categoría de la transacción
        category_id = transaction.get("category_id")

        if category_id:
            # Busca la categoría correspondiente en la colección de categorías
            cat = category.find_one({"_id": ObjectId(category_id)})

            if cat:
                # Si la categoría se encuentra, agrega su nombre a la transacción
                transaction["category_name"] = cat.get("category_name", "Nombre de categoría no encontrado")
            else:
                # Si la categoría no se encuentra, asigna un mensaje de error
                transaction["category_name"] = "Categoría no encontrada"
        else:
            # Si no hay categoría ID, asigna un mensaje de error
            transaction["category_name"] = "Categoría no especificada"

        # Convierte el ObjectId de la transacción a string
        convert_object_id_to_string(transaction, "transaction_id")

    return transactions_list


def validate_category_id(category_id: str) -> None:

    try:
        category_record = category.find_one({"_id": ObjectId(category_id)})
        if not category_record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Category ID does not exist")
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid category ID format")


@router.post("/finance/transaction", response_model=TransactionSchema)
async def create_transaction(transaction: TransactionSchema, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            # buscar que la categoria exista en la bd
            validate_category_id(transaction.category_id)
            # category_id = category.find_one({"_id": ObjectId(transaction.category_id)})
            # if not category_id:
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            #                         detail="Category ID does not exist")

            transaction_data = jsonable_encoder(transaction)
            # poner el id del usuario logueado en el parametro user_id de la transaccion
            transaction_data["user_id"] = current_user.user_id
            # insertar la transaccion
            new_transaction = transactions.insert_one(transaction_data)
            # print(new_transaction)
            # si no se insertó, manda el mensaje de error
            if not new_transaction:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail="Failed to insert transaction")
            # caso contrario retorna un success, mensaje y la data
            transaction_data["_id"] = str(new_transaction.inserted_id)
            return transaction_data

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_e:

        raise http_e

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# obtener una transaccion
@router.get("/finance/transaction/{transaction_id}", response_model=TransactionSchema)
async def get_transaction(transaction_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            transaction_data = transactions.find_one({"_id": ObjectId(transaction_id)})

            if transaction_data:
                return transaction_data
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/finance/last_transactions_user", response_model=List[TransactionSchema])
async def get_last_transactions(is_income: bool, current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        transactions_list = get_last_transactions_list(current_user.user_id, is_income)

        if transactions_list:
            return JSONResponse(content=jsonable_encoder(transactions_list))

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="The user has no registered transactions")
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# obtener todas las transacciones del usuario
@router.get("/finance/transactions_user", response_model=List[TransactionSchema])
async def get_user_transactions(current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        transactions_list = get_transactions_list(current_user.user_id)

        if transactions_list:
            return JSONResponse(content=jsonable_encoder(transactions_list))

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="the user has no registered transactions")
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/finance/delete_transaction/{transaction_id}", response_model=dict)
async def delete_transaction(
        transaction_id: str = Path(..., title="Note ID", description="The ID of the product you want to delete"),
        current_user: TokenData = Depends(get_current_user)
):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        deleted_trantaction = transactions.find_one_and_delete({"_id": ObjectId(transaction_id)})
        if deleted_trantaction:
            convert_object_id_to_string(deleted_trantaction)
            return {"deleted_product": deleted_trantaction}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/finance/updated_transaction/{transaction_id}")
async def update_transaction(transaction_id: str, transaction: TransactionSchema, current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        # funcion validar id de categoria al editar
        validate_category_id(transaction.category_id)
        transaction = jsonable_encoder(transaction)
        transaction["user_id"] = current_user.user_id
        result = transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": transaction}
        )
        if result.modified_count == 1:
            updated_transaction = get_item_by_id(transactions, transaction_id)
            if updated_transaction:
                convert_object_id_to_string(updated_transaction)
                return {"updated_transaction": updated_transaction}
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="transaction not found")
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="transaction not modified")
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# agrupa el monto de las categorias con el mismo id
@router.get("/finance/grafic_user", response_model=List[GraficTransaction])
async def get_data_grafic(current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        grafic = get_total_spent_by_category_v(current_user.user_id)

        if grafic:
            return JSONResponse(content=jsonable_encoder(grafic))

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="the user has no registered data")
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# lo mismo que la de arriba pero mensual
@router.get("/finance/grafic_user_month", response_model=List[GraficTransaction])
async def get_data_grafic_month(current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        grafic = get_total_spent_by_category_month(current_user.user_id)

        if grafic:
            return JSONResponse(content=jsonable_encoder(grafic))

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="the user has no registered data")
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))