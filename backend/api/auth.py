from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.database import get_db
from backend.core.security import create_access_token
from backend.crud.user import get_user_by_email, create_user
from backend.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from backend.models.courier import Courier

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    courier_id = None

    if data.role_id == 1:
        result = await db.execute(select(Courier.courier_id).order_by(Courier.courier_id))
        existing_ids = set(result.scalars().all())
        new_id = 1
        while new_id in existing_ids:
            new_id += 1
        courier_id = new_id

        db.add(Courier(
            courier_id=courier_id,
            courier_type_id=1,
            working_hours=["09:00-18:00"],
        ))
        await db.flush()

    user = await create_user(db, data.email, data.password, data.role_id, courier_id)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user or user.hashed_password != data.password:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token({"sub": user.email, "role": user.role_id, "courier_id": user.courier_id})
    return {"access_token": token, "token_type": "bearer"}