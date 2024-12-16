from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class BudgetCreate(BaseModel):
    user_id: Optional[str] = Field(default=None)
    amount: float = Field(...)
    category_id: str = Field(...)
    date_start: date = Field(...)
    date_end: date = Field(...)
    budget_name: str = Field(...)

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }
