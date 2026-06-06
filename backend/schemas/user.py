from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str
    password: str
    role_id: int = 1  # 1 = courier, 2 = dispatcher


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role_id: int
    courier_id: int | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"