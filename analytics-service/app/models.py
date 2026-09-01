import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProductStats(Base):
    __tablename__ = "product_stats"

    product_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    positive: Mapped[int] = mapped_column(Integer, default=0)
    negative: Mapped[int] = mapped_column(Integer, default=0)
    neutral: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[str] = mapped_column(String(128), index=True)
    message: Mapped[str] = mapped_column(Text)
    negative_ratio: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
