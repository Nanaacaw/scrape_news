#!/usr/bin/env sh
set -eu

python /app/docker/wait_for_db.py
python -c "from src.database.connection import init_database; init_database()"

exec uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"

