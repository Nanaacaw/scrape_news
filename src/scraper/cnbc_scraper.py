import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import re

from src.scraper.base_scraper import BaseScraper
from src.utils.config import (
    CNBC_BASE_URL, CNBC_MARKET_URL, CNBC_INVESTMENT_URL,
    REQUEST_TIMEOUT, USER_AGENT, MAX_ARTICLES_PER_SCRAPE
)
from src.utils.logger import get_logger
from src.utils.helpers import clean_text, parse_indonesian_date

logger = get_logger(__name__)

class CNBCScraper(BaseScraper):
    """CNBC Indonesia news scraper"""
    
    def __init__(self):
        super().__init__(CNBC_BASE_URL)
        
    def scrape_category(self, category_url: str, max_articles: int = MAX_ARTICLES_PER_SCRAPE, max_pages: int = 1) -> List[Dict]:
        """
        Scrape articles from a category page with pagination support
        
        Args:
            category_url: URL of the category page
            max_articles: Maximum number of articles to scrape total
            max_pages: Maximum number of pages to scrape  
            
        Returns:
            List of article dictionaries
        """
        all_articles = []
        articles_scraped = 0
        
        for page_num in range(1, max_pages + 1):
            # CNBC pagination format: ?page=2, ?page=3, etc.
            if page_num == 1:
                page_url = category_url
            else:
                separator = '&' if '?' in category_url else '?'
                page_url = f"{category_url}{separator}page={page_num}"
            
            try:
                logger.info(f"Scraping page {page_num}/{max_pages}: {page_url}")
                response = self.session.get(page_url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                article_links = self._extract_article_links(soup)
                
                if not article_links:
                    logger.info(f"No more articles found on page {page_num}, stopping pagination")
                    break
                
                logger.info(f"Found {len(article_links)} article links on page {page_num}")
                
                remaining = max_articles - articles_scraped
                links_to_scrape = article_links[:min(len(article_links), remaining)]
                
                for i, article_url in enumerate(links_to_scrape):
                    try:
                        logger.info(f"Scraping article {articles_scraped+1}/{max_articles}: {article_url}")
                        article_data = self.scrape_article(article_url)
                        
                        if article_data:
                            all_articles.append(article_data)
                            articles_scraped += 1
                            
                            if articles_scraped >= max_articles:
                                logger.info(f"Reached maximum articles limit ({max_articles})")
                                return all_articles
                            
                            time.sleep(1)
                            
                    except Exception as e:
                        logger.error(f"Failed to scrape article {article_url}: {e}")
                        continue
                
                if page_num < max_pages:
                    time.sleep(2)
                        
            except Exception as e:
                logger.error(f"Failed to scrape page {page_url}: {e}")
                break
                
        logger.info(f"Total articles scraped: {len(all_articles)} from {page_num} page(s)")
        return all_articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article URLs from category page"""
        links = []
        
        for article in soup.find_all('article'):
            link_tag = article.find('a', href=True)
            if link_tag:
                url = link_tag['href']
                if url.startswith('/'):
                    url = self.base_url + url
                if url not in links and self.base_url in url:
                    links.append(url)
        
        for div in soup.find_all('div', class_=re.compile(r'(article|post|news|list).*item', re.I)):
            link_tag = div.find('a', href=True)
            if link_tag:
                url = link_tag['href']
                if url.startswith('/'):
                    url = self.base_url + url
                if url not in links and self.base_url in url:
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
            published_date = self._extract_date(soup, article_url)
            category = self._extract_category(soup)
            
            if not title or not content:
                logger.warning(f"Missing title or content for {article_url}")
                return None
            
            article_data = {
                'url': article_url,
                'source': 'cnbc',
                'title': clean_text(title),
                'content': clean_text(content),
                'summary': clean_text(content[:500]) if content else None,
                'author': clean_text(author) if author else None,
                'category': category,
                'published_date': published_date if published_date else datetime.now(),
                'scraped_date': datetime.now()
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"Failed to scrape article {article_url}: {e}")
            return None
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article category"""
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
        
        return None
    
    def scrape_market_news(self, max_articles: int = MAX_ARTICLES_PER_SCRAPE, max_pages: int = 1) -> List[Dict]:
        """Scrape market news from CNBC Indonesia"""
        return self.scrape_category(CNBC_MARKET_URL, max_articles, max_pages)
    
    def scrape_investment_news(self, max_articles: int = MAX_ARTICLES_PER_SCRAPE, max_pages: int = 1) -> List[Dict]:
        """Scrape investment news from CNBC Indonesia"""
        return self.scrape_category(CNBC_INVESTMENT_URL, max_articles, max_pages)
    
    def scrape_all(self, max_articles_per_category: int = MAX_ARTICLES_PER_SCRAPE, max_pages: int = 1) -> List[Dict]:
        """Scrape market news only (excluding mymoney and investment)"""
        logger.info(f"Scraping Market news (up to {max_pages} page(s))...")
        articles = self.scrape_category(CNBC_MARKET_URL, max_articles_per_category, max_pages)
        logger.info(f"Scraped {len(articles)} articles from Market section")
        
        return articles
