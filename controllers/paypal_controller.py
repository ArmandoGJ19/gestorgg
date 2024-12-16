from datetime import datetime, timedelta
from typing import Dict, Any
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends
from decouple import config
from models.paypal_model import PaypalInput, PaypalPlan
from controllers.user_controller import get_current_user
from models.user_model import TokenData
from fastapi import HTTPException, status
from database.conectiondb import users, payments
import base64
import requests
import cloudinary

cloudinary.config(
    cloud_name=config('PAYPAL_CLIENT_ID'),
    api_key=config('PAYPAL_CLIENT_SECRET'),
)
BASE_URL = 'https://api-m.sandbox.paypal.com'
router = APIRouter()

# Crear una orden de pago
# @router.post("/finance/paypal")
def createOrder(access_token: str, pay, plan_id) -> Dict[str, Any]:
    url = f'{BASE_URL}/v2/checkout/orders'
    payload = {
        'intent': 'CAPTURE',
        'purchase_units': [
            {
                'amount': {
                    'currency_code': pay.currency,
                    'value': pay.amount
                }
            }
        ]
    }
    headers = {
        'Content-Type': 'application/json',
        'PayPal-Request-Id': plan_id,
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.post(url, headers=headers, json=payload)

    # print(response_json.get('id'))
    return {'message': response.json()}


# Generar un token de acceso en paypal
def generateAccessToken():
    try:
        if not config('PAYPAL_CLIENT_ID') or not config('PAYPAL_CLIENT_SECRET'):
            raise Exception('Paypal credentials not found')

        auth = config('PAYPAL_CLIENT_ID') + ':' + config('PAYPAL_CLIENT_SECRET')
        auth = base64.b64encode(auth.encode()).decode('utf-8')

        response = requests.post(
            f'{BASE_URL}/v1/oauth2/token',
            data={'grant_type': 'client_credentials'},
            headers={'Authorization': f'Basic {auth}'}
        )
        data = response.json()
        return data['access_token']

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Crear un nuevo producto en PayPal
def create_product(access_token: str):
    url = f'{BASE_URL}/v1/catalogs/products'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    data = {
        "name": "Suscripcion G|G",
        "description": "Suscripcion mensual a sistema G|G",
        "type": "SERVICE",
        "category": "SOFTWARE",
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Buscar un producto en PayPal
def search_product(access_token: str):
    url = f'{BASE_URL}/v1/catalogs/products'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    response = requests.get(url, headers=headers)
    return response.json()


# Crear un nuevo plan en PayPal
def create_plan(access_token: str, pay, product_id: str):
    url = f'{BASE_URL}/v1/billing/plans'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Prefer': 'return=representation'
    }
    data = {
        "product_id": product_id,
        "name": "Suscripcion G|G",
        "description": "Suscripcion mensual a sistema G|G",
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": pay.amount,
                        "currency_code": pay.currency
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee": {
                "value": pay.amount,
                "currency_code": pay.currency
            },
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        },
        "taxes": {
            "percentage": "10",
            "inclusive": False
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Buscar un plan en PayPal
def search_plan(access_token: str):
    url = f'{BASE_URL}/v1/billing/plans'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Prefer': 'return=representation'
    }
    response = requests.get(url, headers=headers)
    return response.json()


# Crear una nueva suscripción en PayPal
def create_suscription(access_token: str, pay, start_time_iso, plan_id: str) -> dict[str, Any]:
    try:
        url = f'{BASE_URL}/v1/billing/subscriptions'
        headers = {
            'Content-Type': 'application/json',
            'PayPal-Request-Id': 'SUBSCRIPTION-21092019-001',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Prefer': 'return=representation',
        }
        data = {
            "plan_id": plan_id,
            "start_time": start_time_iso,
            "quantity": "1",
            "shipping_amount": {
                "currency_code": pay.currency,
                "value": pay.amount
            },
            "application_context": {
                "brand_name": "Suscripcion G|G",
                "locale": "en-US",
                "shipping_preference": "SET_PROVIDED_ADDRESS",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                },
                "return_url": "http://localhost:3000/gg/dashboard/transaccion",
                "cancel_url": "http://localhost:3000/gg/dashboard/transaccion"
            }
        }
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Activar una suscripción en PayPal
def search_suscription_local(subscription_id: str):
    try:
        access_token = generateAccessToken()
        url = f'{BASE_URL}/v1/billing/subscriptions/{subscription_id}'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        response = requests.get(url, headers=headers)
        return response.json()
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Guardar en la base de datos la información de pagos
def save_plan(existing_user, pay, subscription_id):
    # Datos
    data_user = {
        "user_id": existing_user['_id'],
        "payment_date": pay["create_time"],
        "amount": pay["shipping_amount"]["value"],
        "currency": pay["shipping_amount"]["currency_code"],
        "payment_method": "PAYPAL",
        "subscription_plan": "MONTH",
        "plan_id": pay["plan_id"],
        "subscription_id": subscription_id
    }
    # se guarda en la colección de payments
    payments.insert_one(data_user)

    print("pay", pay)

    update_data = {
        "$set": {
            "subscription_status": True,
            "start_date": pay["start_time"],
            "end_date": pay["billing_info"]["next_billing_time"],
            "last_payment_date": pay["billing_info"]["last_payment"]["time"],
            "subscription_id": subscription_id
        }
    }
    users.update_one(
        {"_id": existing_user['_id']},
        update_data
    )


# Crear planes de pago
@router.post("/finance/paypal")
def create_subscription(pay: PaypalInput, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            existing_user = users.find_one({"username": current_user.username})

            # Validar que el usuario no pague 2 veces
            if not existing_user.get('subscription_status', False):
                access_token = generateAccessToken()
                current_time = datetime.utcnow()
                start_time_iso = (current_time + timedelta(minutes=30)).isoformat() + 'Z'

                # Crear un nuevo producto
                # new_product_response = create_product(access_token)
                # if 'id' not in new_product_response:
                #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el producto")
                # product_id = new_product_response['id']

                # Buscar un producto
                product_response = search_product(access_token)
                product_id = product_response['products'][0]['id']

                # Buscar un plan
                new_plan_response = create_plan(access_token, pay, product_id)
                if 'id' not in new_plan_response:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                        detail="Error al crear el plan")
                plan_id = new_plan_response['id']

                # Crear la suscripción
                subscription_response = create_suscription(access_token, pay, start_time_iso, plan_id)
                subscription_id = subscription_response['id']
                print(subscription_id)
                plan_id = subscription_response['plan_id']

                create_order = createOrder(access_token, pay, plan_id)
                order_id = create_order['message']['id']

                return {
                    'message': 'Subscription in process',
                    'order_id': order_id,
                    'plan_id': plan_id,
                    'subscription_id': subscription_id
                }
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="User already has an active subscription")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Capturar una orden de pago
@router.post("/finance/check/paypal/{order_id}")
def capture_order(order_id: str, pay: PaypalPlan, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            if not order_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            access_token = generateAccessToken()
            url = f'{BASE_URL}/v2/checkout/orders/{order_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            response = requests.get(url, headers=headers)
            response_json = response.json()

            # Datos a mandar
            existing_user = users.find_one({"username": current_user.username})
            if existing_user.get('subscription_status', False):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="User already has an active subscription")

            if response_json.get('status') == 'COMPLETED' or response_json.get('status') == 'APPROVED':
                subs = search_suscription_local(pay.subscription_id)
                return {"message": subs}
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not captured")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Status de suscripcion
@router.get("/finance/search_suscription/{subscription_id}")
def search_suscription_local(subscription_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            access_token = generateAccessToken()
            url = f'{BASE_URL}/v1/billing/subscriptions/{subscription_id}'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            response = requests.get(url, headers=headers)
            return {"message": response.json()}

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Guardar suscripcion
@router.get("/finance/save_suscription/{subscription_id}")
def save_suscription(subscription_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            existing_user = users.find_one({"username": current_user.username})
            if not existing_user.get('subscription_status'):
                access_token = generateAccessToken()
                url = f'{BASE_URL}/v1/billing/subscriptions/{subscription_id}'
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                }

                response = requests.get(url, headers=headers)
                pay = response.json()
                if pay.get('status') == 'ACTIVE':
                    save_plan(existing_user, pay, subscription_id)
                    return {"message": "Paypal plan saved"}
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not captured")

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="User already has an active subscription")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Cancelar la suscripcion
@router.get("/finance/cancel_suscription/{subscription_id}")
def cancel_suscription(subscription_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        if current_user:
            access_token = generateAccessToken()
            url = f'{BASE_URL}/v1/billing/subscriptions/{subscription_id}/cancel'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            data = {"reason": "Not satisfied with the service"}

            response = requests.post(url, headers=headers, json=data)
            if response.status_code in (200, 204):
                # Actualizar en la base de datos
                users.update_one({"username": current_user.username}, {"$set": {"subscription_status": False}})
                # Borrar de la base de datos
                payments.delete_one({"subscription_id": subscription_id})

                return {"message": "Subscription canceled"}
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.json())

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))