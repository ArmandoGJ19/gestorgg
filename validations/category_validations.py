import re

def validate_category(new_category):

    # Validación para apellidos: no deben contener números
    if re.search(r'\d', new_category["category_name"]):
        raise ValueError('La categoría no debe contener números')

    if not re.match(r'\w{3,}', new_category["category_name"]):
        raise ValueError('La categoría debe tener al menos 5 caracteres')

    # Validación para el tipo de categoría: solo puede ser "ingreso" o "gasto"
    allowed_types = ["ingreso", "gasto"]
    if new_category["type"] not in allowed_types:
        raise ValueError('El tipo de categoría debe ser "ingreso" o "gasto"')

def validate_update_category(new_category):

    # Validación para apellidos: no deben contener números
    if re.search(r'\d', new_category["category_name"]):
        raise ValueError('La categoría no debe contener números')

    if not re.match(r'\w{3,}', new_category["category_name"]):
        raise ValueError('La categoría debe tener al menos 5 caracteres')

    # Validación para el tipo de categoría: solo puede ser "ingreso" o "gasto"
    allowed_types = ["ingreso", "gasto"]
    if new_category["type"] not in allowed_types:
        raise ValueError('El tipo de categoría debe ser "ingreso" o "gasto"')