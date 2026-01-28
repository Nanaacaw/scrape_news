"""
CNBC Indonesia Web Scraper
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import re

from src.utils.config import (
    CNBC_BASE_URL, CNBC_MARKET_URL, CNBC_INVESTMENT_URL,
    REQUEST_TIMEOUT, USER_AGENT, MAX_ARTICLES_PER_SCRAPE
)
from src.utils.logger import get_logger
from src.utils.helpers import clean_text, parse_indonesian_date

logger = get_logger(__name__)

class CNBCScraper:
    """CNBC Indonesia news scraper"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self.base_url = CNBC_BASE_URL
        
    def scrape_category(self, category_url: str, max_articles: int = MAX_ARTICLES_PER_SCRAPE) -> List[Dict]:
        """
        Scrape articles from a category page
        
        Args:
            category_url: URL of the category page
            max_articles: Maximum number of articles to scrape
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        try:
            logger.info(f"Scraping category: {category_url}")
            response = self.session.get(category_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            article_links = self._extract_article_links(soup)
            
            logger.info(f"Found {len(article_links)} article links")
            
            for i, article_url in enumerate(article_links[:max_articles]):
                try:
                    logger.info(f"Scraping article {i+1}/{min(len(article_links), max_articles)}: {article_url}")
                    article_data = self.scrape_article(article_url)
                    
                    if article_data:
                        articles.append(article_data)
                        # Be respectful - add delay between requests
                        time.sleep(1)
                        
                except Exception as e:
                    logger.error(f"Failed to scrape article {article_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scrape category {category_url}: {e}")
            
        return articles
    
    def _extract_article_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract article URLs from category page"""
        links = []
        
        # CNBC Indonesia typically uses <article> tags or divs with specific classes
        # This is a generic approach - may need adjustment based on actual HTML structure
        
        # Try finding links in article tags
        for article in soup.find_all('article'):
            link_tag = article.find('a', href=True)
            if link_tag:
                url = link_tag['href']
                if url.startswith('/'):
                    url = self.base_url + url
                if url not in links and self.base_url in url:
                    links.append(url)
        
        # Also try common class patterns
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
            
            # Extract article data
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            author = self._extract_author(soup)
            published_date = self._extract_date(soup)
            category = self._extract_category(soup)
            
            if not title or not content:
                logger.warning(f"Missing title or content for {article_url}")
                return None
            
            article_data = {
                'url': article_url,
                'title': clean_text(title),
                'content': clean_text(content),
                'summary': clean_text(content[:500]) if content else None,
                'author': clean_text(author) if author else None,
                'category': category,
                'published_date': published_date,
                'scraped_date': datetime.now()
            }
            
            return article_data
            
        except Exception as e:
            logger.error(f"Failed to scrape article {article_url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        # Try multiple selectors
        selectors = [
            ('h1', {'class': re.compile(r'(title|headline)', re.I)}),
            ('h1', {}),
            ('meta', {'property': 'og:title'}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article content"""
        # Try multiple selectors for article body
        selectors = [
            ('div', {'class': re.compile(r'(article.*body|content.*body|detail.*content)', re.I)}),
            ('article', {}),
            ('div', {'itemprop': 'articleBody'}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                # Remove script and style tags
                for script in element(['script', 'style', 'aside', 'nav']):
                    script.decompose()
                    
                paragraphs = element.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                if len(content) > 100:  # Ensure we have substantial content
                    return content
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author"""
        selectors = [
            ('span', {'class': re.compile(r'author', re.I)}),
            ('a', {'rel': 'author'}),
            ('meta', {'name': 'author'}),
        ]
        
        for tag, attrs in selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract article published date"""
        selectors = [
            ('time', {'datetime': True}),
            ('span', {'class': re.compile(r'(date|time|publish)', re.I)}),
            ('meta', {'property': 'article:published_time'}),
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
    
    def scrape_market_news(self, max_articles: int = MAX_ARTICLES_PER_SCRAPE) -> List[Dict]:
        """Scrape market news from CNBC Indonesia"""
        return self.scrape_category(CNBC_MARKET_URL, max_articles)
    
    def scrape_investment_news(self, max_articles: int = MAX_ARTICLES_PER_SCRAPE) -> List[Dict]:
        """Scrape investment news from CNBC Indonesia"""
        return self.scrape_category(CNBC_INVESTMENT_URL, max_articles)
    
    def scrape_all(self, max_articles_per_category: int = MAX_ARTICLES_PER_SCRAPE) -> List[Dict]:
        """Scrape all relevant categories"""
        all_articles = []
        
        categories = [
            ('Market', CNBC_MARKET_URL),
            ('Investment', CNBC_INVESTMENT_URL),
        ]
        
        for category_name, category_url in categories:
            logger.info(f"Scraping {category_name} news...")
            articles = self.scrape_category(category_url, max_articles_per_category)
            all_articles.extend(articles)
            logger.info(f"Scraped {len(articles)} articles from {category_name}")
        
        return all_articles
