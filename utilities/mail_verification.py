import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException, status
from pydantic import EmailStr
import random
from decouple import config

EMAIL = config("EMAIL")
PASSWORD_GMAIL = config("PASSWORD_GMAIL")

def send_verification_email(to_email: EmailStr, code: str):
    sender = EMAIL
    password = PASSWORD_GMAIL
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)

        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = to_email
        message['Subject'] = "Codigo de verificación"
        message.attach(MIMEText(f"Tu código de verificación es {code}.", 'plain'))

        server.sendmail(sender, to_email, message.as_string())
        server.quit()
        print(f"Correo enviado a {to_email}")
    except smtplib.SMTPException as e:
        print(f"Error al enviar correo: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email")


def generate_verification_code():
    return str(random.randint(100000, 999999))
