from sqlalchemy import Integer, String, ARRAY, CheckConstraint, Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base


class Courier(Base):
    __tablename__ = "couriers"

    courier_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    courier_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("courier_types.id", ondelete="RESTRICT"), nullable=False)
    working_hours: Mapped[list[str]] = mapped_column(ARRAY(String(11)), nullable=False)

    courier_type_ref = relationship("CourierTypeTable", back_populates="couriers")
    regions = relationship("CourierRegion", back_populates="courier", cascade="all, delete")
    orders = relationship("Order", back_populates="courier")

    __table_args__ = (
        CheckConstraint("courier_id > 0", name="check_courier_id_positive"),
    )


class CourierRegion(Base):
    __tablename__ = "courier_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(Integer, ForeignKey("couriers.courier_id", ondelete="CASCADE"), nullable=False)
    region: Mapped[int] = mapped_column(Integer, nullable=False)

    courier = relationship("Courier", back_populates="regions")

    __table_args__ = (
        CheckConstraint("region > 0", name="check_region_positive"),
        UniqueConstraint("courier_id", "region", name="unique_courier_region"),  # ← добавить
        Index("idx_courier_regions_search", "courier_id", "region"),
    )