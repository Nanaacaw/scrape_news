import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import re

from src.scraper.base_scraper import BaseScraper
from src.utils.config import (
    BLOOMBERG_BASE_URL, BLOOMBERG_MARKET_URL,
    REQUEST_TIMEOUT, USER_AGENT, MAX_ARTICLES_PER_SCRAPE
)
from src.utils.logger import get_logger
from src.utils.helpers import clean_text, parse_indonesian_date

logger = get_logger(__name__)

class BloombergScraper(BaseScraper):
    """Bloomberg Technoz news scraper"""
    
    def __init__(self):
        super().__init__(BLOOMBERG_BASE_URL)
        
    def scrape_category(self, category_url: str, max_articles: int = MAX_ARTICLES_PER_SCRAPE, max_pages: int = 1) -> List[Dict]:
        """
        Args:
            category_url: URL of the category page
            max_articles: Maximum number of articles to scrape total
            max_pages: Not used for Bloomberg (kept for API consistency)
            
        Returns:
            List of article dictionaries
        """
        all_articles = []
        articles_scraped = 0
        
        try:
            logger.info(f"Scraping Bloomberg: {category_url}")
            response = self.session.get(category_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            article_links = self._extract_article_links(soup)
            
            if not article_links:
                logger.warning(f"No article links found on Bloomberg page")
                return []
            
            logger.info(f"Found {len(article_links)} article links on Bloomberg")
            
            links_to_scrape = article_links[:max_articles]
            
            for i, article_url in enumerate(links_to_scrape):
                try:
                    logger.info(f"Scraping article {i+1}/{len(links_to_scrape)}: {article_url}")
                    article_data = self.scrape_article(article_url)
                    
                    if article_data:
                        all_articles.append(article_data)
                        articles_scraped += 1
                        self._rate_limit(1)
                        
                except Exception as e:
                    logger.error(f"Failed to scrape article {article_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scrape Bloomberg page {category_url}: {e}")
            
        logger.info(f"Total articles scraped from Bloomberg: {len(all_articles)}")
        return all_articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article URLs from Bloomberg index page"""
        links = []
        
        for link_tag in soup.find_all('a', href=True):
            url = self._make_absolute_url(link_tag['href'])
            
            if self.base_url in url and url not in links:
                if not any(x in url for x in ['/indeks/', '/kanal/', '/foto', '/video', '/infografis', '/z-zone']):
                    if '/detail-news/' in url or '/market/' in url:
                        path = url.replace(self.base_url, '')
                        if len(path.split('/')) >= 3:
                            links.append(url)
        
        return links
    
    def scrape_article(self, article_url: str) -> Optional[Dict]:
        """
        Scrape a single article
        
        Returns:
            Dictionary with article data or None if failed
        """
        try:
            response = self.session.get(article_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            author = self._extract_author(soup)
            published_date = self._extract_date(soup)
            category = self._extract_category(soup, article_url)
            
            if not title or not content:
                logger.warning(f"Missing title or content for {article_url}")
                return None
            
            article_data = {
                'url': article_url,
                'source': 'bloomberg',
                'title': clean_text(title),
                'content': clean_text(content),
                'author': clean_text(author) if author else None,
                'category': category,
                'published_date': published_date,
                'scraped_date': datetime.now()
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"Failed to scrape Bloomberg article {article_url}: {e}")
            return None

    def _extract_category(self, soup: BeautifulSoup, article_url: str) -> Optional[str]:
        selectors = [
            ('meta', {'property': 'article:section'}),
            ('span', {'class': re.compile(r'categor', re.I)}),
            ('a', {'class': re.compile(r'categor', re.I)}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        try:
            path_parts = article_url.replace(self.base_url, '').strip('/').split('/')
            if path_parts:
                return path_parts[0].title()
        except:
            pass
        
        return None
    
    def scrape_market_news(self, max_articles: int = MAX_ARTICLES_PER_SCRAPE, max_pages: int = 1) -> List[Dict]:
        """Scrape market news from Bloomberg Technoz"""
        return self.scrape_category(BLOOMBERG_MARKET_URL, max_articles, max_pages)
    
    def scrape_all(self, max_articles_per_category: int = MAX_ARTICLES_PER_SCRAPE, max_pages: int = 1) -> List[Dict]:
        """Scrape market news from Bloomberg Technoz"""
        logger.info(f"Scraping Bloomberg Market news...")
        articles = self.scrape_category(BLOOMBERG_MARKET_URL, max_articles_per_category, max_pages)
        logger.info(f"Scraped {len(articles)} articles from Bloomberg Market section")
        
        return articles
