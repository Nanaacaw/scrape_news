import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.config import REQUEST_TIMEOUT, USER_AGENT, MAX_WORKERS
from src.utils.logger import get_logger
from src.utils.helpers import clean_text, parse_indonesian_date

logger = get_logger(__name__)


class BaseScraper:
    """Base class for news scrapers with shared functionality"""
    
    def __init__(self, base_url: str):
        """Initialize scraper with common session setup"""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
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
    
    def _extract_date(self, soup: BeautifulSoup, url: Optional[str] = None) -> Optional[datetime]:
        """Extract article published date using comprehensive selectors"""
        
        # Try extracting from URL if provided (High priority for CNBC/Bloomberg where URL contains timestamp)
        if url:
            # CNBC Indonesia format: .../20260130092013-... (YYYYMMDDHHMMSS)
            cnbc_match = re.search(r'/(\d{14})-', url)
            if cnbc_match:
                try:
                    return datetime.strptime(cnbc_match.group(1), "%Y%m%d%H%M%S")
                except ValueError:
                    pass

        # Try extracting from JSON-LD (Standard for many news sites including Bloomberg)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                content = script.get_text(strip=True)
                if not content:
                    continue
                    
                data = json.loads(content)
                
                # Helper to check a dict for date
                def get_date_from_dict(d):
                    if not isinstance(d, dict): return None
                    date_str = d.get('datePublished') or d.get('dateCreated')
                    if date_str:
                        try:
                            # Handle timezone offsets if present, keep it naive for consistency or strip it
                            # The existing logic strips timezone info
                            if '+' in date_str:
                                date_str = date_str.split('+')[0]
                            elif 'Z' in date_str:
                                date_str = date_str.replace('Z', '')
                            return datetime.fromisoformat(date_str)
                        except:
                            pass
                    return None

                if isinstance(data, list):
                    for item in data:
                        res = get_date_from_dict(item)
                        if res: return res
                else:
                    res = get_date_from_dict(data)
                    if res: return res
            except:
                continue

        selectors = [
            ('time', {'datetime': True}),
            ('time', {}),
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publishdate'}),
            ('meta', {'name': 'publish-date'}),
            ('meta', {'property': 'og:published_time'}),
            ('span', {'class': re.compile(r'(date|time|publish|tanggal|waktu)', re.I)}),
            ('div', {'class': re.compile(r'(date|time|publish|tanggal)', re.I)}),
            ('p', {'class': re.compile(r'(date|time|publish)', re.I)}),
        ]
        
        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs) if tag in ['span', 'div', 'p'] else [soup.find(tag, attrs)]
            
            for element in elements:
                if not element:
                    continue
                    
                try:
                    if tag == 'time':
                        date_str = element.get('datetime', element.get_text(strip=True))
                        if date_str:
                            try:
                                return datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0].split('.')[0])
                            except:
                                parsed = parse_indonesian_date(date_str)
                                if parsed:
                                    return parsed
                    
                    elif tag == 'meta':
                        date_str = element.get('content', '')
                        if date_str:
                            try:
                                return datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0].split('.')[0])
                            except:
                                pass
                    else:
                        date_str = element.get_text(strip=True)
                        if date_str and len(date_str) > 5:
                            parsed_date = parse_indonesian_date(date_str)
                            if parsed_date:
                                return parsed_date
                except:
                    continue
        
        logger.warning("Failed to extract published_date, will use scraped_date")
        return None
    
    def _rate_limit(self, seconds: int = 1):
        """Apply rate limiting between requests"""
        time.sleep(seconds)

    def scrape_articles_concurrently(self, urls: List[str], scrape_func) -> List[Dict]:
        """
        Scrape multiple articles concurrently using ThreadPoolExecutor
        
        Args:
            urls: List of article URLs
            scrape_func: Function to call for each URL (e.g. self.scrape_article)
            
        Returns:
            List of scraped article dictionaries
        """
        results = []
        if not urls:
            return results

        logger.info(f"Starting concurrent scraping of {len(urls)} articles with {MAX_WORKERS} workers")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Map URLs to future objects
            future_to_url = {executor.submit(scrape_func, url): url for url in urls}
            
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    if data:
                        results.append(data)
                    completed += 1
                    if completed % 5 == 0:
                        logger.info(f"Progress: {completed}/{len(urls)} articles scraped")
                except Exception as e:
                    logger.error(f"Concurrent scraping failed for {url}: {e}")
                    
        return results
