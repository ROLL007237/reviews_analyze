import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import Alert, ProductStats

logger = logging.getLogger(__name__)

_consumer_task: asyncio.Task | None = None


async def _process_message(payload: dict) -> None:
    product_id = payload["product_id"]
    sentiment = payload["sentiment"]
    score = float(payload.get("score", 0.0))

    async with AsyncSessionLocal() as session:
        stats = await session.get(ProductStats, product_id)
        if stats is None:
            stats = ProductStats(product_id=product_id, total=0, positive=0, negative=0, neutral=0, avg_score=0.0)
            session.add(stats)

        # running average update
        new_total = stats.total + 1
        stats.avg_score = ((stats.avg_score * stats.total) + score) / new_total
        stats.total = new_total
        if sentiment == "positive":
            stats.positive += 1
        elif sentiment == "negative":
            stats.negative += 1
        else:
            stats.neutral += 1

        negative_ratio = stats.negative / stats.total

        should_alert = (
            stats.total >= settings.ALERT_WINDOW
            and negative_ratio >= settings.NEGATIVE_ALERT_THRESHOLD
        )

        if should_alert:
            alert = Alert(
                product_id=product_id,
                message=(
                    f"Product '{product_id}' has a negative review ratio of "
                    f"{negative_ratio:.0%} over {stats.total} reviews."
                ),
                negative_ratio=negative_ratio,
            )
            session.add(alert)
            logger.warning("ALERT: %s", alert.message)

        await session.commit()

    logger.info(
        "Updated stats for product %s: total=%s positive=%s negative=%s neutral=%s avg_score=%.2f",
        product_id, stats.total, stats.positive, stats.negative, stats.neutral, stats.avg_score,
    )


async def _run_consumer_loop() -> None:
    consumer = AIOKafkaConsumer(
        settings.PROCESSED_REVIEWS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await consumer.start()
    logger.info("Analytics consumer started, listening on %s", settings.PROCESSED_REVIEWS_TOPIC)

    try:
        async for message in consumer:
            try:
                await _process_message(message.value)
            except Exception:  # noqa: BLE001 - keep consuming even if one message fails
                logger.exception("Failed to process message: %s", message.value)
    finally:
        await consumer.stop()


def start_consumer_task() -> None:
    global _consumer_task
    _consumer_task = asyncio.create_task(_run_consumer_loop())


async def stop_consumer_task() -> None:
    if _consumer_task is not None:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
