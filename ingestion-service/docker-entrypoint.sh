#!/bin/sh

set -e

echo "Waiting for database..."

until python -c "
import asyncio
import os
import asyncpg

async def check():
    url = os.environ['DATABASE_URL']
    url = url.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    await conn.close()

asyncio.run(check())
" 2>/dev/null
do
    echo "Database is not ready yet..."
    sleep 2
done

echo "Database is ready."

echo "Running Alembic migrations..."

alembic upgrade head

echo "Migrations completed."

echo "Starting application..."

exec "$@"
