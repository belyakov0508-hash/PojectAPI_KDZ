from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.database import engine, Base
from backend.models import courier, order  # noqa: F401
from backend.api import couriers_router, monitoring_router, orders_router, dispatcher_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Courier API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://26.8.60.217:5173",
        "http://26.156.210.186:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(couriers_router)
app.include_router(monitoring_router)
app.include_router(orders_router)
app.include_router(dispatcher_router)


@app.get("/health")
async def health():
    return {"status": "ok"}