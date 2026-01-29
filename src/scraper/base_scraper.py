import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import re

from src.utils.config import REQUEST_TIMEOUT, USER_AGENT
from src.utils.logger import get_logger
from src.utils.helpers import clean_text, parse_indonesian_date

logger = get_logger(__name__)


class BaseScraper:
    """Base class for news scrapers with shared functionality"""
    
    def __init__(self, base_url: str):
        """Initialize scraper with common session setup"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self.base_url = base_url
    
    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute"""
        if url.startswith('/'):
            return self.base_url + url
        return url
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title using common selectors"""
        selectors = [
            ('h1', {'class': re.compile(r'(title|headline|judul)', re.I)}),
            ('h1', {}),
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'twitter:title'}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content using common selectors"""
        selectors = [
            ('div', {'class': re.compile(r'(article.*content|content.*article|detail.*content|body)', re.I)}),
            ('article', {}),
            ('div', {'itemprop': 'articleBody'}),
            ('div', {'id': re.compile(r'(article|content)', re.I)}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                for script in element(['script', 'style', 'aside', 'nav', 'footer', 'header']):
                    script.decompose()
                    
                paragraphs = element.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                if len(content) > 100:
                    return content
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author using common selectors"""
        selectors = [
            ('span', {'class': re.compile(r'(author|penulis|reporter)', re.I)}),
            ('a', {'rel': 'author'}),
            ('meta', {'name': 'author'}),
            ('div', {'class': re.compile(r'author', re.I)}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '').strip()
                text = element.get_text(strip=True)
                text = re.sub(r'^(Oleh|By|Penulis|Reporter):\s*', '', text, flags=re.I)
                return text
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract article published date using common selectors"""
        selectors = [
            ('time', {'datetime': True}),
            ('span', {'class': re.compile(r'(date|time|publish|tanggal)', re.I)}),
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publishdate'}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'time':
                    date_str = element.get('datetime', '')
                    try:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                elif tag == 'meta':
                    date_str = element.get('content', '')
                    try:
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        pass
                else:
                    date_str = element.get_text(strip=True)
                    parsed_date = parse_indonesian_date(date_str)
                    if parsed_date:
                        return parsed_date
        
        return None
    
    def _rate_limit(self, seconds: int = 1):
        """Apply rate limiting between requests"""
        time.sleep(seconds)
