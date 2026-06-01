import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.core.database import get_db
from backend.models.order import Order, OrderStatus

router = APIRouter(prefix="/api/orders", tags=["Orders"])
dispatcher_router = APIRouter(prefix="/api/dispatcher", tags=["Dispatcher"])


@dispatcher_router.post("/upload-orders")
async def upload_orders(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате JSON")

    try:
        contents = await file.read()
        data = json.loads(contents)

        for item in data:
            order = Order(
                order_id=item["order_id"],
                weight=item["weight"],
                region=item["region"],
                delivery_hours=item["delivery_hours"],
                status=OrderStatus.pending,
            )
            db.add(order)

        await db.commit()
        return {"message": f"Успешно импортировано заказов: {len(data)}"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@router.get("/")
async def get_all_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order))
    return result.scalars().all()


@router.get("/courier/{courier_id}")
async def get_courier_orders(courier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).filter(Order.courier_id == courier_id))
    return result.scalars().all()


@router.post("/{order_id}/complete")
async def complete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).filter(Order.order_id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    order.status = OrderStatus.completed
    order.complete_time = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Заказ выполнен", "order_id": order_id}


@router.patch("/{order_id}/assign")
async def assign_courier(order_id: int, courier_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).filter(Order.order_id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    order.courier_id = courier_id
    order.status = OrderStatus.assigned
    order.assign_time = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Курьер назначен", "order_id": order_id, "courier_id": courier_id}