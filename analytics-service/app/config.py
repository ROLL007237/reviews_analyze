from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/analytics_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    PROCESSED_REVIEWS_TOPIC: str = "processed-reviews"
    CONSUMER_GROUP: str = "analytics-service"
    # if the share of negative reviews in the last N reviews (see WINDOW) exceeds this, raise an alert
    NEGATIVE_ALERT_THRESHOLD: float = 0.5
    ALERT_WINDOW: int = 10


settings = Settings()
