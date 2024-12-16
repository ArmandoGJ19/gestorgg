
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from controllers.user_controller import router as router_user
from controllers.category_controller import router as router_category
from controllers.transaction_controller import router as router_transaction
from controllers.consejos_controller import router as router_consejos
from controllers.budget_controller import router as router_budget
from controllers.CalculatorController import router as router_calculator
# from controllers.hormiga_controller import router as router_hormiga
from controllers.user_report_controller import router as router_user_report
from controllers.user_photo_controller import router as router_user_photo
from controllers.training import router as router_training
from utilities.reporte import generate_and_send_reports
from controllers.entrenamientos.prophet import router as router_entrenamiento_prophet
from controllers.entrenamientos.predictions import router as router_predictions
from controllers.paypal_controller import router as router_paypal
import logging
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Origen específico sin espacio adicional
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"]   # Permite todos los headers
)


app.include_router(router_user)
app.include_router(router_category)
app.include_router(router_transaction)
app.include_router(router_consejos)
app.include_router(router_budget)
app.include_router(router_calculator)
# app.include_router(router_hormiga)
app.include_router(router_user_report)
app.include_router(router_user_photo)
app.include_router(router_training)
app.include_router(router_paypal)
app.include_router(router_entrenamiento_prophet)
app.include_router(router_predictions)


# Configuración de APScheduler
scheduler = BackgroundScheduler()

# Programar la tarea para el primer día de cada mes a las 00:00
@scheduler.scheduled_job('cron', year=2024, month=8, day=14, hour=22, minute=50)
# @scheduler.scheduled_job('cron', day=1, hour=0, minute=0)
def scheduled_task():
    logging.info("Iniciando tarea programada para enviar reportes mensuales")
    generate_and_send_reports()


# Iniciar el programador
scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


logging.basicConfig(level=logging.INFO)