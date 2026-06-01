import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.database import get_db
from backend.models.courier import Courier, CourierRegion, CourierType

router = APIRouter(prefix="/api/couriers", tags=["Couriers"])
monitoring_router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@monitoring_router.get("/couriers")
async def get_all_couriers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Courier))
    return result.scalars().all()


@monitoring_router.post("/upload-couriers")
async def upload_couriers(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате JSON")

    try:
        contents = await file.read()
        data = json.loads(contents)

        for item in data:
            courier = Courier(
                courier_id=item["courier_id"],
                courier_type=CourierType(item["courier_type"]),
                working_hours=item["working_hours"],
            )
            db.add(courier)

            for region in item.get("regions", []):
                db.add(CourierRegion(courier_id=item["courier_id"], region=region))

        await db.commit()
        return {"message": f"Успешно импортировано курьеров: {len(data)}"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.get("/{courier_id}")
async def get_courier(courier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Courier).filter(Courier.courier_id == courier_id))
    courier = result.scalar_one_or_none()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    return courier


@router.patch("/{courier_id}")
async def update_courier(courier_id: int, update_data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Courier).filter(Courier.courier_id == courier_id))
    courier = result.scalar_one_or_none()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")

    for key, value in update_data.items():
        if hasattr(courier, key):
            setattr(courier, key, value)

    await db.commit()
    await db.refresh(courier)
    return {"message": "Данные курьера обновлены", "courier": courier}