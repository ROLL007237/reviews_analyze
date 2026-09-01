import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    product_id: str = Field(..., max_length=128)
    author: str = Field(..., max_length=128)
    text: str = Field(..., min_length=1)


class ReviewOut(BaseModel):
    id: uuid.UUID
    product_id: str
    author: str
    text: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
