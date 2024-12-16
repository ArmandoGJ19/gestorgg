from pydantic import BaseModel, Field


class SalaryInput(BaseModel):
    gross_salary: float
    include_imss: bool = Field(default=False)
    include_subsidy: bool = Field(default=False)
    period: str