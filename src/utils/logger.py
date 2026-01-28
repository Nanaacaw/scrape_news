"""
Centralized logging configuration
"""
import sys
from loguru import logger
from src.utils.config import LOG_LEVEL, LOG_FULL_PATH

# Remove default handler
logger.remove()

# Add console handler with color
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True
)

# Add file handler with rotation
logger.add(
    LOG_FULL_PATH,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=LOG_LEVEL,
    rotation="10 MB",
    retention="30 days",
    compression="zip"
)

def get_logger(name: str):
    """Get a logger instance with the specified name"""
    return logger.bind(name=name)
