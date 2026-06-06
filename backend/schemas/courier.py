from pydantic import BaseModel


class CourierCreate(BaseModel):
    courier_id: int
    courier_type_id: int  # 1 = foot, 2 = bike, 3 = car
    working_hours: list[str]
    regions: list[int]


class CourierResponse(BaseModel):
    courier_id: int
    courier_type_id: int
    working_hours: list[str]

    model_config = {"from_attributes": True}