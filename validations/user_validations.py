import re
from validate_email import validate_email
from database.conectiondb import users


def validate_user(user):
    if len(user["password"]) < 8:
        raise ValueError('Contraseña muy corta')

    if not re.search(r'[A-Z]', user["password"]):
        raise ValueError('Falta mayúscula en contraseña')

    # Verifica que la contraseña no sea totalmente numérica
    if user['password'].isdigit():
        raise ValueError('La contraseña no puede ser totalmente numérica')

    if not re.match(r'[^@]+@[^@]+\.[^@]+', user["email"]):
        raise ValueError('Email inválido')

    if not validate_email(user["email"]):
        raise ValueError('Dominio de email no existe')


def validate_update_user(update_user):

    if len(update_user["password"]) < 8:
        raise ValueError('La Contraseña debe tener mínimo 8 caracteres')

    if not re.search(r'[A-Z]', update_user["password"]):
        raise ValueError('Falta mayúscula en contraseña')

    # Verifica que la contraseña no sea totalmente numérica
    if update_user['password'].isdigit():
        raise ValueError('La contraseña no puede ser totalmente numérica')

    if re.search(r'\d', update_user["name"]):
        raise ValueError('El nombre no debe contener números')

    if not re.match(r'\w{3,}', update_user["name"]):
        raise ValueError('El nombre debe tener al menos 3 caracteres')

    # Validación para apellidos: no deben contener números
    if re.search(r'\d', update_user["lastname"]):
        raise ValueError('Los apellidos no deben contener números')

    if not re.match(r'\w{3,}', update_user["lastname"]):
        raise ValueError('Los apellidos deben ser al menos 5 caracteres')
