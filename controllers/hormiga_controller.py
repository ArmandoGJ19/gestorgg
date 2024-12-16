# from fastapi import APIRouter, HTTPException, Depends, status
# from models.neural_network import train_model_logistic
# from models.user_model import TokenData
# from controllers.user_controller import get_current_user
# from models.data_preparation import extract_transactions, prepare_data
# from joblib import load
# router = APIRouter()
#
#
# @router.post("/train")
# async def train_neural_network(current_user:  TokenData = Depends(get_current_user)):
#     try:
#         if not current_user:
#             raise HTTPException(status_code=401, detail="Unauthorized")
#         loss = train_model_logistic(current_user.user_id)
#         # print(current_user.user_id)
#         return {"loss": loss}
#     except HTTPException as http_error:
#         raise http_error
#
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#
# @router.get("/predict")
# async def predict_expenses(current_user: TokenData = Depends(get_current_user)):
#     try:
#         if not current_user:
#             raise HTTPException(status_code=401, detail="Unauthorized")
#
#         transactions_list = extract_transactions(current_user.user_id)
#         df = prepare_data(transactions_list)
#
#         X = df[['amount_normalized', 'transactions_per_day', 'transactions_per_week', 'category_frequency']]
#
#         # Carga el modelo de regresión logística
#         model = load('modelo_regresion_logistica.joblib')
#
#         # Haz predicciones
#         predictions = model.predict(X)
#         predictions_proba = model.predict_proba(X)[:, 1]  # Obtener probabilidades
#
#         expenses_pred = [
#             {
#                 "amount": float(df.iloc[i]['monto']),
#                 "is_ant_expense": bool(predictions[i]),
#                 "probability_ant_expense": float(predictions_proba[i]),
#                 "date": str(df.iloc[i]['date']),
#                 "category_id": df.iloc[i]['category_id']
#             } for i in range(len(predictions))
#         ]
#
#         return {"user_id": current_user.user_id, "predictions": expenses_pred}
#
#     except HTTPException as http_error:
#         raise http_error
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
# # @router.get("/finance/categories_by_user")
# # async def get_categories_by_user(current_user: TokenData = Depends(get_current_user)):
# #     try:
# #         if not current_user:
# #             raise HTTPException(status_code=401, detail="Unauthorized")
# #
# #         category_ids = get_category_id_user(current_user.user_id)
# #         return {"category_ids": category_ids}  # Devuelve los IDs en el formato deseado
# #     except HTTPException as http_error:
# #         raise http_error
# #     except Exception as e:
# #         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#
#
