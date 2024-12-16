from typing import Optional
from pydantic import BaseModel, Field
from datetime import date


class TransactionSchema(BaseModel):
    user_id: Optional[str] = Field(default=None)
    type: str = Field(...)  # "Ingreso" o "Gasto"
    category_id: str = Field(...)
    monto: float = Field(...)
    fecha: date = Field(...)
    descripcion: str = Field(...)
    # include_imss: Optional[bool] = Field(default=False)
    # salary_period: Optional[str] = Field(default=None)


class GraficTransaction(BaseModel):
    monto: float = Field(...)
    category_name: str = Field(...)
