import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.consumer import start_consumer_task, stop_consumer_task
from app.database import get_db
from app.models import ReviewAnalysis

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_consumer_task()
    yield
    await stop_consumer_task()


app = FastAPI(title="AI Processing Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/analysis/{review_id}")
async def get_analysis(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(ReviewAnalysis).where(ReviewAnalysis.review_id == review_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found (may still be processing)")
    return {
        "review_id": analysis.review_id,
        "product_id": analysis.product_id,
        "sentiment": analysis.sentiment,
        "score": analysis.score,
        "summary": analysis.summary,
        "topics": analysis.topics,
        "created_at": analysis.created_at,
    }
