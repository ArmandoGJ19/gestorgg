from fastapi import APIRouter, Depends
from database.conectiondb import budgets, category
from models.user_model import TokenData
from controllers.user_controller import get_current_user
from utilities.common import convert_object_id_to_string, convert_objectid_to_str, get_item_by_id
from database.conectiondb import transactions
from models.budget_model import BudgetCreate as bu
from controllers.transaction_controller import validate_category_id
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from datetime import datetime, timedelta
import asyncio

router = APIRouter()


def get_user_budgets_list(user_id):
    budgets_cursor = budgets.find({"user_id": user_id})
    budgets_list = list(budgets_cursor)
    for budget in budgets_list:
        convert_object_id_to_string(budget, "budget_id")

    return budgets_list


# def get_week_start_date():
#     today = datetime.now()
#     week_start_date = today - timedelta(days=today.weekday(), weeks=1)  # Lunes de la semana actual
#     return week_start_date.strftime('%Y-%m-%d')
def get_week_start_date():
    today = datetime.now()
    week_start_date = today - timedelta(days=today.weekday())  # Lunes de la semana actual
    return week_start_date.strftime('%Y-%m-%d')

def get_week_end_date():
    today = datetime.now()
    week_end_date = today + timedelta(days=6-today.weekday())  # Domingo de la semana actual
    return week_end_date.strftime('%Y-%m-%d')

@router.get("/finance/budget")
async def get_budgets(current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            user_budgets = get_user_budgets_list(current_user.user_id)
            if user_budgets:
                return jsonable_encoder(user_budgets)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="the user has no registered budgets")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/finance/budget/add", response_model=dict)
async def create_budget(budget_data: bu, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            # Convertir las fechas a ISO para la comparación
            budget_start = budget_data.date_start.isoformat()
            budget_end = budget_data.date_end.isoformat()

            # Verificar si hay presupuestos activos que se traslapen en fechas para la misma categoría
            overlapping_budgets_count = budgets.count_documents({
                "user_id": current_user.user_id,
                "category_id": budget_data.category_id,
                "$or": [
                    {"date_start": {"$lte": budget_end}, "date_end": {"$gte": budget_start}},
                ]
            })

            if overlapping_budgets_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un presupuesto activo en este rango de fechas para la categoría seleccionada."
                )
            # validar que no se repitan las categorias
            # id_category = budgets.find_one({"category_id": budget_data.category_id})
            # if id_category:
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            #                         detail="This category already exist.")

            new_budget = {
                "budget_name": budget_data.budget_name,
                "amount": budget_data.amount,
                "category_id": budget_data.category_id,
                "date_start": budget_data.date_start.isoformat(),
                "date_end": budget_data.date_end.isoformat(),
                "user_id": current_user.user_id
            }
            print("new_budget" + str(new_budget))
            inserted_budget = budgets.insert_one(new_budget)
            if inserted_budget:
                # Obtener el _id generado por MongoDB y agregarlo al diccionario
                new_budget["_id"] = str(inserted_budget.inserted_id)
                return {"message": "Budget created successfully"}

            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create budget")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/finance/budget/delete/{budget_id}", response_model=dict)
async def delete_budget(budget_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            deleted_budget = budgets.delete_one({"_id": ObjectId(budget_id), "user_id": current_user.user_id})
            if deleted_budget.deleted_count > 0:
                return {"message": "Budget deleted successfully"}
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/finance/budget/edit/{budget_id}")
async def edit_budget(budget_id: str, budget_data: bu, current_user: TokenData = Depends(get_current_user)):
    try:
        budget_start = budget_data.date_start.isoformat()
        budget_end = budget_data.date_end.isoformat()

        # Verificar si hay presupuestos activos que se traslapen en fechas para la misma categoría
        overlapping_budgets_count = budgets.count_documents({
            "user_id": current_user.user_id,
            "category_id": budget_data.category_id,
            "$or": [
                {"date_start": {"$lte": budget_end}, "date_end": {"$gte": budget_start}},
            ]
        })

        if overlapping_budgets_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un presupuesto activo en este rango de fechas para la categoría seleccionada."
            )
        if current_user:
            validate_category_id(budget_data.category_id)
            if budget_data.date_start is not None:
                budget_data.date_start = budget_data.date_start.isoformat()
            if budget_data.date_end is not None:
                budget_data.date_end = budget_data.date_end.isoformat()
            budget_data_dict = {k: v for k, v in budget_data.dict().items() if v is not None}
            updated_budget = budgets.update_one({"_id": ObjectId(budget_id), "user_id": current_user.user_id},
                                                {"$set": budget_data_dict})
            if updated_budget.matched_count > 0:
                return {"message": "Budget updated successfully"}
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/finance/budgets/summary")
async def get_transactions_summary(current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        week_start_date = get_week_start_date()
        week_end_date = get_week_end_date()  # Fecha actual
        print(week_start_date, week_end_date)

        pipeline = [
            {"$match": {
                "user_id": current_user.user_id,
                "fecha": {"$gte": week_start_date, "$lte": week_end_date}
            }},
            {"$group": {
                "_id": "$category_id",
                "total_amount": {"$sum": "$monto"}
            }},
            {"$lookup": {
                "from": "budgets",
                "let": {"category_id": "$_id", "start_date": week_start_date, "end_date": week_end_date},
                "pipeline": [
                    {"$match": {
                        "$expr": {
                            "$and": [
                                {"$eq": ["$category_id", "$$category_id"]},
                                {"$lte": ["$date_start", "$$end_date"]},
                                {"$gte": ["$date_end", "$$start_date"]}
                            ]
                        }
                    }},
                    {"$project": {"amount": 1, "date_start": 1, "date_end": 1}}
                ],
                "as": "budget_info"
            }},
            {"$unwind": "$budget_info"},
            {"$project": {
                "category_id": "$_id",
                "total_amount": 1,
                "budget_amount": "$budget_info.amount",
                "budget_start": "$budget_info.date_start",
                "budget_end": "$budget_info.date_end"
            }}
        ]

        result = list(transactions.aggregate(pipeline))
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="No transactions found for the last week.")
        print(result)
        return jsonable_encoder(result)
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
