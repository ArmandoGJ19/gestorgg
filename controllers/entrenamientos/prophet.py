from fastapi import APIRouter, HTTPException, status
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, ParameterGrid

router = APIRouter()


def load_data(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def preprocess_data(datos: pd.DataFrame) -> pd.DataFrame:
    gastos = datos[datos['type'] == 'gasto']
    gastos_diarios = gastos.groupby('fecha')['monto'].sum().reset_index()
    gastos_diarios.columns = ['ds', 'y']
    gastos_diarios['ds'] = pd.to_datetime(gastos_diarios['ds'])
    return gastos_diarios


def split_data(data: pd.DataFrame, train_ratio: float = 0.8):
    train_size = int(len(data) * train_ratio)
    train_data = data[:train_size]
    test_data = data[train_size:]
    return train_data, test_data


def cross_validate_model(data, param_grid, n_splits=5):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    best_mae = float('inf')
    best_params = None
    best_model = None

    for params in ParameterGrid(param_grid):
        maes = []
        for train_index, test_index in tscv.split(data):
            train_data = data.iloc[train_index]
            test_data = data.iloc[test_index]

            model = Prophet(
                yearly_seasonality=False,
                changepoint_prior_scale=params['changepoint_prior_scale'],
                seasonality_prior_scale=params['seasonality_prior_scale'],
                holidays_prior_scale=params['holidays_prior_scale']
            )
            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)

            model.fit(train_data)
            future = model.make_future_dataframe(periods=len(test_data))
            forecast = model.predict(future)
            test_forecast = forecast.iloc[-len(test_data):]

            mae = mean_absolute_error(test_data['y'], test_forecast['yhat'])
            maes.append(mae)

        avg_mae = np.mean(maes)

        if avg_mae < best_mae:
            best_mae = avg_mae
            best_params = params
            best_model = model

    return best_model, best_params, best_mae


def save_model(model, file_path: str):
    joblib.dump(model, file_path)


def load_model(file_path: str):
    return joblib.load(file_path)


def plot_forecast(test_data: pd.DataFrame, forecast: pd.DataFrame, file_path: str):
    # Asegúrate de que las predicciones y los datos de prueba estén alineados correctamente
    test_data_aligned = test_data[test_data['ds'].isin(forecast['ds'])]
    forecast_aligned = forecast[forecast['ds'].isin(test_data['ds'])]

    plt.figure(figsize=(10, 6))
    plt.plot(test_data_aligned['ds'], test_data_aligned['y'], label='Datos Reales')
    plt.plot(forecast_aligned['ds'], forecast_aligned['yhat'], label='Predicciones')
    plt.fill_between(forecast_aligned['ds'], forecast_aligned['yhat_lower'], forecast_aligned['yhat_upper'], color='blue', alpha=0.2)
    plt.title('Predicciones de Gastos en Datos de Prueba (Modelo Mejorado)')
    plt.xlabel('Fecha')
    plt.ylabel('Gastos')
    plt.legend()
    plt.savefig(file_path)
    plt.show()


@router.get("/finance/training/prophet_model")
async def get_prophet_model():
    try:
        data_path = './utilities/data_sinteticos_usuario_v1.csv'
        datos = load_data(data_path)
        gastos_diarios = preprocess_data(datos)
        train_data, test_data = split_data(gastos_diarios)

        param_grid = {
            'changepoint_prior_scale': [0.001, 0.01, 0.1, 0.5, 1.0],
            'seasonality_prior_scale': [1.0, 10.0, 20.0, 30.0, 40.0, 50.0],
            'holidays_prior_scale': [0.01, 0.1, 1.0, 10.0],
        }

        best_model, best_params, best_mae = cross_validate_model(gastos_diarios, param_grid)
        save_model(best_model, 'modelo_prophet_v2.pkl')

        best_model = load_model('modelo_prophet_v2.pkl')
        future = best_model.make_future_dataframe(periods=len(test_data))
        forecast = best_model.predict(future)
        test_forecast = forecast.iloc[-len(test_data):]
        rmse = np.sqrt(mean_squared_error(test_data['y'], test_forecast['yhat']))

        plot_forecast(test_data, test_forecast, "./img/prophet/predicciones_test_prophet_v7.png")

        return {
            "best_params": best_params,
            "best_mae": best_mae,
            "best_rmse": rmse,
            "message": "Modelo Prophet guardado correctamente"
        }
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
