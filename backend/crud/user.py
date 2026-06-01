from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, role: str = "courier") -> User:
    user = User(
        email=email,
        hashed_password=password,  # храним как есть
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user