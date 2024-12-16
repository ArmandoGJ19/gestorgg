from datetime import datetime, timedelta
from bson import ObjectId
from database.conectiondb import transactions

import pandas as pd


def extract_transactions(user_id):
    collection = transactions
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=1)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    # trasacs = collection.find({"user_id": ObjectId(user_id), "fecha": {"$gte": start_date, "$lt": end_date}})
    trasacs = collection.find({"user_id": user_id, "fecha": {"$gte": start_date_str, "$lt": end_date_str}})
    # print(list(trasacs))
    return list(trasacs)


def prepare_data(transactions_bd: list):
    if not transactions_bd:
        print("No transactions provided.")
        return pd.DataFrame()

    df = pd.DataFrame(transactions_bd)
    # Eliminar las columnas que no se necesitan
    df = df.dropna(subset=['fecha', 'monto'])
    # Convertir la fecha en un formato
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')
    df['day_week'] = df['fecha'].dt.day_name()
    df['week_year'] = df['fecha'].dt.isocalendar().week
    df['hour_day'] = df['fecha'].dt.hour

    # Normalizar el monto
    monto_std = df['monto'].std()
    df['amount_normalized'] = (df['monto'] - df['monto'].mean()) / monto_std if monto_std > 0 else 0
    df['date'] = df['fecha'].dt.date
    df['transactions_per_day'] = df.groupby('date')['date'].transform('count')
    df['transactions_per_week'] = df.groupby('week_year')['week_year'].transform('count')

    # Calcular la frecuencia de cada categoría
    df['category_frequency'] = df.groupby('category_id')['category_id'].transform('count')

    # Identificar gastos hormiga
    # Umbral para considerar un gasto como hormiga basado en el monto
    ANT_EXPENSE_AMOUNT_THRESHOLD = 100
    # Umbral para la frecuencia mínima de categoría para considerar repetición significativa
    CATEGORY_REPETITION_THRESHOLD = 3

    # Identificar gastos hormiga basados en el monto y la repetición de la categoría
    df['is_ant_expense'] = ((df['monto'] < ANT_EXPENSE_AMOUNT_THRESHOLD) &
                            (df['category_frequency'] >= CATEGORY_REPETITION_THRESHOLD))
    print(df)
    return df
