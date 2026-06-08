"""Тесты для моделей Courier, CourierRegion и CRUD-функций курьеров."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from backend.models.courier import Courier, CourierRegion
from backend.crud.courier import (
    get_courier,
    get_all_couriers,
    create_courier,
    update_courier,
    get_courier_earnings,
    get_courier_rating,
)
from backend.schemas.courier import CourierCreate


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_courier_data(**kwargs) -> CourierCreate:
    defaults = dict(
        courier_id=1,
        courier_type_id=1,
        working_hours=["09:00-18:00"],
        regions=[1, 2],
        email="courier1@example.com",
        password="pass",
    )
    defaults.update(kwargs)
    return CourierCreate(**defaults)


# ---------------------------------------------------------------------------
# Courier model
# ---------------------------------------------------------------------------

async def test_create_courier_model(db_with_data: AsyncSession):
    db = db_with_data
    courier = Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"])
    db.add(courier)
    await db.commit()
    await db.refresh(courier)

    assert courier.courier_id == 1
    assert courier.courier_type_id == 1
    assert courier.working_hours == ["09:00-18:00"]


async def test_courier_id_must_be_positive(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=0, courier_type_id=1, working_hours=["09:00-18:00"]))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_courier_type_fk_constraint(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=99, working_hours=["09:00-18:00"]))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_courier_primary_key_unique(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["10:00-18:00"]))
    await db.commit()

    db.add(Courier(courier_id=1, courier_type_id=2, working_hours=["11:00-20:00"]))
    with pytest.raises(IntegrityError):
        await db.commit()


# ---------------------------------------------------------------------------
# CourierRegion model
# ---------------------------------------------------------------------------

async def test_create_courier_region(db_with_data: AsyncSession):
    db = db_with_data
    courier = Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"])
    db.add(courier)
    await db.commit()

    region = CourierRegion(courier_id=1, region=5)
    db.add(region)
    await db.commit()
    await db.refresh(region)

    assert region.id is not None
    assert region.region == 5


async def test_courier_region_positive_constraint(db_with_data: AsyncSession):
    db = db_with_data
    courier = Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"])
    db.add(courier)
    await db.commit()

    db.add(CourierRegion(courier_id=1, region=0))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_courier_region_unique_constraint(db_with_data: AsyncSession):
    db = db_with_data
    courier = Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"])
    db.add(courier)
    await db.commit()

    db.add(CourierRegion(courier_id=1, region=3))
    await db.commit()

    db.add(CourierRegion(courier_id=1, region=3))
    with pytest.raises(IntegrityError):
        await db.commit()


async def test_courier_region_cascade_delete(db_with_data: AsyncSession):
    db = db_with_data
    courier = Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"])
    db.add(courier)
    await db.commit()
    db.add(CourierRegion(courier_id=1, region=1))
    db.add(CourierRegion(courier_id=1, region=2))
    await db.commit()

    await db.delete(courier)
    await db.commit()

    result = await db.execute(
        select(CourierRegion).filter(CourierRegion.courier_id == 1)
    )
    assert result.scalars().all() == []


# ---------------------------------------------------------------------------
# CRUD: get_courier
# ---------------------------------------------------------------------------

async def test_get_courier_existing(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=42, courier_type_id=2, working_hours=["08:00-20:00"]))
    await db.commit()

    found = await get_courier(db, 42)
    assert found is not None
    assert found.courier_id == 42


async def test_get_courier_not_found(db_with_data: AsyncSession):
    result = await get_courier(db_with_data, 999)
    assert result is None


# ---------------------------------------------------------------------------
# CRUD: get_all_couriers
# ---------------------------------------------------------------------------

async def test_get_all_couriers_empty(db_with_data: AsyncSession):
    couriers = await get_all_couriers(db_with_data)
    assert couriers == []


async def test_get_all_couriers_multiple(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-17:00"]))
    db.add(Courier(courier_id=2, courier_type_id=2, working_hours=["10:00-20:00"]))
    await db.commit()

    couriers = await get_all_couriers(db)
    assert len(couriers) == 2


# ---------------------------------------------------------------------------
# CRUD: create_courier
# ---------------------------------------------------------------------------

async def test_create_courier_crud(db_with_data: AsyncSession):
    courier = await create_courier(db_with_data, make_courier_data())
    assert courier.courier_id == 1
    assert courier.courier_type_id == 1

    regions = await db_with_data.execute(
        select(CourierRegion).filter(CourierRegion.courier_id == 1)
    )
    region_rows = regions.scalars().all()
    assert {r.region for r in region_rows} == {1, 2}


async def test_create_courier_creates_user(db_with_data: AsyncSession):
    from backend.models.user import User

    await create_courier(db_with_data, make_courier_data())

    result = await db_with_data.execute(
        select(User).filter(User.email == "courier1@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.courier_id == 1
    assert user.role_id == 1


# ---------------------------------------------------------------------------
# CRUD: update_courier
# ---------------------------------------------------------------------------

async def test_update_courier(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    updated = await update_courier(db, 1, {"courier_type_id": 3})
    assert updated is not None
    assert updated.courier_type_id == 3


async def test_update_courier_not_found(db_with_data: AsyncSession):
    result = await update_courier(db_with_data, 999, {"courier_type_id": 2})
    assert result is None


async def test_update_courier_ignores_unknown_fields(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    updated = await update_courier(db, 1, {"nonexistent_field": "value"})
    assert updated is not None  # не упал, просто проигнорировал


# ---------------------------------------------------------------------------
# CRUD: get_courier_earnings
# ---------------------------------------------------------------------------

async def test_earnings_no_completed_orders(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    earnings = await get_courier_earnings(db, 1)
    assert earnings == 0


async def test_earnings_foot_courier(db_with_data: AsyncSession):
    """Пеший курьер: коэффициент 2. Один выполненный заказ → 500 * 2 * 1 = 1000."""
    from datetime import datetime, timezone
    from backend.models.order import Order, OrderStatus

    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    order = Order(
        order_id=1,
        weight=1.0,
        region=1,
        delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed,
        courier_id=1,
        assign_time=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
        complete_time=datetime(2024, 1, 1, 10, 30, tzinfo=timezone.utc),
    )
    db.add(order)
    await db.commit()

    earnings = await get_courier_earnings(db, 1)
    assert earnings == 1000


async def test_earnings_bike_courier(db_with_data: AsyncSession):
    """Велокурьер: коэффициент 5. Два выполненных заказа → 500 * 5 * 2 = 5000."""
    from datetime import datetime, timezone, timedelta
    from backend.models.order import Order, OrderStatus

    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=2, working_hours=["09:00-18:00"]))
    await db.commit()

    for i in range(1, 3):
        db.add(Order(
            order_id=i,
            weight=1.0,
            region=1,
            delivery_hours=["09:00-18:00"],
            status=OrderStatus.completed,
            courier_id=1,
            assign_time=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
            complete_time=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc) + timedelta(minutes=30 * i),
        ))
    await db.commit()

    earnings = await get_courier_earnings(db, 1)
    assert earnings == 5000


async def test_earnings_car_courier(db_with_data: AsyncSession):
    """Курьер на машине: коэффициент 9. Один заказ → 500 * 9 = 4500."""
    from datetime import datetime, timezone
    from backend.models.order import Order, OrderStatus

    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=3, working_hours=["09:00-18:00"]))
    await db.commit()

    db.add(Order(
        order_id=1,
        weight=5.0,
        region=2,
        delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed,
        courier_id=1,
        assign_time=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
        complete_time=datetime(2024, 1, 1, 9, 45, tzinfo=timezone.utc),
    ))
    await db.commit()

    earnings = await get_courier_earnings(db, 1)
    assert earnings == 4500


async def test_earnings_only_completed_count(db_with_data: AsyncSession):
    """Pending и assigned заказы не влияют на заработок."""
    from datetime import datetime, timezone
    from backend.models.order import Order, OrderStatus

    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=2, working_hours=["09:00-18:00"]))
    await db.commit()

    db.add(Order(
        order_id=1, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.pending,
    ))
    db.add(Order(
        order_id=2, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.assigned, courier_id=1,
        assign_time=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
    ))
    db.add(Order(
        order_id=3, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed, courier_id=1,
        assign_time=datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc),
        complete_time=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
    ))
    await db.commit()

    earnings = await get_courier_earnings(db, 1)
    assert earnings == 2500  # 500 * 5 * 1


async def test_earnings_courier_not_found(db_with_data: AsyncSession):
    result = await get_courier_earnings(db_with_data, 999)
    assert result is None


# ---------------------------------------------------------------------------
# CRUD: get_courier_rating
# ---------------------------------------------------------------------------

async def test_rating_no_completed_orders(db_with_data: AsyncSession):
    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    rating = await get_courier_rating(db, 1)
    assert rating is None


async def test_rating_fast_delivery(db_with_data: AsyncSession):
    """Доставка за 1 минуту → рейтинг близок к 5."""
    from datetime import datetime, timezone, timedelta
    from backend.models.order import Order, OrderStatus

    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    t0 = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    db.add(Order(
        order_id=1, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed, courier_id=1,
        assign_time=t0,
        complete_time=t0 + timedelta(minutes=1),
    ))
    await db.commit()

    rating = await get_courier_rating(db, 1)
    assert rating is not None
    assert 4.9 <= rating <= 5.0


async def test_rating_hour_delivery(db_with_data: AsyncSession):
    """Доставка ровно за 3600 секунд → рейтинг = 0."""
    from datetime import datetime, timezone, timedelta
    from backend.models.order import Order, OrderStatus

    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    t0 = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    db.add(Order(
        order_id=1, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed, courier_id=1,
        assign_time=t0,
        complete_time=t0 + timedelta(seconds=3600),
    ))
    await db.commit()

    rating = await get_courier_rating(db, 1)
    assert rating == 0.0


async def test_rating_multiple_regions(db_with_data: AsyncSession):
    """Рейтинг берётся по минимальному среднему времени регионов."""
    from datetime import datetime, timezone, timedelta
    from backend.models.order import Order, OrderStatus

    db = db_with_data
    db.add(Courier(courier_id=1, courier_type_id=1, working_hours=["09:00-18:00"]))
    await db.commit()

    t0 = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    # Регион 1: 30 мин, регион 2: 120 мин → min = 1800 сек
    db.add(Order(
        order_id=1, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed, courier_id=1,
        assign_time=t0,
        complete_time=t0 + timedelta(minutes=30),
    ))
    db.add(Order(
        order_id=2, weight=1.0, region=2, delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed, courier_id=1,
        assign_time=t0,
        complete_time=t0 + timedelta(minutes=30 + 120),
    ))
    await db.commit()

    rating = await get_courier_rating(db, 1)
    assert rating is not None
    # t=1800 → (3600-1800)/3600*5 = 2.5
    assert rating == pytest.approx(2.5, abs=0.01)