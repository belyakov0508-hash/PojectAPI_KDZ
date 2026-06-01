import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.schemas.courier import CourierCreate, CourierResponse
from backend.crud.courier import get_courier, get_all_couriers, create_courier, update_courier

router = APIRouter(prefix="/api/couriers", tags=["Couriers"])
monitoring_router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


# Получить всех курьеров
@monitoring_router.get("/couriers", response_model=list[CourierResponse])
async def get_all_couriers_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_all_couriers(db)


# Загрузка JSON-файла курьеров
@monitoring_router.post("/upload-couriers")
async def upload_couriers(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
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


# Получить курьера по ID
@router.get("/{courier_id}", response_model=CourierResponse)
async def get_courier_endpoint(courier_id: int, db: AsyncSession = Depends(get_db)):
    courier = await get_courier(db, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    return courier


# Обновить данные курьера
@router.patch("/{courier_id}", response_model=CourierResponse)
async def update_courier_endpoint(courier_id: int, update_data: dict, db: AsyncSession = Depends(get_db)):
    courier = await update_courier(db, courier_id, update_data)
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    return courier


# Создать курьера
@router.post("/", response_model=CourierResponse)
async def create_courier_endpoint(data: CourierCreate, db: AsyncSession = Depends(get_db)):
    return await create_courier(db, data)