from datetime import datetime, timedelta
from database.conectiondb import transactions, category
import openai
from decouple import config
from bson import ObjectId
openai.api_key = config('OPENAI')


def detectar_gastos_hormiga(user_id):
    collection = transactions
    collection_category = category

    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=1)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    pipeline = [
        {"$match": {
            "user_id": user_id,
            "fecha": {"$gte": start_date_str, "$lte": end_date_str},
            "type": "gasto",
            "monto": {"$lt": 100}
        }},
        {"$group": {
            "_id": "$category_id",
            "count": {"$sum": 1},
            "transacciones": {"$push": "$$ROOT"}
        }},
        {"$match": {
            "count": {"$gte": 3}
        }}
    ]
    resultados = collection.aggregate(pipeline)
    gastos_hormiga = []

    for resultado in resultados:
        categoria = collection_category.find_one({"_id": ObjectId(resultado["_id"])})
        category_name = categoria["category_name"] if categoria else "Categoría no especificada"
        count = resultado["count"]  # Obtiene el conteo de transacciones para esta categoría
        for transaccion in resultado["transacciones"]:
            transaccion["category_name"] = category_name
            transaccion["count"] = count  # Agrega el conteo a cada transacción
        gastos_hormiga.extend(resultado["transacciones"])

    return gastos_hormiga


def sintetizar_gastos_hormiga(gastos_hormiga):
    sintesis = {}
    for gasto in gastos_hormiga:
        categoria = gasto.get("category_name", "Categoría no especificada")
        if categoria not in sintesis:
            sintesis[categoria] = 0
        sintesis[categoria] += 1
    return sintesis


def generar_prompt_gpt3(gastos_sintetizados):
    prompt = "Resumen de gastos hormiga en la última semana: "
    if gastos_sintetizados:
        for categoria, conteo in gastos_sintetizados.items():
            prompt += f'Categoría "{categoria}" con {conteo} transacciones menores a $100. '
    else:
        prompt += "No se detectaron gastos hormiga significativos. "
    prompt += ("Por favor, dime en qué categoría o categorías tengo un gasto hormiga y cuántas veces se repitió. "
               "Además, ¿cómo puedo mejorar mis hábitos de gasto basándome en esta información? "
               "Sé realmente breve y da un consejo solamente.")
    return prompt


def obtener_respuesta_gpt3_con_analisis_de_gastos(user_id):
    gastos_hormiga = detectar_gastos_hormiga(user_id)
    if not gastos_hormiga:
        return "No se detectaron gastos hormiga significativos en la última semana."

    gastos_sintetizados = sintetizar_gastos_hormiga(gastos_hormiga)
    prompt = generar_prompt_gpt3(gastos_sintetizados)

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
