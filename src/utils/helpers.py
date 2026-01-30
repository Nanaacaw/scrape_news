from datetime import datetime, timedelta
import re
from typing import Optional, List, Dict, Set
import os
from pathlib import Path
import pandas as pd

def clean_text(text: str) -> str:
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    # Preserve alphanumeric, basic punctuation, currency symbols, and percentage
    text = re.sub(r'[^\w\s\-.,!?()%$€£]', '', text)
    return text.strip()

_STOCK_TICKERS_CACHE: Optional[Dict[str, str]] = None

def load_idx_stocks() -> Dict[str, str]:
    global _STOCK_TICKERS_CACHE
    
    if _STOCK_TICKERS_CACHE is not None:
        return _STOCK_TICKERS_CACHE
    
    base_dir = Path(__file__).parent.parent.parent
    csv_path = base_dir / 'data' / 'idx_stonks.csv'
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Stock data file not found: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        
        _STOCK_TICKERS_CACHE = {}
        for _, row in df.iterrows():
            ticker = str(row['code']).strip().upper()
            company_name = str(row['name']).strip() if 'name' in row and pd.notna(row['name']) else None
            _STOCK_TICKERS_CACHE[ticker] = company_name
        
        return _STOCK_TICKERS_CACHE
        
    except Exception as e:
        raise RuntimeError(f"Failed to load stock data from CSV: {e}")

def extract_stock_tickers(text: str) -> List[str]:
    """
    Extract stock tickers from text (Indonesian stock market: BEI/IDX)
    Uses the complete list of 952 Indonesian stocks from idx_stonks.csv
    
    Returns:
        List of unique ticker symbols found in text
    """
    if not text:
        return []
    
    try:
        valid_tickers = set(load_idx_stocks().keys())
    except Exception as e:
        print(f"Warning: Could not load stock tickers: {e}")
        return []
    
    pattern = r'\b[A-Z]{4}\b'
    potential_tickers = re.findall(pattern, text)
    
    tickers = [t for t in potential_tickers if t in valid_tickers]
    
    return list(set(tickers))

def get_stock_name(ticker: str) -> Optional[str]:
    """
    Get company name for a stock ticker
    
    Args:
        ticker: Stock ticker code (e.g., 'BBRI')
        
    Returns:
        Company name or None if not found
    """
    try:
        stocks = load_idx_stocks()
        return stocks.get(ticker.upper())
    except Exception:
        return None

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
        date_str = re.sub(r'^[A-Za-z]+,\s*', '', date_str)
        
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
