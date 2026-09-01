from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_processing_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    RAW_REVIEWS_TOPIC: str = "raw-reviews"
    PROCESSED_REVIEWS_TOPIC: str = "processed-reviews"
    CONSUMER_GROUP: str = "ai-processing-service"
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"


settings = Settings()
