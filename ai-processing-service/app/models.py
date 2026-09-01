import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReviewAnalysis(Base):
    __tablename__ = "review_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    product_id: Mapped[str] = mapped_column(String(128), index=True)
    sentiment: Mapped[str] = mapped_column(String(16))  # positive | negative | neutral
    score: Mapped[float] = mapped_column(Float)  # -1.0 .. 1.0
    summary: Mapped[str] = mapped_column(Text)
    topics: Mapped[str] = mapped_column(Text)  # comma-separated
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
