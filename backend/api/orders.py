import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.core.security import require_dispatcher, require_courier
from backend.schemas.order import OrderCreate, OrderResponse
from backend.crud.order import (
    get_all_orders, get_courier_orders,
    create_order, assign_courier, complete_order, get_order
)

router = APIRouter(prefix="/api/orders", tags=["Orders"])
dispatcher_router = APIRouter(prefix="/api/dispatcher", tags=["Dispatcher"])


# Загрузка JSON-файла заказов — только диспетчер
@dispatcher_router.post("/upload-orders")
async def upload_orders(
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
        existing = await get_order(db, item.get("order_id"))
        if existing:
            invalid_ids.append(item.get("order_id"))

    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail={"message": "Заказы с такими ID уже существуют", "invalid_ids": invalid_ids}
        )

    try:
        for item in data:
            order_data = OrderCreate(**item)
            await create_order(db, order_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")

    return {"message": f"Успешно импортировано заказов: {len(data)}"}


# Получить все заказы — только диспетчер
@router.get("/", response_model=list[OrderResponse])
async def get_all_orders_endpoint(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    return await get_all_orders(db)


# Получить свои заказы — только курьер
@router.get("/my", response_model=list[OrderResponse])
async def get_my_orders_endpoint(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_courier),
):
    return await get_courier_orders(db, user["courier_id"])


# Получить заказы курьера по ID — только диспетчер
@router.get("/courier/{courier_id}", response_model=list[OrderResponse])
async def get_courier_orders_endpoint(
    courier_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    return await get_courier_orders(db, courier_id)

# Посмотреть свою статистику — только курьер
@router.get("/my/stats")
async def get_my_stats(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_courier),
):
    from sqlalchemy import select
    from backend.models.order import Order
    from backend.models.courier import Courier

    courier_id = user["courier_id"]

    # Получаем тип курьера
    courier_result = await db.execute(
        select(Courier).where(Courier.courier_id == courier_id)
    )
    courier = courier_result.scalar_one_or_none()
    if not courier:
        raise HTTPException(status_code=404, detail="Курьер не найден")

    # Коэффициент зарплаты
    c = {1: 2, 2: 5, 3: 9}.get(courier.courier_type_id, 0)

    # Получаем все завершённые заказы курьера, отсортированные по времени завершения
    result = await db.execute(
        select(Order)
        .where(Order.courier_id == courier_id, Order.status == "completed")
        .order_by(Order.complete_time)
    )
    completed_orders = result.scalars().all()

    if not completed_orders:
        return {
            "courier_id": courier_id,
            "completed": 0,
            "rating": None,
            "earnings": 0,
        }

    # Зарплата
    earnings = len(completed_orders) * 500 * c

    # Рейтинг — считаем среднее время доставки по каждому региону
    # td[i] = среднее время доставки заказов в районе i
    region_times = {}  # region -> list of delivery times in seconds

    for i, order in enumerate(completed_orders):
        if order.complete_time is None:
            continue

        if i == 0:
            # Первый заказ: время = complete_time - assign_time
            if order.assign_time is None:
                continue
            delivery_time = (order.complete_time - order.assign_time).total_seconds()
        else:
            # Остальные: время = complete_time - complete_time предыдущего
            prev = completed_orders[i - 1]
            if prev.complete_time is None:
                continue
            delivery_time = (order.complete_time - prev.complete_time).total_seconds()

        region = order.region
        if region not in region_times:
            region_times[region] = []
        region_times[region].append(delivery_time)

    if not region_times:
        return {
            "courier_id": courier_id,
            "completed": len(completed_orders),
            "rating": None,
            "earnings": earnings,
        }

    # td[i] = среднее время по каждому региону
    td = [sum(times) / len(times) for times in region_times.values()]

    # t = минимальное из средних
    t = min(td)

    # Рейтинг
    rating = round((3600 - min(t, 3600)) / 3600 * 5, 2)

    return {
        "courier_id": courier_id,
        "completed": len(completed_orders),
        "rating": rating,
        "earnings": earnings,
    }


# Создать заказ — только диспетчер
@router.post("/", response_model=OrderResponse)
async def create_order_endpoint(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    return await create_order(db, data)


# Назначить курьера на заказ — только диспетчер
@router.patch("/{order_id}/assign", response_model=OrderResponse)
async def assign_courier_endpoint(
    order_id: int,
    courier_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_dispatcher),
):
    try:
        order = await assign_courier(db, order_id, courier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


# Завершить заказ — только курьер
@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order_endpoint(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_courier),
):
    try:
        order = await complete_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order