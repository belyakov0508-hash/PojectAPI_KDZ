"""
Тесты разграничения прав доступа на уровне API.

Роли:
  role_id=1  →  courier   (require_courier)
  role_id=2  →  dispatcher (require_dispatcher)

Матрица проверок:
  - Эндпоинты диспетчера недоступны курьеру (403)
  - Эндпоинты курьера недоступны диспетчеру (403)
  - Без токена — 401/403
  - С правильной ролью — 200 / 2xx
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.core.database import get_db
from backend.core.security import create_access_token
from backend.crud.courier import create_courier
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


def _dispatcher_token(email: str = "disp@example.com") -> str:
    return create_access_token({"sub": email, "role": 2, "courier_id": None})


def _courier_token(courier_id: int, email: str = "courier@example.com") -> str:
    return create_access_token({"sub": email, "role": 1, "courier_id": courier_id})


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Эндпоинты, требующие роль DISPATCHER
# ---------------------------------------------------------------------------

DISPATCHER_ENDPOINTS = [
    ("GET",   "/api/orders/"),
    ("GET",   "/api/monitoring/couriers"),
    ("GET",   "/api/monitoring/available-orders"),
    ("GET",   "/api/couriers/1"),
    ("GET",   "/api/couriers/1/rating"),
    ("GET",   "/api/couriers/1/earnings"),
]


@pytest.mark.parametrize("method,url", DISPATCHER_ENDPOINTS)
async def test_dispatcher_endpoint_forbidden_for_courier(
    client: AsyncClient, method: str, url: str
):
    """Курьер не может обратиться к эндпоинту диспетчера → 403."""
    token = _courier_token(courier_id=1)
    resp = await client.request(method, url, headers=_auth(token))
    assert resp.status_code == 403


@pytest.mark.parametrize("method,url", DISPATCHER_ENDPOINTS)
async def test_dispatcher_endpoint_forbidden_without_token(
    client: AsyncClient, method: str, url: str
):
    """Без токена доступ к эндпоинту диспетчера запрещён → 401 или 403."""
    resp = await client.request(method, url)
    assert resp.status_code in (401, 403)


@pytest.mark.parametrize("method,url", [
    ("GET", "/api/orders/"),
    ("GET", "/api/monitoring/couriers"),
    ("GET", "/api/monitoring/available-orders"),
])
async def test_dispatcher_endpoint_allowed_for_dispatcher(
    client: AsyncClient, method: str, url: str
):
    """Диспетчер имеет доступ → 200."""
    token = _dispatcher_token()
    resp = await client.request(method, url, headers=_auth(token))
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Эндпоинты, требующие роль COURIER
# ---------------------------------------------------------------------------

COURIER_ENDPOINTS = [
    ("GET",  "/api/orders/my"),
    ("GET",  "/api/orders/my/stats"),
]


@pytest.mark.parametrize("method,url", COURIER_ENDPOINTS)
async def test_courier_endpoint_forbidden_for_dispatcher(
    client: AsyncClient, method: str, url: str
):
    """Диспетчер не может обратиться к курьерскому эндпоинту → 403."""
    token = _dispatcher_token()
    resp = await client.request(method, url, headers=_auth(token))
    assert resp.status_code == 403


@pytest.mark.parametrize("method,url", COURIER_ENDPOINTS)
async def test_courier_endpoint_forbidden_without_token(
    client: AsyncClient, method: str, url: str
):
    resp = await client.request(method, url)
    assert resp.status_code in (401, 403)


async def test_courier_endpoint_allowed_for_courier(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Курьер с валидным токеном получает свои заказы → 200."""
    await create_courier(
        db_with_data,
        CourierCreate(
            courier_id=10,
            courier_type_id=1,
            working_hours=["09:00-18:00"],
            regions=[1],
            email="c10@example.com",
            password="pw",
        ),
    )
    token = _courier_token(courier_id=10, email="c10@example.com")
    resp = await client.get("/api/orders/my", headers=_auth(token))
    assert resp.status_code == 200


async def test_courier_stats_allowed_for_courier(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Курьер с валидным токеном получает статистику → 200."""
    await create_courier(
        db_with_data,
        CourierCreate(
            courier_id=20,
            courier_type_id=2,
            working_hours=["09:00-18:00"],
            regions=[1],
            email="c20@example.com",
            password="pw",
        ),
    )
    token = _courier_token(courier_id=20, email="c20@example.com")
    resp = await client.get("/api/orders/my/stats", headers=_auth(token))
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST-эндпоинты создания — только диспетчер
# ---------------------------------------------------------------------------

async def test_create_order_forbidden_for_courier(client: AsyncClient):
    """POST /api/orders/ — только диспетчер."""
    token = _courier_token(courier_id=1)
    resp = await client.post(
        "/api/orders/",
        json={"order_id": 100, "weight": 1.5, "region": 1, "delivery_hours": ["09:00-18:00"]},
        headers=_auth(token),
    )
    assert resp.status_code == 403


async def test_create_order_allowed_for_dispatcher(
    client: AsyncClient, db_with_data: AsyncSession
):
    token = _dispatcher_token()
    resp = await client.post(
        "/api/orders/",
        json={"order_id": 200, "weight": 2.0, "region": 1, "delivery_hours": ["10:00-20:00"]},
        headers=_auth(token),
    )
    assert resp.status_code == 200


async def test_create_courier_endpoint_forbidden_for_courier(client: AsyncClient):
    """POST /api/couriers/ — только диспетчер."""
    token = _courier_token(courier_id=1)
    payload = {
        "courier_id": 99,
        "courier_type_id": 1,
        "working_hours": ["09:00-18:00"],
        "regions": [1],
        "email": "new@example.com",
        "password": "pw",
    }
    resp = await client.post("/api/couriers/", json=payload, headers=_auth(token))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH-эндпоинты — только диспетчер
# ---------------------------------------------------------------------------

async def test_assign_courier_forbidden_for_courier(client: AsyncClient):
    """PATCH /api/orders/{id}/assign — только диспетчер."""
    token = _courier_token(courier_id=1)
    resp = await client.patch(
        "/api/orders/1/assign?courier_id=1",
        headers=_auth(token),
    )
    assert resp.status_code == 403


async def test_complete_order_forbidden_for_dispatcher(client: AsyncClient):
    """POST /api/orders/{id}/complete — только курьер."""
    token = _dispatcher_token()
    resp = await client.post("/api/orders/1/complete", headers=_auth(token))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Загрузка файлов — только диспетчер
# ---------------------------------------------------------------------------

async def test_upload_orders_forbidden_for_courier(client: AsyncClient):
    token = _courier_token(courier_id=1)
    resp = await client.post(
        "/api/dispatcher/upload-orders",
        files={"file": ("orders.json", b"[]", "application/json")},
        headers=_auth(token),
    )
    assert resp.status_code == 403


async def test_upload_couriers_forbidden_for_courier(client: AsyncClient):
    token = _courier_token(courier_id=1)
    resp = await client.post(
        "/api/monitoring/upload-couriers",
        files={"file": ("couriers.json", b"[]", "application/json")},
        headers=_auth(token),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /api/monitoring/available-couriers — только диспетчер
# ---------------------------------------------------------------------------

async def test_available_couriers_forbidden_for_courier(client: AsyncClient):
    token = _courier_token(courier_id=1)
    resp = await client.get(
        "/api/monitoring/available-couriers?weight=5.0&region=1",
        headers=_auth(token),
    )
    assert resp.status_code == 403


async def test_available_couriers_allowed_for_dispatcher(client: AsyncClient):
    token = _dispatcher_token()
    resp = await client.get(
        "/api/monitoring/available-couriers?weight=5.0&region=1",
        headers=_auth(token),
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /health — публичный эндпоинт
# ---------------------------------------------------------------------------

async def test_health_is_public(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
