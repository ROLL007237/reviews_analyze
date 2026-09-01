# Review Analyzer — MVP

Event-driven система анализа отзывов на 3 микросервисах (FastAPI), связанных через Kafka
(Redpanda), с локальной LLM (Ollama) для анализа тональности, и миграциями Alembic
на каждый сервис (database-per-service).

## Архитектура

```
                 POST /reviews
                      │
                      ▼
        ┌─────────────────────────┐
        │   Ingestion Service      │  :8001
        │  (FastAPI + Postgres)    │
        └────────────┬─────────────┘
                      │ topic: raw-reviews
                      ▼
        ┌─────────────────────────┐
        │ AI Processing Service    │  :8002
        │ (Kafka consumer          │
        │  + Ollama + Postgres)    │
        └────────────┬─────────────┘
                      │ topic: processed-reviews
                      ▼
        ┌─────────────────────────┐
        │  Analytics Service       │  :8003
        │ (Kafka consumer          │
        │  + Postgres, alerts)     │
        └─────────────────────────┘
```

- **ingestion-service** — принимает отзыв через REST, сохраняет в свою БД (`ingestion_db`),
  публикует событие в топик `raw-reviews`.
- **ai-processing-service** — слушает `raw-reviews`, отправляет текст в Ollama, парсит
  тональность/summary/topics, пишет в свою БД (`ai_processing_db`), публикует в `processed-reviews`.
- **analytics-service** — слушает `processed-reviews`, агрегирует статистику по продуктам
  (`analytics_db`) и создаёт алерты при высокой доле негативных отзывов.

Каждый сервис — независимое FastAPI-приложение со своей БД и своими Alembic-миграциями
(паттерн database-per-service).

## Запуск

```bash
docker compose up --build
```

После первого старта нужно один раз скачать модель в контейнер Ollama:

```bash
docker exec -it review-analyzer-ollama-1 ollama pull llama3.2:1b
```

(можно взять любую другую модель — просто поменяйте `OLLAMA_MODEL` в docker-compose.yml)

Миграции применяются автоматически при старте контейнера (`alembic upgrade head` в CMD).

## Проверка работы

```bash
# 1. Создать отзыв
curl -X POST http://localhost:8001/reviews \
  -H "Content-Type: application/json" \
  -d '{"product_id": "sku-123", "author": "Ivan", "text": "Ужасное качество, сломалось на второй день!"}'

# 2. Посмотреть результат анализа (через пару секунд, после обработки Ollama)
curl http://localhost:8002/analysis/<review_id>

# 3. Посмотреть агрегированную статистику по продукту
curl http://localhost:8003/stats/sku-123

# 4. Посмотреть алерты
curl http://localhost:8003/alerts
```

## Локальная разработка без Docker

Для каждого сервиса:

```bash
cd ingestion-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Не забудьте поднять Kafka/Redpanda, Postgres и Ollama отдельно (например, только их
через `docker compose up redpanda postgres ollama`) и выставить переменные окружения
из `docker-compose.yml` (`DATABASE_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `OLLAMA_URL`, ...).

## Что можно добавить дальше (out of scope для MVP)

- Dead-letter топик для сообщений, которые не удалось обработать
- Idempotency / exactly-once обработку (сейчас at-least-once с upsert по review_id)
- Schema Registry (Avro/Protobuf) вместо "сырого" JSON в Kafka-сообщениях
- WebSocket/SSE для live-обновлений в дашборде
- Настоящий канал уведомлений (email/Slack) вместо записи алерта в БД
- OpenTelemetry-трейсинг сквозь все три сервиса
- Rate limiting и аутентификация на публичных эндпоинтах
