import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from consumer import start_consumer_task, stop_consumer_task
from database import get_db
from models import Alert, ProductStats

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_consumer_task()
    yield
    await stop_consumer_task()


app = FastAPI(title="Analytics Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stats/{product_id}")
async def get_stats(product_id: str, db: AsyncSession = Depends(get_db)):
    stats = await db.get(ProductStats, product_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="No stats yet for this product")
    return {
        "product_id": stats.product_id,
        "total": stats.total,
        "positive": stats.positive,
        "negative": stats.negative,
        "neutral": stats.neutral,
        "avg_score": round(stats.avg_score, 3),
        "negative_ratio": round(stats.negative / stats.total, 3) if stats.total else 0.0,
        "updated_at": stats.updated_at,
    }


@app.get("/stats")
async def list_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductStats))
    return [
        {
            "product_id": s.product_id,
            "total": s.total,
            "positive": s.positive,
            "negative": s.negative,
            "neutral": s.neutral,
            "avg_score": round(s.avg_score, 3),
        }
        for s in result.scalars().all()
    ]


@app.get("/alerts")
async def list_alerts(product_id: str | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Alert).order_by(Alert.created_at.desc()).limit(50)
    if product_id:
        stmt = stmt.where(Alert.product_id == product_id)
    result = await db.execute(stmt)
    return result.scalars().all()
