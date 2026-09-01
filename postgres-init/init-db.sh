#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE ingestion_db;
    CREATE DATABASE ai_processing_db;
    CREATE DATABASE analytics_db;
EOSQL
