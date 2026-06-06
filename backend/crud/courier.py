from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.courier import Courier, CourierRegion
from backend.schemas.courier import CourierCreate
from backend.crud.user import create_user


async def get_courier(db: AsyncSession, courier_id: int) -> Courier | None:
    result = await db.execute(select(Courier).filter(Courier.courier_id == courier_id))
    return result.scalar_one_or_none()


async def get_all_couriers(db: AsyncSession) -> list[Courier]:
    result = await db.execute(select(Courier))
    return result.scalars().all()


async def create_courier(db: AsyncSession, data: CourierCreate) -> Courier:
    courier = Courier(
        courier_id=data.courier_id,
        courier_type_id=data.courier_type_id,
        working_hours=data.working_hours,
    )
    db.add(courier)

    for region in data.regions:
        db.add(CourierRegion(courier_id=data.courier_id, region=region))

    # Создаём пользователя для курьера автоматически
    await create_user(db, data.email, data.password, role_id=1, courier_id=data.courier_id)

    await db.commit()
    await db.refresh(courier)
    return courier


async def update_courier(db: AsyncSession, courier_id: int, update_data: dict) -> Courier | None:
    courier = await get_courier(db, courier_id)
    if not courier:
        return None

    for key, value in update_data.items():
        if hasattr(courier, key):
            setattr(courier, key, value)

    await db.commit()
    await db.refresh(courier)
    return courier