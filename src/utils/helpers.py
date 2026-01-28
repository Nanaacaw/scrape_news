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
    Extract stock tickers from text (Indonesian stock market: BEI/IDX)
    Tickers are typically 4-letter uppercase codes
    
    Returns:
        List of unique ticker symbols found in text
    """
    if not text:
        return []
    
    # Common Indonesian stock tickers (partial list for better accuracy)
    # This helps reduce false positives
    known_tickers = {
        # Banking
        'BBRI', 'BBCA', 'BMRI', 'BBNI', 'BBTN', 'BNGA', 'NISP', 'BNLI', 'MEGA', 'BRIS',
        # Telecom
        'TLKM', 'EXCL', 'ISAT', 'FREN',
        # Energy
        'PGAS', 'MEDC', 'ELSA', 'AKRA', 'ADRO', 'PTBA', 'ITMG', 'HRUM',
        # Consumer
        'UNVR', 'INDF', 'ICBP', 'MYOR', 'KLBF', 'SIDO', 'KAEF', 'GGRM', 'HMSP',
        # Tech & Media
        'GOTO', 'BUKA', 'EMTK', 'MNCN',
        # Property
        'BSDE', 'CTRA', 'PWON', 'ASRI', 'LPKR', 'SMRA',
        # Automotive
        'ASII', 'AUTO', 'IMAS', 'SMSM',
        # Retail
        'ACES', 'ERAA', 'LPPF', 'MAPI', 'RALS',
        # Construction
        'WIKA', 'WSKT', 'PTPP', 'ADHI', 'TOTL',
        # Mining
        'ANTM', 'INCO', 'TINS', 'MDKA',
        # Conglomerate
        'AALI', 'JSMR', 'UNTR', 'BUMI',
    }
    
    # Find all 4-letter uppercase words
    pattern = r'\b[A-Z]{4}\b'
    potential_tickers = re.findall(pattern, text)
    
    # Filter to only known tickers to reduce false positives
    # (e.g., "YANG", "AKAN", "DARI" are common Indonesian words)
    tickers = [t for t in potential_tickers if t in known_tickers]
    
    return list(set(tickers))  # Return unique tickers

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
