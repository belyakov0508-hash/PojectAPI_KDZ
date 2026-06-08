"""Тесты API-эндпоинтов аутентификации: POST /api/auth/login."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.core.database import get_db
from backend.crud.user import create_user


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Вспомогательная фикстура: клиент с подменённой БД
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(db_with_data: AsyncSession):
    """HTTP-клиент, использующий тестовую in-memory БД."""
    async def override_get_db():
        yield db_with_data

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Вспомогательная функция: создать пользователя в БД
# ---------------------------------------------------------------------------

async def _add_user(db: AsyncSession, email: str, password: str, role_id: int = 2):
    """Добавляет пользователя напрямую в БД (пароль хранится в открытом виде)."""
    return await create_user(db, email=email, password=password, role_id=role_id)


# ---------------------------------------------------------------------------
# POST /api/auth/login — успешный вход
# ---------------------------------------------------------------------------

async def test_login_success(client: AsyncClient, db_with_data: AsyncSession):
    await _add_user(db_with_data, "disp@example.com", "secret", role_id=2)

    resp = await client.post("/api/auth/login", json={
        "email": "disp@example.com",
        "password": "secret",
    })

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 10


async def test_login_returns_jwt_with_correct_claims(
    client: AsyncClient, db_with_data: AsyncSession
):
    """Токен содержит sub (email) и role."""
    import jwt as pyjwt
    from backend.core.security import SECRET_KEY, ALGORITHM

    await _add_user(db_with_data, "disp2@example.com", "pass2", role_id=2)
    resp = await client.post("/api/auth/login", json={
        "email": "disp2@example.com",
        "password": "pass2",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "disp2@example.com"
    assert payload["role"] == 2


# ---------------------------------------------------------------------------
# POST /api/auth/login — неверные данные
# ---------------------------------------------------------------------------

async def test_login_wrong_password(client: AsyncClient, db_with_data: AsyncSession):
    await _add_user(db_with_data, "user@example.com", "correct")

    resp = await client.post("/api/auth/login", json={
        "email": "user@example.com",
        "password": "wrong",
    })

    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "any",
    })
    assert resp.status_code == 401


async def test_login_missing_email_field(client: AsyncClient):
    """Запрос без поля email — 422 Unprocessable Entity."""
    resp = await client.post("/api/auth/login", json={"password": "pass"})
    assert resp.status_code == 422


async def test_login_missing_password_field(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"email": "a@b.com"})
    assert resp.status_code == 422


async def test_login_empty_body(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={})
    assert resp.status_code == 422


async def test_login_empty_email_string(client: AsyncClient, db_with_data: AsyncSession):
    """Пустая строка email → 401 (пользователь не найден)."""
    resp = await client.post("/api/auth/login", json={"email": "", "password": "x"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Защищённые эндпоинты без токена / с невалидным токеном
# ---------------------------------------------------------------------------

async def test_protected_endpoint_without_token(client: AsyncClient):
    """GET /api/orders/ без заголовка Authorization → 403."""
    resp = await client.get("/api/orders/")
    assert resp.status_code in (401, 403)


async def test_protected_endpoint_with_invalid_token(client: AsyncClient):
    """Невалидный JWT → 401."""
    resp = await client.get(
        "/api/orders/",
        headers={"Authorization": "Bearer totally.invalid.token"},
    )
    assert resp.status_code == 401


async def test_protected_endpoint_with_malformed_header(client: AsyncClient):
    """Заголовок без схемы Bearer → 401 или 403 (зависит от FastAPI HTTPBearer)."""
    resp = await client.get(
        "/api/orders/",
        headers={"Authorization": "justtoken"},
    )
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Токен работает на защищённом эндпоинте
# ---------------------------------------------------------------------------

async def test_valid_token_grants_access(client: AsyncClient, db_with_data: AsyncSession):
    """После успешного логина токен принимается на защищённом эндпоинте."""
    await _add_user(db_with_data, "disp_access@example.com", "pw", role_id=2)
    login = await client.post("/api/auth/login", json={
        "email": "disp_access@example.com",
        "password": "pw",
    })
    token = login.json()["access_token"]

    resp = await client.get(
        "/api/orders/",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Диспетчер имеет доступ → не 401/403
    assert resp.status_code == 200
