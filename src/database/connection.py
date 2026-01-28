"""
Database connection and session management
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.models import Base
from src.utils.config import DATABASE_FULL_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create SQLite engine
DATABASE_URL = f"sqlite:///{DATABASE_FULL_PATH}"
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query debugging
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized at {DATABASE_FULL_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@contextmanager
def get_db() -> Session:
    """
    Get database session with context manager
    
    Usage:
        with get_db() as db:
            # perform database operations
            db.query(Article).all()
    """
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
    """Get a new database session (remember to close it)"""
    return SessionLocal()
