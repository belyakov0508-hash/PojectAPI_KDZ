from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class OrderStatusEnum(str, Enum):
    pending = "pending"
    assigned = "assigned"
    completed = "completed"


class OrderCreate(BaseModel):
    order_id: int
    weight: float
    region: int
    delivery_hours: list[str]


class OrderResponse(BaseModel):
    order_id: int
    weight: float
    region: int
    delivery_hours: list[str]
    status: OrderStatusEnum
    courier_id: int | None
    assign_time: datetime | None
    complete_time: datetime | None

    model_config = {"from_attributes": True}