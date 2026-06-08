from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.order import Order, OrderStatus
from backend.models.courier import Courier
from backend.schemas.order import OrderCreate

COURIER_TYPE_MAX_WEIGHT = {
    1: 10.0,  # foot
    2: 15.0,  # bike
    3: 50.0,  # car
}


async def get_order(db: AsyncSession, order_id: int) -> Order | None:
    result = await db.execute(select(Order).filter(Order.order_id == order_id))
    return result.scalar_one_or_none()


async def get_all_orders(db: AsyncSession) -> list[Order]:
    result = await db.execute(select(Order))
    return list(result.scalars().all())


async def get_courier_orders(db: AsyncSession, courier_id: int) -> list[Order]:
    result = await db.execute(select(Order).filter(Order.courier_id == courier_id))
    return list(result.scalars().all())


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

    # Идемпотентность — уже назначен на того же курьера
    if order.status == OrderStatus.assigned and order.courier_id == courier_id:
        return order

    if order.status != OrderStatus.pending:
        raise ValueError(f"Заказ уже имеет статус '{OrderStatus(order.status).value}'")

    courier_result = await db.execute(select(Courier).filter(Courier.courier_id == courier_id))
    courier = courier_result.scalar_one_or_none()
    if not courier:
        raise ValueError("Курьер не найден")

    max_weight = COURIER_TYPE_MAX_WEIGHT.get(courier.courier_type_id, 0)
    if float(order.weight) > max_weight:
        raise ValueError(
            f"Заказ весит {order.weight} кг, курьер может везти максимум {max_weight} кг"
        )

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

    if order.status != OrderStatus.assigned:
        raise ValueError(f"Нельзя завершить заказ со статусом '{OrderStatus(order.status).value}'")

    order.status = OrderStatus.completed
    order.complete_time = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(order)
    return order