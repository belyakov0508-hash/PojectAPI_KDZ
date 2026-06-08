from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.models.courier import Courier, CourierRegion
from backend.models.order import Order, OrderStatus
from backend.schemas.courier import CourierCreate
from backend.crud.user import add_user

COURIER_TYPE_COEFFICIENT = {
    1: 2,  # foot
    2: 5,  # bike
    3: 9,  # car
}


async def get_courier(db: AsyncSession, courier_id: int) -> Courier | None:
    result = await db.execute(select(Courier).filter(Courier.courier_id == courier_id))
    return result.scalar_one_or_none()


async def get_all_couriers(db: AsyncSession) -> list[Courier]:
    result = await db.execute(select(Courier))
    return list(result.scalars().all())


async def create_courier(db: AsyncSession, data: CourierCreate) -> Courier:
    courier = Courier(
        courier_id=data.courier_id,
        courier_type_id=data.courier_type_id,
        working_hours=data.working_hours,
    )
    db.add(courier)

    for region in data.regions:
        db.add(CourierRegion(courier_id=data.courier_id, region=region))

    add_user(db, data.email, data.password, role_id=1, courier_id=data.courier_id)

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


async def get_courier_rating(db: AsyncSession, courier_id: int) -> float | None:
    result = await db.execute(
        select(Order)
        .filter(
            Order.courier_id == courier_id,
            Order.status == OrderStatus.completed,
            Order.complete_time.isnot(None),
        )
        .order_by(Order.complete_time)
    )
    completed_orders = result.scalars().all()

    if not completed_orders:
        return None

    region_times: dict[int, list[float]] = {}

    for i, order in enumerate(completed_orders):
        if i == 0:
            if order.assign_time is None:
                continue
            delivery_time = (order.complete_time - order.assign_time).total_seconds()
        else:
            prev = completed_orders[i - 1]
            if prev.complete_time is None:
                continue
            delivery_time = (order.complete_time - prev.complete_time).total_seconds()

        region = order.region
        if region not in region_times:
            region_times[region] = []
        region_times[region].append(delivery_time)

    if not region_times:
        return None

    td = [sum(times) / len(times) for times in region_times.values()]
    t = min(td)
    return round((3600 - min(t, 3600)) / 3600 * 5, 2)


async def get_courier_earnings(db: AsyncSession, courier_id: int) -> int | None:
    courier = await get_courier(db, courier_id)
    if not courier:
        return None

    coefficient = COURIER_TYPE_COEFFICIENT.get(courier.courier_type_id, 1)

    result = await db.execute(
        select(func.count(Order.order_id))
        .filter(
            Order.courier_id == courier_id,
            Order.status == OrderStatus.completed,
        )
    )
    completed_count = result.scalar() or 0

    return 500 * coefficient * completed_count