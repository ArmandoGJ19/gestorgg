from typing import Literal
from typing import Optional
from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    category_name: str = Field(...)
    type: Literal["ingreso", "gasto"] = Field(..., description="Input should be 'ingreso' or 'gasto'")


class CategoryEdit(BaseModel):
    category_name: str = Field(...)
    type: Literal["ingreso", "gasto"] = Field(..., description="Input should be 'ingreso' or 'gasto'")


class CategoryDelete(BaseModel):
    category_id: str = Field(...)


class CategoryResponse(BaseModel):
    category_name: str
    user_id: Optional[str] = Field(default=None)
    _id: str