import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.core.database import get_db
from backend.core.security import require_dispatcher
from backend.models.courier import Courier
from backend.models.user import User
from backend.schemas.courier import CourierCreate
from backend.crud.courier import get_courier, create_courier, update_courier

router = APIRouter(prefix="/api/couriers", tags=["Couriers"])
monitoring_router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


# Получить всех курьеров с регионами — только диспетчер
@monitoring_router.get("/couriers")
async def get_all_couriers_endpoint(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    result = await db.execute(
        select(Courier, User.email, User.hashed_password)
        .join(User, User.courier_id == Courier.courier_id, isouter=True)
        .options(selectinload(Courier.regions))
    )
    rows = result.all()
    couriers = []
    for courier, email, password in rows:
        couriers.append({
            "courier_id": courier.courier_id,
            "courier_type_id": courier.courier_type_id,
            "working_hours": courier.working_hours,
            "regions": courier.regions,
            "email": email,
            "password": password,
        })
    return couriers


# Загрузка JSON-файла курьеров — только диспетчер
@monitoring_router.post("/upload-couriers")
async def upload_couriers(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    if not file.filename or not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате JSON")
    try:
        contents = await file.read()
        data = json.loads(contents)
        for item in data:
            courier_data = CourierCreate(**item)
            await create_courier(db, courier_data)
        return {"message": f"Успешно импортировано курьеров: {len(data)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


# Получить курьера по ID — только диспетчер
@router.get("/{courier_id}")
async def get_courier_endpoint(
    courier_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    courier = await get_courier(db, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    return courier


# Обновить данные курьера — только диспетчер
@router.patch("/{courier_id}")
async def update_courier_endpoint(
    courier_id: int,
    update_data: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    courier = await update_courier(db, courier_id, update_data)
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    return courier


# Создать курьера — только диспетчер
@router.post("/")
async def create_courier_endpoint(
    data: CourierCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    return await create_courier(db, data)