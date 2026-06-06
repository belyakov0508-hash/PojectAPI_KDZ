from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.order import Order, OrderStatus
from backend.schemas.order import OrderCreate


async def get_order(db: AsyncSession, order_id: int) -> Order | None:
    result = await db.execute(select(Order).filter(Order.order_id == order_id))
    return result.scalar_one_or_none()


async def get_all_orders(db: AsyncSession) -> list[Order]:
    result = await db.execute(select(Order))
    return result.scalars().all()


async def get_courier_orders(db: AsyncSession, courier_id: int) -> list[Order]:
    result = await db.execute(select(Order).filter(Order.courier_id == courier_id))
    return result.scalars().all()


async def create_order(db: AsyncSession, data: OrderCreate) -> Order:
    order = Order(
        order_id=data.order_id,
        weight=data.weight,
        region=data.region,
        delivery_hours=data.delivery_hours,
        status=OrderStatus.pending,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def assign_courier(db: AsyncSession, order_id: int, courier_id: int) -> Order | None:
    order = await get_order(db, order_id)
    if not order:
        return None

    order.courier_id = courier_id
    order.status = OrderStatus.assigned
    order.assign_time = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)
    return order


async def complete_order(db: AsyncSession, order_id: int) -> Order | None:
    order = await get_order(db, order_id)
    if not order:
        return None

    order.status = OrderStatus.completed
    order.complete_time = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)
    return order