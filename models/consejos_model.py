from pydantic import BaseModel


class Pregunta(BaseModel):
    pregunta: str