import enum
from sqlalchemy import Integer, String, ARRAY, CheckConstraint, Index
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base

class CourierType(enum.Enum):
    foot = "foot"
    bike = "bike"
    car  = "car"

class Courier(Base):
    __tablename__ = "couriers"

    courier_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    courier_type: Mapped[CourierType] = mapped_column(
        SAEnum(CourierType, name="courier_enum"), nullable=False
    )
    working_hours: Mapped[list[str]] = mapped_column(ARRAY(String(11)), nullable=False)

    regions  = relationship("CourierRegion", back_populates="courier", cascade="all, delete")
    orders   = relationship("Order", back_populates="courier")

    __table_args__ = (
        CheckConstraint("courier_id > 0", name="check_courier_id_positive"),
    )

class CourierRegion(Base):
    __tablename__ = "courier_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    region: Mapped[int] = mapped_column(Integer, nullable=False)

    courier = relationship("Courier", back_populates="regions")

    __table_args__ = (
        CheckConstraint("region > 0", name="check_region_positive"),
        Index("idx_courier_regions_search", "courier_id", "region"),
    )