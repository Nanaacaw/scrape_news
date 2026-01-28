"""
Helper utilities
"""
from datetime import datetime, timedelta
import re
from typing import Optional, List

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep Indonesian letters
    text = re.sub(r'[^\w\s\-.,!?()]', '', text)
    return text.strip()

def extract_stock_tickers(text: str) -> List[str]:
    """
    Extract stock tickers from text (e.g., BBCA, TLKM, GOTO)
    Assumes tickers are 4-letter uppercase words
    """
    # Look for 4-letter uppercase words that might be stock tickers
    tickers = re.findall(r'\b[A-Z]{4}\b', text)
    return list(set(tickers))

def parse_indonesian_date(date_str: str) -> Optional[datetime]:
    """
    Parse Indonesian date strings to datetime
    Examples: "28 Januari 2026", "Selasa, 28 Jan 2026 15:30"
    """
    month_map = {
        'januari': 1, 'jan': 1,
        'februari': 2, 'feb': 2,
        'maret': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'mei': 5,
        'juni': 6, 'jun': 6,
        'juli': 7, 'jul': 7,
        'agustus': 8, 'agu': 8, 'agt': 8,
        'september': 9, 'sep': 9,
        'oktober': 10, 'okt': 10,
        'november': 11, 'nov': 11,
        'desember': 12, 'des': 12
    }
    
    try:
        # Remove day name if present
        date_str = re.sub(r'^[A-Za-z]+,\s*', '', date_str)
        
        # Extract day, month, year
        pattern = r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})'
        match = re.search(pattern, date_str, re.IGNORECASE)
        
        if match:
            day = int(match.group(1))
            month_str = match.group(2).lower()
            year = int(match.group(3))
            month = month_map.get(month_str)
            
            if month:
                return datetime(year, month, day)
    except Exception:
        pass
    
    return None

def calculate_time_range(days: int) -> tuple:
    """Calculate start and end datetime for a time range"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length while preserving words"""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length].rsplit(' ', 1)[0]
    return truncated + '...'
