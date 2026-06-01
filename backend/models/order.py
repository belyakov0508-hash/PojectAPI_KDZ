import enum
from sqlalchemy import Integer, String, Numeric, ForeignKey, ARRAY, TIMESTAMP, CheckConstraint, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base

class OrderStatus(enum.Enum):
    pending   = "pending"
    assigned  = "assigned"
    completed = "completed"

class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    weight: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    region: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_hours: Mapped[list[str]] = mapped_column(ARRAY(String(11)), nullable=False)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status_enum"),
        nullable=False, default=OrderStatus.pending
    )
    courier_id: Mapped[int | None] = mapped_column(
        ForeignKey("couriers.courier_id", ondelete="SET NULL"), nullable=True
    )
    assign_time = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    complete_time = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    courier = relationship("Courier", back_populates="orders")

    __table_args__ = (
        CheckConstraint("order_id > 0", name="check_order_id_positive"),
        CheckConstraint("region > 0", name="check_order_region_positive"),
        CheckConstraint("weight >= 0.01 AND weight <= 50.00", name="check_order_weight_range"),
        Index("idx_orders_status_region", "status", "region"),
    )