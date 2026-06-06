from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, role_id: int = 1) -> User:
    user = User(
        email=email,
        hashed_password=password,
        role_id=role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user