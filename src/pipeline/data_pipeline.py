"""
Data pipeline for processing scraped articles
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import datetime

from src.database.models import Article
from src.sentiment.analyzer import SentimentAnalyzer
from src.utils.logger import get_logger
from src.utils.helpers import extract_stock_tickers

logger = get_logger(__name__)

class DataPipeline:
    """
    Data processing pipeline:
    1. Save scraped articles to database
    2. Extract stock tickers
    3. Perform sentiment analysis
    """
    
    def __init__(self):
        self.sentiment_analyzer = None
    
    def _get_sentiment_analyzer(self) -> SentimentAnalyzer:
        if self.sentiment_analyzer is None:
            logger.info("Initializing sentiment analyzer...")
            self.sentiment_analyzer = SentimentAnalyzer()
        return self.sentiment_analyzer
    
    def process_articles(self, db: Session, articles_data: List[Dict]) -> int:
        """
        Args:
            db: Database session
            articles_data: List of article dictionaries from scraper
            
        Returns:
            Number of new articles processed
        """
        if not articles_data:
            logger.warning("No articles to process")
            return 0
        
        logger.info(f"Processing {len(articles_data)} articles...")
        
        new_articles_count = 0
        articles_for_processing = []
        
        for article_data in articles_data:
            existing = db.query(Article).filter(Article.url == article_data['url']).first()
            
            if existing:
                logger.debug(f"Article already exists: {article_data['url']}")
                continue
            
            article_data.pop('summary', None)
            
            article = Article(**article_data)
            db.add(article)
            db.flush()
            
            articles_for_processing.append(article)
            new_articles_count += 1
        
        db.commit()
        logger.info(f"Saved {new_articles_count} new articles to database")
        
        if not articles_for_processing:
            return 0
        
        self._extract_tickers(db, articles_for_processing)
        
        self._analyze_sentiments(db, articles_for_processing)
        
        logger.info("Pipeline processing complete")
        
        return new_articles_count
    
    def _extract_tickers(self, db: Session, articles: List[Article]):
        """Extract stock tickers from articles"""
        logger.info(f"Extracting tickers from {len(articles)} articles...")
        
        for article in articles:
            text = f"{article.title} {article.content[:500]}"
            tickers = extract_stock_tickers(text)
            
            if tickers:
                article.tickers = ','.join(tickers)
                logger.debug(f"Article {article.id}: Found tickers {tickers}")
        
        db.commit()
        logger.info("Ticker extraction complete")
    
    def _analyze_sentiments(self, db: Session, articles: List[Article]):
        """Analyze sentiment for articles and update them directly"""
        logger.info(f"Analyzing sentiment for {len(articles)} articles...")
        
        analyzer = self._get_sentiment_analyzer()
        
        # Pass more context to analyzer (up to 5000 chars)
        # The analyzer now handles long texts via sliding window
        texts = [f"{article.title} {article.content[:5000]}" for article in articles]
        
        sentiment_results = analyzer.analyze_batch(texts)
        
        for article, result in zip(articles, sentiment_results):
            article.sentiment_score = result['sentiment_score']
            article.sentiment_label = result['sentiment_label']
            article.confidence = result['confidence']
            article.analyzed_date = datetime.now()
        
        db.commit()
        logger.info("Sentiment analysis complete")

