"""
Configuration management for CNBC News Scraper
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
BASE_DIR = Path(__file__).parent.parent.parent

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/cnbc_news.db')
DATABASE_FULL_PATH = BASE_DIR / DATABASE_PATH

# Scraping Configuration
SCRAPE_INTERVAL_HOURS = int(os.getenv('SCRAPE_INTERVAL_HOURS', '1'))
MAX_ARTICLES_PER_SCRAPE = int(os.getenv('MAX_ARTICLES_PER_SCRAPE', '50'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
USER_AGENT = os.getenv(
    'USER_AGENT',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
)

# CNBC Indonesia URLs
CNBC_BASE_URL = os.getenv('CNBC_BASE_URL', 'https://www.cnbcindonesia.com')
CNBC_MARKET_URL = os.getenv('CNBC_MARKET_URL', f'{CNBC_BASE_URL}/market')
CNBC_INVESTMENT_URL = os.getenv('CNBC_INVESTMENT_URL', f'{CNBC_BASE_URL}/investment')

# Sentiment Analysis Configuration
SENTIMENT_MODEL = os.getenv('SENTIMENT_MODEL', 'indobenchmark/indobert-base-p1')
SENTIMENT_BATCH_SIZE = int(os.getenv('SENTIMENT_BATCH_SIZE', '8'))
SENTIMENT_MAX_LENGTH = int(os.getenv('SENTIMENT_MAX_LENGTH', '512'))

# Screening Criteria
MIN_SENTIMENT_SCORE = float(os.getenv('MIN_SENTIMENT_SCORE', '0.3'))
MIN_ARTICLES_FOR_SIGNAL = int(os.getenv('MIN_ARTICLES_FOR_SIGNAL', '3'))
SIGNAL_TIMEFRAME_DAYS = int(os.getenv('SIGNAL_TIMEFRAME_DAYS', '7'))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/scraper.log')
LOG_FULL_PATH = BASE_DIR / LOG_FILE

# Create necessary directories
(BASE_DIR / 'data').mkdir(exist_ok=True)
(BASE_DIR / 'logs').mkdir(exist_ok=True)
(BASE_DIR / 'models').mkdir(exist_ok=True)
