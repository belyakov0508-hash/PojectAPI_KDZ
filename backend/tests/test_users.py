"""Тесты для моделей User и Role."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from backend.models.role import Role
from backend.models.user import User


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------

async def test_create_role(db: AsyncSession):
    role = Role(name="courier")
    db.add(role)
    await db.commit()
    await db.refresh(role)

    assert role.id is not None
    assert role.name == "courier"


async def test_role_name_unique(db: AsyncSession):
    db.add(Role(name="courier"))
    await db.commit()

    db.add(Role(name="courier"))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_multiple_roles(db: AsyncSession):
    db.add(Role(name="courier"))
    db.add(Role(name="dispatcher"))
    await db.commit()

    result = await db.execute(select(Role))
    roles = result.scalars().all()
    assert len(roles) == 2
    assert {r.name for r in roles} == {"courier", "dispatcher"}


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

async def test_create_user(db_with_data: AsyncSession):
    db = db_with_data
    user = User(email="test@example.com", hashed_password="pass123", role_id=1)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role_id == 1
    assert user.courier_id is None


async def test_user_email_unique(db_with_data: AsyncSession):
    db = db_with_data
    db.add(User(email="same@example.com", hashed_password="a", role_id=1))
    await db.commit()

    db.add(User(email="same@example.com", hashed_password="b", role_id=1))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_user_with_courier_id(db_with_data: AsyncSession):
    db = db_with_data
    courier = Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"])
    db.add(courier)
    await db.commit()

    user = User(
        email="courier@example.com",
        hashed_password="pass",
        role_id=1,
        courier_id=1,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.courier_id == 1


async def test_user_role_fk_constraint(db_with_data: AsyncSession):
    """Нельзя создать пользователя с несуществующей ролью."""
    db = db_with_data
    db.add(User(email="bad@example.com", hashed_password="x", role_id=999))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_get_user_by_email(db_with_data: AsyncSession):
    db = db_with_data
    from backend.crud.user import get_user_by_email, create_user

    await create_user(db, email="find@example.com", password="secret", role_id=1)

    found = await get_user_by_email(db, "find@example.com")
    assert found is not None
    assert found.email == "find@example.com"


async def test_get_user_by_email_not_found(db_with_data: AsyncSession):
    from backend.crud.user import get_user_by_email

    result = await get_user_by_email(db_with_data, "nobody@example.com")
    assert result is None


from backend.models.courier import Courier  # noqa: E402 (needed after usage above)
