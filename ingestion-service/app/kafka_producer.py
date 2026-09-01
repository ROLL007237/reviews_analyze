import json
import logging

from aiokafka import AIOKafkaProducer

from app.config import settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await _producer.start()
    logger.info("Kafka producer started")


async def stop_producer() -> None:
    if _producer is not None:
        await _producer.stop()
        logger.info("Kafka producer stopped")


async def publish_raw_review(event: dict) -> None:
    if _producer is None:
        raise RuntimeError("Kafka producer is not started")
    await _producer.send_and_wait(settings.RAW_REVIEWS_TOPIC, value=event, key=event["review_id"].encode("utf-8"))
