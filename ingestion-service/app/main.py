import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.kafka_producer import publish_raw_review, start_producer, stop_producer
from app.models import Review
from app.schemas import ReviewCreate, ReviewOut

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_producer()
    yield
    await stop_producer()


app = FastAPI(title="Ingestion Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/reviews", response_model=ReviewOut, status_code=201)
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_db)):
    review = Review(product_id=payload.product_id, author=payload.author, text=payload.text)
    db.add(review)
    await db.commit()
    await db.refresh(review)

    await publish_raw_review(
        {
            "review_id": str(review.id),
            "product_id": review.product_id,
            "author": review.author,
            "text": review.text,
        }
    )

    return review


@app.get("/reviews/{review_id}", response_model=ReviewOut)
async def get_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@app.get("/reviews", response_model=list[ReviewOut])
async def list_reviews(product_id: str | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Review).order_by(Review.created_at.desc())
    if product_id:
        stmt = stmt.where(Review.product_id == product_id)
    result = await db.execute(stmt)
    return result.scalars().all()
