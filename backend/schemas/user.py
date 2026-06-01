from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: str
    password: str
    role: str = "courier"


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"