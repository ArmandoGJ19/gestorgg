
from fastapi import APIRouter, Depends, HTTPException, status
from database.conectiondb import db
from models.user_model import TokenData
from controllers.user_controller import get_current_user
from utilities.gastos_hormiga import detectar_gastos_hormiga
from utilities.consejos import obtener_respuesta_gpt3_automatica
from utilities.gastos_hormiga import obtener_respuesta_gpt3_con_analisis_de_gastos
router = APIRouter()


@router.post("/preguntar")
async def preguntar(current_user: TokenData = Depends(get_current_user)):
    user_id = current_user.user_id
    try:
        # Verifica si el usuario está autenticado
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        # Verifica que el user_id es válido
        if not user_id or not isinstance(user_id, str):
            raise ValueError("Invalid user_id")

        # Obtiene la respuesta de utilizando la función modificada
        respuesta = obtener_respuesta_gpt3_automatica(user_id)

        # Valida la respuesta antes de guardar en la base de datos
        if not respuesta:
            raise ValueError("No se obtuvo respuesta del servidor")

        # Guarda la pregunta y la respuesta en la base de datos
        db.respuestas.insert_one({"user_id": user_id, "pregunta": "Consulta automática", "respuesta": respuesta})

        # Devuelve la respuesta
        return {"respuesta": respuesta}

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        # Maneja cualquier otro error que pueda ocurrir
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/preguntar_gasto_hormiga")
async def preguntar_gasto_hormiga(current_user: TokenData = Depends(get_current_user)):

    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        if not current_user.user_id or not isinstance(current_user.user_id, str):
            raise ValueError("Invalid user_id")

        respuesta = obtener_respuesta_gpt3_con_analisis_de_gastos(current_user.user_id)

        # Valida la respuesta antes de guardar en la base de datos
        if not respuesta:
            raise ValueError("No se obtuvo respuesta del servidor")
        # Devuelve la respuesta
        return {"respuesta": respuesta}

    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        # Maneja cualquier otro error que pueda ocurrir
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


