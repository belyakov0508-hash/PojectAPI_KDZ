from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base


class CourierTypeTable(Base):
    __tablename__ = "courier_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    couriers = relationship("Courier", back_populates="courier_type_ref")