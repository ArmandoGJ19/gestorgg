import json

from controllers.training import get_transactions_list_v2
import openai
from decouple import config
from bson import ObjectId
openai.api_key = config('OPENAI')
from datetime import datetime
import pandas as pd
import re
def obtener_respuesta_gpt3_con_prediciones(user_id):
    transacciones = get_transactions_list_v2(user_id)
    actual_date = datetime.now()
    if transacciones.empty:
        return {"message": "No se encontraron transacciones para analizar."}

    transacciones_str = transacciones.to_string(index=False)
    prompt = f"""
        A continuación se presentan los datos históricos de transacciones del cliente. Cada transacción incluye la
         fecha, el monto y el nombre de la categoría del gasto. Usa estos datos para predecir los gastos futuros del
          cliente para el próximo mes. Considera las tendencias y patrones observados en los datos históricos
           para tratar de hacer predicciones lo mas precisas posibles.:

        {transacciones_str}

        Por favor, proporciona una predicción detallada por categoria, solo de los gastos del cliente en un lapso de un mes,
         teniendo en cuenta el dia actual en el que se hace la predicción f{actual_date}, considerando las categorías
          y montos promedio basados en los datos proporcionados. El formato debe ser el siguiente:
        {{
            "user_id": "user_id",
            "predictions": {{
                    "name": {{
                        "category_name": "name",
                        "predicted_amount": <monto_predecido>
                    }}
            }}
        }}
        """
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON"},
            {"role": "user", "content": prompt},
        ]
    )
    return response.choices[0].message.content