#!/usr/bin/env sh
set -eu

python /app/docker/wait_for_db.py
python -c "from src.database.connection import init_database; init_database()"

exec python -m src.scraper.scheduler

