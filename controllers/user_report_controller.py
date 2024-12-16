
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from models.user_model import TokenData
from models.user_model import SendReports
from database.conectiondb import users
from controllers.user_controller import get_current_user
from utilities.reporte import generate_and_send_reports
from bson import ObjectId
router = APIRouter()

# Hacer el cambio en el usuario
def add_reports (userID):
    user = users.find_one({"_id": userID})
    # print(user)
    if 'send_reports' not in user:
        # print("agregando el campo de reportes")
        users.update_one({"_id": userID}, {"$set": {"send_reports": True}})


# Función para habilitar/dehabilitar el envío de reportes
@router.post("/finance/reportes/enable")
async def enable_reports(send_reports: SendReports, current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        
        # Válidar que el usuario tenga el campo de send_Reports
        user_id = ObjectId(current_user.user_id)
        add_reports(user_id)

        users.update_one({"_id": user_id}, {"$set": {"send_reports": send_reports.send_reports}})
        if send_reports.send_reports:
            return {"message": "Envío de reportes mensuales, activado"}
        else:
            return {"message": "Envío de reportes mensuales, desactivado"}
    
    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/finance/send_monthly_reports")
async def send_monthly_reports(background_tasks: BackgroundTasks, current_user: TokenData = Depends(get_current_user)):
    try:
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        # Válidar que el usuario tenga el campo de send_Reports
        user_id = ObjectId(current_user.user_id)
        add_reports(user_id)
        user = users.find_one({"_id": user_id})
        reports_send = user["send_reports"]

        if reports_send:
            background_tasks.add_task(generate_and_send_reports)
            # print("Se mandó el correo")

        return {"message": "Reportes enviados en segundo plano a todos los usuarios"}

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

