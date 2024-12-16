# import numpy as np
# from keras.models import Sequential
# from keras.layers import Dense, LSTM
# from sklearn.model_selection import train_test_split
# from models.data_preparation import extract_transactions, prepare_data
# from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
# from keras.regularizers import l1_l2
#
# # otro modelo
# from sklearn.linear_model import LogisticRegression
# from sklearn.metrics import accuracy_score, confusion_matrix
# from sklearn.model_selection import cross_val_score
# from joblib import dump
#
# def create_sequences(df, n_steps):
#     X, y = [], []
#     for i in range(len(df) - n_steps):
#         X.append(df[['amount_normalized', 'transactions_per_day', 'transactions_per_week', 'category_frequency']].iloc[
#                  i:(i + n_steps)].values)
#         y.append(df['is_ant_expense'].iloc[i + n_steps])
#     print("longitud de X: ", len(X),"longitud de y: ", len(y))
#     return np.array(X), np.array(y)
#
#
# # funcion de regresion logistica
# def train_model_logistic(user_id: str):
#     transactions_list = extract_transactions(user_id)
#     df = prepare_data(transactions_list)
#
#     if df.empty:
#         return "No data available for training"
#
#     # Selecciona tus características y la etiqueta
#     X = df[['amount_normalized', 'transactions_per_day', 'transactions_per_week', 'category_frequency']]
#     y = df['is_ant_expense']
#
#     # Convierte las etiquetas a tipo numérico si aún no lo están
#     y = y.astype('int')
#
#     # División del dataset
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#     # Crear y entrenar el modelo de Regresión Logística
#     model = LogisticRegression()
#
#     scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
#     print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))
#     model.fit(X_train, y_train)
#     dump(model, 'modelo_regresion_logistica.joblib')
#     # Evaluar el modelo
#     y_pred = model.predict(X_test)
#     accuracy = accuracy_score(y_test, y_pred)
#     print('Test accuracy:', accuracy)
#
#     return accuracy