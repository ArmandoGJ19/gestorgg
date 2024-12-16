import json

import openai
from fastapi import APIRouter, HTTPException, status, Depends
from controllers.user_controller import get_current_user
from controllers.user_controller import TokenData
from utilities.predictions import obtener_respuesta_gpt3_con_prediciones
from database.conectiondb import db
router = APIRouter()

@router.get("/finance/predict_spens")
async def predict_spens(current_user: TokenData = Depends(get_current_user)):
    user_id = current_user.user_id
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if not user_id or not isinstance(user_id, str):
            raise ValueError("Invalid user_id")

        # Obtiene la respuesta de utilizando la función modificada
        respuesta = obtener_respuesta_gpt3_con_prediciones(user_id)

        # Valida la respuesta antes de guardar en la base de datos
        if not respuesta:
            raise ValueError("No se obtuvo respuesta del servidor")

        try:
            respuesta_json = json.loads(respuesta)
        except json.JSONDecodeError:
            raise ValueError("La respuesta no es un objeto JSON válido")

        # Guarda la pregunta y la respuesta en la base de datos
        db.predictions.insert_one({"user_id": user_id, "predictions": respuesta_json})

        # Devuelve la respuesta
        return respuesta_json
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

