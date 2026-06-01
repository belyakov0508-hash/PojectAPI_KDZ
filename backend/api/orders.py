import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.schemas.order import OrderCreate, OrderResponse
from backend.crud.order import (
    get_all_orders, get_courier_orders,
    create_order, assign_courier, complete_order
)

router = APIRouter(prefix="/api/orders", tags=["Orders"])
dispatcher_router = APIRouter(prefix="/api/dispatcher", tags=["Dispatcher"])


# Загрузка JSON-файла заказов
@dispatcher_router.post("/upload-orders")
async def upload_orders(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате JSON")
    try:
        contents = await file.read()
        data = json.loads(contents)
        for item in data:
            order_data = OrderCreate(**item)
            await create_order(db, order_data)
        return {"message": f"Успешно импортировано заказов: {len(data)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


# Получить все заказы
@router.get("/", response_model=list[OrderResponse])
async def get_all_orders_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_all_orders(db)


# Получить заказы курьера
@router.get("/courier/{courier_id}", response_model=list[OrderResponse])
async def get_courier_orders_endpoint(courier_id: int, db: AsyncSession = Depends(get_db)):
    return await get_courier_orders(db, courier_id)


# Создать заказ
@router.post("/", response_model=OrderResponse)
async def create_order_endpoint(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    return await create_order(db, data)


# Назначить курьера на заказ
@router.patch("/{order_id}/assign", response_model=OrderResponse)
async def assign_courier_endpoint(order_id: int, courier_id: int, db: AsyncSession = Depends(get_db)):
    order = await assign_courier(db, order_id, courier_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order


# Завершить заказ
@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order_endpoint(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await complete_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order