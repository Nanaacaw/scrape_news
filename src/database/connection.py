from contextlib import contextmanager
import os

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.models import Base
from src.utils.config import DATABASE_FULL_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

engine: Engine | None = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return f"postgresql://{database_url.removeprefix('postgres://')}"
    return database_url


def init_engine() -> Engine:
    global engine
    if engine is not None:
        return engine

    database_url = os.getenv("DATABASE_URL") or f"sqlite:///{DATABASE_FULL_PATH}"
    database_url = _normalize_database_url(database_url)

    if not database_url.startswith(("postgresql", "sqlite")):
        raise RuntimeError("Unsupported DATABASE_URL scheme (use postgresql:// or sqlite://)")

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    SessionLocal.configure(bind=engine)
    return engine

def init_database():
    try:
        engine = init_engine()
        Base.metadata.create_all(bind=engine)
        logger.info(
            "Database initialized ({})",
            engine.url.render_as_string(hide_password=True),
        )
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@contextmanager
def get_db() -> Session:
    """
    Usage:
        with get_db() as db:
            # perform database operations
            db.query(Article).all()
    """
    init_engine()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    init_engine()
    return SessionLocal()
