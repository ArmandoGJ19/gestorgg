from pymongo import MongoClient

financeManager = MongoClient(
    "mongodb://localhost:27017/",
)

db = financeManager["finance"]
users = db["users"]
blacklisted_tokens = db["blacklisted_tokens"]
category = db["category"]
transactions = db["transactions"]
mensajes = db["mensajes"]
budgets = db["budgets"]
predictions = db["predictions"]
payments = db["payments"]
predictions_prophet = db["predictions_prophet"]