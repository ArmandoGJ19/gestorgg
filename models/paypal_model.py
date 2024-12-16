from pydantic import BaseModel, Field

class PaypalInput(BaseModel):
    # user_id: str
    # payment_date: datetime = Field(default=None)
    amount: float = Field(...)
    currency: str = Field(...)
    payment_method: str = Field(...)
    subscription_plan: str = Field(...)

    # user_id: str = Field(...)
    # plan_id: str = Field(...)

class PaypalPlan(BaseModel):
    amount: float = Field(...)
    currency: str = Field(...)
    payment_method: str = Field(...)
    subscription_plan: str = Field(...)
    plan_id: str = Field(...)
    subscription_id: str = Field(...)