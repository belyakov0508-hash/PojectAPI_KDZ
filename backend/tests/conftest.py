import json
import pytest_asyncio
from sqlalchemy import Text, event
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator


# ---------------------------------------------------------------------------
# Патч ARRAY для SQLite
# ---------------------------------------------------------------------------

class ArrayAsJson(TypeDecorator):
    """Хранит list[str] как JSON TEXT в SQLite."""
    impl = Text
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


def _array_factory(*args, **kwargs):
    return ArrayAsJson()


import sqlalchemy as _sa
import sqlalchemy.sql.sqltypes as _sqltypes

_sa.ARRAY = _array_factory        # type: ignore[attr-defined]
_sqltypes.ARRAY = _array_factory  # type: ignore[attr-defined]

try:
    import sqlalchemy.dialects.postgresql as _pg
    _pg.ARRAY = _array_factory    # type: ignore[attr-defined]
except Exception:
    pass

# ---------------------------------------------------------------------------
# Импортируем модели ПОСЛЕ патча
# ---------------------------------------------------------------------------
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.core.database import Base
from backend.models import Role, CourierTypeTable, User, Courier, CourierRegion, Order  # noqa: F401


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncSession:
    """Создаёт чистую in-memory SQLite БД для каждого теста."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Включаем проверку внешних ключей в SQLite — по умолчанию она отключена
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_with_data(db: AsyncSession) -> AsyncSession:
    """БД с предзаполненными справочниками ролей и типов курьеров."""
    db.add(Role(id=1, name="courier"))
    db.add(Role(id=2, name="dispatcher"))
    db.add(CourierTypeTable(id=1, name="foot"))
    db.add(CourierTypeTable(id=2, name="bike"))
    db.add(CourierTypeTable(id=3, name="car"))
    await db.commit()
    return db