from datetime import datetime
import dateutil.relativedelta
from database.conectiondb import db
import openai
from decouple import config
openai.api_key = config('OPENAI')

def calcular_ingresos_totales(user_id):
    # inicio_mes = datetime.datetime.now().replace(day=1)
    # fin_mes = (inicio_mes + dateutil.relativedelta.relativedelta(months=1, days=-1)).date()

    # definir las fechas de inicio y fin
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin_mes = (inicio_mes + dateutil.relativedelta.relativedelta(months=1, days=-1)).replace(hour=23, minute=59,
                                                                                             second=59,
                                                                                           microsecond=999999)
    # Convertir a formato de cadena para que las acepte el mongo
    inicio_mes_str = inicio_mes.strftime("%Y-%m-%d")
    fin_mes_str = fin_mes.strftime("%Y-%m-%d")
    # consulta
    pipeline = [
        {"$match": {"user_id": user_id, "fecha": {"$gte": inicio_mes_str, "$lte": fin_mes_str}, "type": "ingreso"}},
        {"$group": {"_id": None, "total_ingreso": {"$sum": "$monto"}}}
    ]
    # realizar la consulta
    resultados = db.transactions.aggregate(pipeline)

    total_ingresos = 0
    # recorrer los resultados para regresar el total
    for resultado in resultados:
        total_ingresos = resultado.get("total_ingreso", 0)
    return total_ingresos


def analizar_habitos_de_gastos(user_id):
    hoy = datetime.now()
    # inicio_mes = hoy.replace(day=1)
    # fin_mes = (inicio_mes + dateutil.relativedelta.relativedelta(months=1, days=-1)).date()
    # definir las fechas de inicio y fin
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin_mes = (inicio_mes + dateutil.relativedelta.relativedelta(months=1, days=-1)).replace(hour=23, minute=59,
                                                                                             second=59,
                                                                                             microsecond=999999)
    # Convertir a formato de cadena para que las acepte el mongo
    inicio_mes_str = inicio_mes.strftime("%Y-%m-%d")
    fin_mes_str = fin_mes.strftime("%Y-%m-%d")
    # consulta
    pipeline = [
        {"$match": {"user_id": user_id, "fecha": {"$gte": inicio_mes_str, "$lte": fin_mes_str}, "type": "gasto"}},
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
            "total_gasto": {"$sum": "$monto"}
        }}
    ]
    # realizar la consulta
    resultados = db.transactions.aggregate(pipeline)

    resumen = {}
    for resultado in resultados:
        categoria_nombre = resultado["_id"]
        gasto_total = resultado["total_gasto"]
        resumen[categoria_nombre] = gasto_total
    # Analizar patrones y definir consejos
    consejos = []
    umbral_de_gasto = calcular_ingresos_totales(user_id) * 0.3
    umbral_porcentaje_categoria = 0.40
    for categoria, gasto in resumen.items():
        if gasto > umbral_de_gasto:
            consejos.append(f"Considera reducir tus gastos en {categoria}.")
        elif gasto > umbral_de_gasto * umbral_porcentaje_categoria:
            consejos.append(f"El gasto en {categoria} es alto. Considera ajustar tus gastos.")

    return consejos, resumen


def obtener_respuesta_gpt3_automatica(user_id):
    # Calcula los ingresos totales y analiza los hábitos de gastos
    consejos, resumen = analizar_habitos_de_gastos(user_id)
    ingresos_totales = calcular_ingresos_totales(user_id)
    # Construye un prompt detallado con la información financiera del usuario
    prompt = f"Ingresos totales este mes: ${ingresos_totales}. "
    prompt += "Desglose de gastos por categoría: "
    prompt += ', '.join([f'{cat}: ${monto}' for cat, monto in resumen.items()]) + ". "
    prompt += "Consejos: " + ', '.join(consejos) + ". "
    prompt += ("¿Cuáles son mis gastos e ingresos este mes y que recomendaciones me das?"
               " dame la formación en esta estructura,-ingresos totales -> $, -gastos totales son -> $ "
               " -desglose -> comida = $ -consejos -> , solo da la recomendacion"
               " indicando en que categoria se requiere el ajuste de gastos siendo"
               " breve y no pongas palabras como Mi, te recomiendo o cosas de ese estilo.  ")

    # Envía el prompt a GPT-3 y obtén la respuesta
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
