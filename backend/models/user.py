from sqlalchemy import Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="courier")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)