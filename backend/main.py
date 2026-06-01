from fastapi import FastAPI
from backend.core.database import engine, Base
import backend.models.courier
import backend.models.order

app = FastAPI(title="Courier API")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health():
    return {"status": "ok"}