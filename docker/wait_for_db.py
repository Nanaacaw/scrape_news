import os
import time

from sqlalchemy import create_engine, text


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return f"postgresql://{database_url.removeprefix('postgres://')}"
    return database_url


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    database_url = _normalize_database_url(database_url)

    retries = int(os.getenv("DB_WAIT_RETRIES", "30"))
    delay_seconds = float(os.getenv("DB_WAIT_DELAY_SECONDS", "1"))

    engine = create_engine(database_url, pool_pre_ping=True)

    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database is ready")
            return
        except Exception as exc:
            print(f"Waiting for database ({attempt}/{retries}): {exc}")
            time.sleep(delay_seconds)

    raise SystemExit("Database not ready after waiting")


if __name__ == "__main__":
    main()

