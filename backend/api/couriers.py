import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.core.database import get_db
from backend.core.security import require_dispatcher
from backend.models.courier import Courier
from backend.models.order import Order, OrderStatus
from backend.models.user import User
from backend.schemas.courier import CourierCreate
from backend.crud.courier import get_courier, create_courier, update_courier, get_courier_rating, get_courier_earnings
from backend.crud.order import COURIER_TYPE_MAX_WEIGHT

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
        rating = await get_courier_rating(db, courier.courier_id)
        earnings = await get_courier_earnings(db, courier.courier_id)
        couriers.append({
            "courier_id": courier.courier_id,
            "courier_type_id": courier.courier_type_id,
            "working_hours": courier.working_hours,
            "regions": courier.regions,
            "email": email,
            "password": password,
            "rating": rating,
            "earnings": earnings,
        })
    return couriers


# Получить доступные заказы (только pending) — только диспетчер
@monitoring_router.get("/available-orders")
async def get_available_orders_endpoint(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    result = await db.execute(
        select(Order).filter(Order.status == OrderStatus.pending)
    )
    orders = result.scalars().all()
    return [
        {
            "order_id": o.order_id,
            "weight": float(o.weight),
            "region": o.region,
            "delivery_hours": o.delivery_hours,
            "status": o.status.value,
        }
        for o in orders
    ]


# Получить курьеров, способных доставить заказ с указанным весом — только диспетчер
@monitoring_router.get("/available-couriers")
async def get_available_couriers_endpoint(
    weight: float = Query(..., gt=0, description="Вес заказа в кг"),
    region: int = Query(..., description="Регион заказа"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    # Определяем подходящие типы курьеров по весу
    suitable_type_ids = [
        type_id
        for type_id, max_weight in COURIER_TYPE_MAX_WEIGHT.items()
        if weight <= max_weight
    ]

    if not suitable_type_ids:
        return []

    result = await db.execute(
        select(Courier)
        .filter(Courier.courier_type_id.in_(suitable_type_ids))
        .options(selectinload(Courier.regions))
    )
    couriers_all = result.scalars().all()
    couriers = [c for c in couriers_all if region in [r.region for r in c.regions]]

    response = []
    for courier in couriers:
        rating = await get_courier_rating(db, courier.courier_id)
        earnings = await get_courier_earnings(db, courier.courier_id)
        response.append({
            "courier_id": courier.courier_id,
            "courier_type_id": courier.courier_type_id,
            "working_hours": courier.working_hours,
            "regions": [r.region for r in courier.regions],
            "rating": rating,
            "earnings": earnings,
        })

    return response


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
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка чтения файла: {str(e)}")

    # Проверяем какие ID уже существуют в БД
    invalid_ids = []
    for item in data:
        existing = await get_courier(db, item.get("courier_id"))
        if existing:
            invalid_ids.append(item.get("courier_id"))

    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail={"message": "Курьеры с такими ID уже существуют", "invalid_ids": invalid_ids}
        )

    try:
        for item in data:
            courier_data = CourierCreate(**item)
            await create_courier(db, courier_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")

    return {"message": f"Успешно импортировано курьеров: {len(data)}"}


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


# Получить рейтинг курьера — только диспетчер
@router.get("/{courier_id}/rating")
async def get_courier_rating_endpoint(
    courier_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    courier = await get_courier(db, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    rating = await get_courier_rating(db, courier_id)
    return {"courier_id": courier_id, "rating": rating}


# Получить заработок курьера — только диспетчер
@router.get("/{courier_id}/earnings")
async def get_courier_earnings_endpoint(
    courier_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    courier = await get_courier(db, courier_id)
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")
    earnings = await get_courier_earnings(db, courier_id)
    return {"courier_id": courier_id, "earnings": earnings}


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