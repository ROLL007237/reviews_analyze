from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ingestion_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    RAW_REVIEWS_TOPIC: str = "raw-reviews"


settings = Settings()
