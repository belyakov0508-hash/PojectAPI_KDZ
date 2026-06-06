from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.security import create_access_token
from backend.crud.user import get_user_by_email, create_user
from backend.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    user = await create_user(db, data.email, data.password, data.role_id)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user or user.hashed_password != data.password:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token({"sub": user.email, "role": user.role_id, "courier_id": user.courier_id})
    return {"access_token": token, "token_type": "bearer"}