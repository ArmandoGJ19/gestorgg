from fastapi import APIRouter, HTTPException, status, Depends
import pandas as pd
import matplotlib.pyplot as plt
# user
from models.user_model import TokenData
from controllers.user_controller import get_current_user

from controllers.entrenamientos.prophet import preprocess_data, load_model, plot_forecast

from database.conectiondb import transactions, category, predictions_prophet
from bson import ObjectId
from utilities.common import convert_object_id_to_string
from datetime import datetime
import json

router = APIRouter()


def get_transactions_list_v2(current_id):
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

    transactions_df = pd.DataFrame(transactions_list)
    return transactions_df


@router.get("/finance/prediction/prophet_model_v2")
async def get_prophet_prediction_v2(current_user: TokenData = Depends(get_current_user)):
    try:
        # Obtener transacciones del usuario y convertirlas a DataFrame
        transactions_df = get_transactions_list_v2(current_user.user_id)

        # fechas estén en el formato correcto
        transactions_df['fecha'] = pd.to_datetime(transactions_df['fecha'])

        # Preprocesar datos
        gastos_diarios = preprocess_data(transactions_df)

        # Cargar modelo
        best_model = load_model('modelo_prophet_v2.pkl')
        start_date_str = datetime.now().strftime('%Y-%m-%d')
        # Realizar predicción para el próximo mes desde hoy
        start_date = pd.to_datetime(start_date_str)
        periods = 30  # 30 días para un mes
        future = best_model.make_future_dataframe(periods=periods)

        # Asegurarse de que el dataframe futuro comience desde hoy
        future = future[future['ds'] >= start_date]

        if future.empty:
            future = best_model.make_future_dataframe(periods=periods, freq='D', include_history=False)
            future['ds'] = pd.date_range(start=start_date, periods=periods, freq='D')

        forecast = best_model.predict(future)

        # Convertir forecast a JSON serializable
        forecast_json = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_json(date_format='iso', orient='split')

        # Guardar la predicción en MongoDB
        prediction_data = {
            "user_id": current_user.user_id,
            "forecast": json.loads(forecast_json),
            "created_at": datetime.now()
        }

        insert_result = predictions_prophet.insert_one(prediction_data)

        if insert_result.inserted_id:
            return {
                "forecast": json.loads(forecast_json),
                "message": "Predicción realizada correctamente",
                "prediction_id": str(insert_result.inserted_id)
            }
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Error al guardar la predicción")
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Obtener la última predicción de la base de datos
@router.get("/finance/prediction/prophet_model_v2/last")
async def get_last_prediction_v2(current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        # Obtener la última predicción ordenando por 'created_at' en orden descendente
        prediction = predictions_prophet.find_one({"user_id": current_user.user_id}, sort=[("created_at", -1)])

        if not prediction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Predicción no encontrada")

        prediction["_id"] = str(prediction["_id"])
        return prediction
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
