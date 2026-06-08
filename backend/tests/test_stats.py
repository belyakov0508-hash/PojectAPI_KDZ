"""
Тесты API-эндпоинтов статистики:
  GET /api/orders/my/stats          — статистика курьера (его токен)
  GET /api/couriers/{id}/rating     — рейтинг курьера (диспетчер)
  GET /api/couriers/{id}/earnings   — заработок курьера (диспетчер)
"""
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.core.database import get_db
from backend.core.security import create_access_token
from backend.crud.courier import create_courier
from backend.models.courier import Courier
from backend.models.order import Order, OrderStatus
from backend.schemas.courier import CourierCreate


pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(db_with_data: AsyncSession):
    async def override_get_db():
        yield db_with_data

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


def _dispatcher_headers() -> dict:
    token = create_access_token({"sub": "disp@example.com", "role": 2, "courier_id": None})
    return {"Authorization": f"Bearer {token}"}


def _courier_headers(courier_id: int) -> dict:
    token = create_access_token({"sub": f"c{courier_id}@example.com", "role": 1, "courier_id": courier_id})
    return {"Authorization": f"Bearer {token}"}


async def _make_courier(db: AsyncSession, courier_id: int, type_id: int = 2) -> None:
    """Создаёт курьера в БД через CRUD."""
    await create_courier(
        db,
        CourierCreate(
            courier_id=courier_id,
            courier_type_id=type_id,
            working_hours=["09:00-18:00"],
            regions=[1, 2],
            email=f"c{courier_id}@example.com",
            password="pw",
        ),
    )


async def _add_completed_order(
    db: AsyncSession,
    order_id: int,
    courier_id: int,
    region: int = 1,
    assign_offset_min: int = 0,
    complete_offset_min: int = 30,
    base: datetime | None = None,
) -> Order:
    """Добавляет завершённый заказ с заданными временны́ми отступами от base."""
    if base is None:
        base = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    order = Order(
        order_id=order_id,
        weight=1.0,
        region=region,
        delivery_hours=["09:00-18:00"],
        status=OrderStatus.completed,
        courier_id=courier_id,
        assign_time=base + timedelta(minutes=assign_offset_min),
        complete_time=base + timedelta(minutes=complete_offset_min),
    )
    db.add(order)
    await db.commit()
    return order


# ===========================================================================
# GET /api/orders/my/stats
# ===========================================================================

async def test_my_stats_no_completed_orders(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Курьер без выполненных заказов → completed=0, rating=None, earnings=0."""
    await _make_courier(db_with_data, courier_id=1, type_id=1)

    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(1))
    assert resp.status_code == 200
    body = resp.json()
    assert body["courier_id"] == 1
    assert body["completed"] == 0
    assert body["rating"] is None
    assert body["earnings"] == 0


async def test_my_stats_foot_courier_one_order(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Пеший курьер (коэффициент 2), 1 заказ → earnings = 500*2*1 = 1000."""
    await _make_courier(db_with_data, courier_id=2, type_id=1)
    await _add_completed_order(db_with_data, order_id=1, courier_id=2,
                                assign_offset_min=0, complete_offset_min=20)

    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(2))
    assert resp.status_code == 200
    body = resp.json()
    assert body["completed"] == 1
    assert body["earnings"] == 1000
    assert body["rating"] is not None


async def test_my_stats_bike_courier_two_orders(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Велокурьер (коэффициент 5), 2 заказа → earnings = 500*5*2 = 5000."""
    await _make_courier(db_with_data, courier_id=3, type_id=2)
    base = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    await _add_completed_order(db_with_data, 1, 3, complete_offset_min=30, base=base)
    await _add_completed_order(db_with_data, 2, 3, complete_offset_min=60, base=base)

    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(3))
    body = resp.json()
    assert body["completed"] == 2
    assert body["earnings"] == 5000


async def test_my_stats_car_courier(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Курьер на машине (коэффициент 9), 3 заказа → earnings = 500*9*3 = 13500."""
    await _make_courier(db_with_data, courier_id=4, type_id=3)
    base = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    for i in range(1, 4):
        await _add_completed_order(db_with_data, i, 4,
                                    complete_offset_min=30 * i, base=base)

    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(4))
    body = resp.json()
    assert body["completed"] == 3
    assert body["earnings"] == 13500


async def test_my_stats_rating_fast_delivery(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Доставка за 1 минуту → рейтинг близок к 5.0."""
    await _make_courier(db_with_data, courier_id=5, type_id=1)
    await _add_completed_order(db_with_data, 1, 5,
                                assign_offset_min=0, complete_offset_min=1)

    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(5))
    body = resp.json()
    assert body["rating"] is not None
    assert body["rating"] >= 4.9


async def test_my_stats_rating_hour_delivery(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Доставка ровно 1 час → рейтинг = 0.0."""
    await _make_courier(db_with_data, courier_id=6, type_id=1)
    await _add_completed_order(db_with_data, 1, 6,
                                assign_offset_min=0, complete_offset_min=60)

    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(6))
    body = resp.json()
    assert body["rating"] == 0.0


async def test_my_stats_courier_not_in_db(client: AsyncClient):
    """Токен курьера, которого нет в БД → 404."""
    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(9999))
    assert resp.status_code == 404


async def test_my_stats_response_has_required_fields(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Ответ содержит все обязательные поля."""
    await _make_courier(db_with_data, courier_id=7, type_id=2)
    resp = await client.get("/api/orders/my/stats", headers=_courier_headers(7))
    body = resp.json()
    for field in ("courier_id", "completed", "rating", "earnings"):
        assert field in body, f"Поле '{field}' отсутствует в ответе"


# ===========================================================================
# GET /api/couriers/{courier_id}/rating  (диспетчер)
# ===========================================================================

async def test_courier_rating_no_orders(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Рейтинг курьера без завершённых заказов → rating=None."""
    await _make_courier(db_with_data, courier_id=10, type_id=1)

    resp = await client.get("/api/couriers/10/rating", headers=_dispatcher_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["courier_id"] == 10
    assert body["rating"] is None


async def test_courier_rating_with_fast_order(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Быстрая доставка → рейтинг близок к 5."""
    await _make_courier(db_with_data, courier_id=11, type_id=2)
    await _add_completed_order(db_with_data, 1, 11,
                                assign_offset_min=0, complete_offset_min=5)

    resp = await client.get("/api/couriers/11/rating", headers=_dispatcher_headers())
    body = resp.json()
    assert body["rating"] is not None
    assert body["rating"] > 4.5


async def test_courier_rating_not_found(client: AsyncClient):
    """Несуществующий курьер → 404."""
    resp = await client.get("/api/couriers/9999/rating", headers=_dispatcher_headers())
    assert resp.status_code == 404


async def test_courier_rating_multiple_regions(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Рейтинг считается по минимальному среднему из регионов."""
    await _make_courier(db_with_data, courier_id=12, type_id=1)
    base = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

    # Регион 1: 30 мин → td=1800 с
    await _add_completed_order(db_with_data, 1, 12, region=1,
                                assign_offset_min=0, complete_offset_min=30, base=base)
    # Регион 2: ещё 120 мин → td=7200 с (от complete предыдущего)
    await _add_completed_order(db_with_data, 2, 12, region=2,
                                complete_offset_min=150, base=base)

    resp = await client.get("/api/couriers/12/rating", headers=_dispatcher_headers())
    body = resp.json()
    # t = min(1800, 7200) = 1800 → (3600-1800)/3600*5 = 2.5
    assert body["rating"] == pytest.approx(2.5, abs=0.01)


# ===========================================================================
# GET /api/couriers/{courier_id}/earnings  (диспетчер)
# ===========================================================================

async def test_courier_earnings_no_orders(
    client: AsyncClient, db_with_data: AsyncSession
):
    await _make_courier(db_with_data, courier_id=20, type_id=1)
    resp = await client.get("/api/couriers/20/earnings", headers=_dispatcher_headers())
    assert resp.status_code == 200
    assert resp.json()["earnings"] == 0


async def test_courier_earnings_foot_one_order(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Пеший, 1 заказ → 1000."""
    await _make_courier(db_with_data, courier_id=21, type_id=1)
    await _add_completed_order(db_with_data, 1, 21)

    resp = await client.get("/api/couriers/21/earnings", headers=_dispatcher_headers())
    assert resp.json()["earnings"] == 1000


async def test_courier_earnings_bike_multiple_orders(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Велокурьер, 3 заказа → 500*5*3 = 7500."""
    await _make_courier(db_with_data, courier_id=22, type_id=2)
    base = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    for i in range(1, 4):
        await _add_completed_order(db_with_data, i, 22,
                                    complete_offset_min=30 * i, base=base)

    resp = await client.get("/api/couriers/22/earnings", headers=_dispatcher_headers())
    assert resp.json()["earnings"] == 7500


async def test_courier_earnings_not_found(client: AsyncClient):
    resp = await client.get("/api/couriers/9999/earnings", headers=_dispatcher_headers())
    assert resp.status_code == 404


async def test_courier_earnings_response_fields(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Ответ содержит courier_id и earnings."""
    await _make_courier(db_with_data, courier_id=23, type_id=3)
    resp = await client.get("/api/couriers/23/earnings", headers=_dispatcher_headers())
    body = resp.json()
    assert "courier_id" in body
    assert "earnings" in body
    assert body["courier_id"] == 23


async def test_courier_earnings_only_completed_count(
    client: AsyncClient, db_with_data: AsyncSession
):
    """pending и assigned заказы не учитываются в заработке."""
    await _make_courier(db_with_data, courier_id=24, type_id=2)
    base = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)

    # 1 завершённый
    await _add_completed_order(db_with_data, 1, 24, complete_offset_min=30, base=base)

    # 1 assigned — не считается
    db = db_with_data
    db.add(Order(
        order_id=2, weight=1.0, region=1, delivery_hours=["09:00-18:00"],
        status=OrderStatus.assigned, courier_id=24,
        assign_time=base,
    ))
    await db.commit()

    resp = await client.get("/api/couriers/24/earnings", headers=_dispatcher_headers())
    # Только 1 завершённый: 500 * 5 * 1 = 2500
    assert resp.json()["earnings"] == 2500
