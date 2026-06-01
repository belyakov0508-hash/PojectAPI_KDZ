from pydantic import BaseModel
from enum import Enum


class CourierTypeEnum(str, Enum):
    foot = "foot"
    bike = "bike"
    car = "car"


class CourierCreate(BaseModel):
    courier_id: int
    courier_type: CourierTypeEnum
    working_hours: list[str]
    regions: list[int]


class CourierResponse(BaseModel):
    courier_id: int
    courier_type: CourierTypeEnum
    working_hours: list[str]

    model_config = {"from_attributes": True}