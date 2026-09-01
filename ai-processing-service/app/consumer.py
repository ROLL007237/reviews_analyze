import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import ReviewAnalysis
from app.ollama_client import analyze_review

logger = logging.getLogger(__name__)

_consumer_task: asyncio.Task | None = None


async def _process_message(payload: dict, producer: AIOKafkaProducer) -> None:
    review_id = payload["review_id"]
    product_id = payload["product_id"]
    text = payload["text"]

    result = await analyze_review(text)

    async with AsyncSessionLocal() as session:
        stmt = (
            insert(ReviewAnalysis)
            .values(
                review_id=review_id,
                product_id=product_id,
                sentiment=result["sentiment"],
                score=result["score"],
                summary=result["summary"],
                topics=result["topics"],
            )
            .on_conflict_do_update(
                index_elements=[ReviewAnalysis.review_id],
                set_={
                    "sentiment": result["sentiment"],
                    "score": result["score"],
                    "summary": result["summary"],
                    "topics": result["topics"],
                },
            )
        )
        await session.execute(stmt)
        await session.commit()

    event = {
        "review_id": review_id,
        "product_id": product_id,
        **result,
    }
    await producer.send_and_wait(
        settings.PROCESSED_REVIEWS_TOPIC, value=event, key=review_id.encode("utf-8")
    )
    logger.info("Processed review %s -> sentiment=%s", review_id, result["sentiment"])


async def _run_consumer_loop() -> None:
    consumer = AIOKafkaConsumer(
        settings.RAW_REVIEWS_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    await consumer.start()
    await producer.start()
    logger.info("AI processing consumer started, listening on %s", settings.RAW_REVIEWS_TOPIC)

    try:
        async for message in consumer:
            try:
                await _process_message(message.value, producer)
            except Exception:  # noqa: BLE001 - keep consuming even if one message fails
                logger.exception("Failed to process message: %s", message.value)
    finally:
        await consumer.stop()
        await producer.stop()


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
