"""Тесты для модели Order и CRUD-функций заказов."""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from backend.models.courier import Courier
from backend.models.order import Order, OrderStatus
from backend.crud.order import (
    get_order,
    get_all_orders,
    get_courier_orders,
    create_order,
    assign_courier,
    complete_order,
)
from backend.schemas.order import OrderCreate


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_order_data(**kwargs) -> OrderCreate:
    defaults = dict(
        order_id=1,
        weight=5.0,
        region=1,
        delivery_hours=["09:00-18:00"],
    )
    defaults.update(kwargs)
    return OrderCreate(**defaults)


async def _add_courier(db: AsyncSession, courier_id: int = 1, type_id: int = 2) -> Courier:
    courier = Courier(courier_id=courier_id, courier_type_id=type_id, working_hours=["09:00-18:00"])
    db.add(courier)
    await db.commit()
    return courier


# ---------------------------------------------------------------------------
# Order model constraints
# ---------------------------------------------------------------------------

async def test_create_order_model(db_with_data: AsyncSession):
    db = db_with_data
    order = Order(
        order_id=1, weight=3.5, region=1,
        delivery_hours=["09:00-12:00"],
        status=OrderStatus.pending,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    assert order.order_id == 1
    assert order.status == OrderStatus.pending
    assert order.courier_id is None


async def test_order_id_positive_constraint(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Order(order_id=0, weight=1.0, region=1,
                 delivery_hours=["09:00-18:00"], status=OrderStatus.pending))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_order_region_positive_constraint(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Order(order_id=1, weight=1.0, region=0,
                 delivery_hours=["09:00-18:00"], status=OrderStatus.pending))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_order_weight_min_constraint(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Order(order_id=1, weight=0.0, region=1,
                 delivery_hours=["09:00-18:00"], status=OrderStatus.pending))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_order_weight_max_constraint(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Order(order_id=1, weight=50.01, region=1,
                 delivery_hours=["09:00-18:00"], status=OrderStatus.pending))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_order_weight_boundary_values(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Order(order_id=1, weight=0.01, region=1,
                 delivery_hours=["09:00-18:00"], status=OrderStatus.pending))
    db.add(Order(order_id=2, weight=50.00, region=1,
                 delivery_hours=["09:00-18:00"], status=OrderStatus.pending))
    await db.commit()  # не должно бросить исключение


# ---------------------------------------------------------------------------
# CRUD: get_order
# ---------------------------------------------------------------------------

async def test_get_order_existing(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Order(order_id=7, weight=2.0, region=3,
                 delivery_hours=["10:00-14:00"], status=OrderStatus.pending))
    await db.commit()

    found = await get_order(db, 7)
    assert found is not None
    assert found.order_id == 7


async def test_get_order_not_found(db_with_data: AsyncSession):
    result = await get_order(db_with_data, 9999)
    assert result is None


# ---------------------------------------------------------------------------
# CRUD: get_all_orders
# ---------------------------------------------------------------------------

async def test_get_all_orders_empty(db_with_data: AsyncSession):
    orders = await get_all_orders(db_with_data)
    assert orders == []


async def test_get_all_orders_multiple(db_with_data: AsyncSession):
    db = db_with_data
    for i in range(1, 4):
        db.add(Order(order_id=i, weight=1.0, region=1,
                     delivery_hours=["09:00-18:00"], status=OrderStatus.pending))
    await db.commit()

    orders = await get_all_orders(db)
    assert len(orders) == 3


# ---------------------------------------------------------------------------
# CRUD: create_order
# ---------------------------------------------------------------------------

async def test_create_order_crud(db_with_data: AsyncSession):
    order = await create_order(db_with_data, make_order_data())
    assert order.order_id == 1
    assert order.status == OrderStatus.pending
    assert order.courier_id is None
    assert order.assign_time is None
    assert order.complete_time is None


async def test_create_order_sets_pending_status(db_with_data: AsyncSession):
    order = await create_order(db_with_data, make_order_data(order_id=10, weight=3.0))
    assert order.status == OrderStatus.pending


# ---------------------------------------------------------------------------
# CRUD: get_courier_orders
# ---------------------------------------------------------------------------

async def test_get_courier_orders_empty(db_with_data: AsyncSession):
    db = db_with_data
    await _add_courier(db)
    orders = await get_courier_orders(db, 1)
    assert orders == []


async def test_get_courier_orders(db_with_data: AsyncSession):
    db = db_with_data
    await _add_courier(db, courier_id=1)
    await _add_courier(db, courier_id=2)

    db.add(Order(order_id=1, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
                 status=OrderStatus.assigned, courier_id=1))
    db.add(Order(order_id=2, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
                 status=OrderStatus.assigned, courier_id=1))
    db.add(Order(order_id=3, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
                 status=OrderStatus.assigned, courier_id=2))
    await db.commit()

    orders = await get_courier_orders(db, 1)
    assert len(orders) == 2
    assert all(o.courier_id == 1 for o in orders)


# ---------------------------------------------------------------------------
# CRUD: assign_courier
# ---------------------------------------------------------------------------

async def test_assign_courier_success(db_with_data: AsyncSession):
    db = db_with_data
    # Bike courier (type_id=2): max 15 kg
    await _add_courier(db, courier_id=1, type_id=2)
    await create_order(db, make_order_data(order_id=1, weight=10.0))

    order = await assign_courier(db, order_id=1, courier_id=1)
    assert order is not None
    assert order.status == OrderStatus.assigned
    assert order.courier_id == 1
    assert order.assign_time is not None


async def test_assign_courier_idempotent(db_with_data: AsyncSession):
    """Повторное назначение того же курьера не должно вызывать ошибку."""
    db = db_with_data
    await _add_courier(db, courier_id=1, type_id=2)
    await create_order(db, make_order_data(order_id=1, weight=5.0))

    order1 = await assign_courier(db, 1, 1)
    order2 = await assign_courier(db, 1, 1)  # повторно
    assert order2.status == OrderStatus.assigned
    assert order2.courier_id == 1


async def test_assign_courier_order_not_found(db_with_data: AsyncSession):
    db = db_with_data
    await _add_courier(db)

    result = await assign_courier(db, order_id=999, courier_id=1)
    assert result is None


async def test_assign_courier_not_found(db_with_data: AsyncSession):
    db = db_with_data
    await create_order(db, make_order_data(order_id=1, weight=5.0))

    with pytest.raises(ValueError, match="Курьер не найден"):
        await assign_courier(db, order_id=1, courier_id=999)


async def test_assign_courier_weight_too_heavy(db_with_data: AsyncSession):
    """Пеший курьер (max 10 kg) не может взять 11 кг."""
    db = db_with_data
    await _add_courier(db, courier_id=1, type_id=1)  # foot, max 10 kg
    await create_order(db, make_order_data(order_id=1, weight=11.0))

    with pytest.raises(ValueError, match="максимум"):
        await assign_courier(db, order_id=1, courier_id=1)


async def test_assign_courier_already_assigned_to_other(db_with_data: AsyncSession):
    """Заказ уже назначен на другого курьера → ValueError."""
    db = db_with_data
    await _add_courier(db, courier_id=1, type_id=2)
    await _add_courier(db, courier_id=2, type_id=2)
    await create_order(db, make_order_data(order_id=1, weight=5.0))

    await assign_courier(db, order_id=1, courier_id=1)

    with pytest.raises(ValueError):
        await assign_courier(db, order_id=1, courier_id=2)


async def test_assign_completed_order_raises(db_with_data: AsyncSession):
    db = db_with_data
    await _add_courier(db, courier_id=1, type_id=2)

    t = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    db.add(Order(
        order_id=1, weight=3.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed, courier_id=1,
        assign_time=t, complete_time=t + timedelta(minutes=30),
    ))
    await db.commit()

    with pytest.raises(ValueError, match="completed"):
        await assign_courier(db, order_id=1, courier_id=1)


# ---------------------------------------------------------------------------
# CRUD: complete_order
# ---------------------------------------------------------------------------

async def test_complete_order_success(db_with_data: AsyncSession):
    db = db_with_data
    await _add_courier(db, courier_id=1, type_id=2)
    await create_order(db, make_order_data(order_id=1, weight=5.0))
    await assign_courier(db, 1, 1)

    order = await complete_order(db, order_id=1)
    assert order is not None
    assert order.status == OrderStatus.completed
    assert order.complete_time is not None


async def test_complete_order_not_found(db_with_data: AsyncSession):
    result = await complete_order(db_with_data, order_id=999)
    assert result is None


async def test_complete_pending_order_raises(db_with_data: AsyncSession):
    db = db_with_data
    await create_order(db, make_order_data(order_id=1, weight=1.0))

    with pytest.raises(ValueError, match="pending"):
        await complete_order(db, order_id=1)


async def test_complete_already_completed_raises(db_with_data: AsyncSession):
    db = db_with_data
    await _add_courier(db, courier_id=1, type_id=2)
    await create_order(db, make_order_data(order_id=1, weight=5.0))
    await assign_courier(db, 1, 1)
    await complete_order(db, 1)

    with pytest.raises(ValueError, match="completed"):
        await complete_order(db, 1)


# ---------------------------------------------------------------------------
# Weight limits per courier type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("type_id,weight,should_succeed", [
    (1, 10.0, True),   # foot, exactly max
    (1, 10.01, False), # foot, over max
    (2, 15.0, True),   # bike, exactly max
    (2, 15.01, False), # bike, over max
    (3, 50.0, True),   # car, exactly max
])
async def test_assign_weight_limits(
    db_with_data: AsyncSession, type_id: int, weight: float, should_succeed: bool
):
    db = db_with_data
    await _add_courier(db, courier_id=1, type_id=type_id)
    await create_order(db, make_order_data(order_id=1, weight=weight))

    if should_succeed:
        order = await assign_courier(db, 1, 1)
        assert order.status == OrderStatus.assigned
    else:
        with pytest.raises(ValueError):
            await assign_courier(db, 1, 1)
