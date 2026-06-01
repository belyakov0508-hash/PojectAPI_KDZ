from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.core.database import engine, Base
from backend.models import courier, order  # noqa: F401
from backend.api import couriers_router, monitoring_router, orders_router, dispatcher_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Courier API", lifespan=lifespan)

app.include_router(couriers_router)
app.include_router(monitoring_router)
app.include_router(orders_router)
app.include_router(dispatcher_router)


@app.get("/health")
async def health():
    return {"status": "ok"}