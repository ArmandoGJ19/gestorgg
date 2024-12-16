from bson import ObjectId
from database.conectiondb import users, category
from fastapi import HTTPException


# Función para convertir el ObjectId de MongoDB a cadena
def convert_object_id_to_string(item, field_name="item_id"):
    item[field_name] = str(item["_id"])
    del item["_id"]


# Función para obtener un elemento por su ID
def get_item_by_id(collection, item_id):
    item = collection.find_one({"_id": ObjectId(item_id)})
    return item


def get_user_id(username: str):
    user = users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return str(user["_id"])


def convert_objectid_to_str(item):
    if isinstance(item, ObjectId):
        return str(item)
    if isinstance(item, dict):
        for k, v in item.items():
            item[k] = convert_objectid_to_str(v)
    if isinstance(item, list):
        item = [convert_objectid_to_str(v) for v in item]
    return item


def get_category_id_user(user_id):
    categories = category.find({"user_id": user_id})  # Asume que un usuario puede tener múltiples categorías
    if categories is None:
        raise HTTPException(status_code=404, detail="Categories not found")

    category_ids = [str(cat["_id"]) for cat in categories]  # Convertir ObjectId a string
    return category_ids

