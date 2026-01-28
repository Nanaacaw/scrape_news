"""
Data pipeline for processing scraped articles
"""
from typing import List, Dict
from sqlalchemy.orm import Session

from src.database.models import Article, Sentiment
from src.sentiment.analyzer import SentimentAnalyzer
from src.screening.screener import StockScreener
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataPipeline:
    """
    Data processing pipeline:
    1. Save scraped articles to database
    2. Perform sentiment analysis
    3. Extract stock tickers
    4. Generate screening signals
    """
    
    def __init__(self):
        self.sentiment_analyzer = None
        self.screener = StockScreener()
    
    def _get_sentiment_analyzer(self) -> SentimentAnalyzer:
        """Lazy load sentiment analyzer"""
        if self.sentiment_analyzer is None:
            logger.info("Initializing sentiment analyzer...")
            self.sentiment_analyzer = SentimentAnalyzer()
        return self.sentiment_analyzer
    
    def process_articles(self, db: Session, articles_data: List[Dict]) -> int:
        """
        Process scraped articles through the full pipeline
        
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
        articles_for_sentiment = []
        
        # Step 1: Save articles to database (skip duplicates)
        for article_data in articles_data:
            # Check if article already exists
            existing = db.query(Article).filter(Article.url == article_data['url']).first()
            
            if existing:
                logger.debug(f"Article already exists: {article_data['url']}")
                continue
            
            # Create new article
            article = Article(**article_data)
            db.add(article)
            db.flush()  # Get article ID
            
            articles_for_sentiment.append(article)
            new_articles_count += 1
        
        db.commit()
        logger.info(f"Saved {new_articles_count} new articles to database")
        
        if not articles_for_sentiment:
            return 0
        
        # Step 2: Perform sentiment analysis
        self._analyze_sentiments(db, articles_for_sentiment)
        
        # Step 3: Extract stock tickers
        self._extract_stocks(db, articles_for_sentiment)
        
        logger.info("Pipeline processing complete")
        
        return new_articles_count
    
    def _analyze_sentiments(self, db: Session, articles: List[Article]):
        """Analyze sentiment for articles"""
        logger.info(f"Analyzing sentiment for {len(articles)} articles...")
        
        analyzer = self._get_sentiment_analyzer()
        
        # Prepare texts for batch processing
        texts = [f"{article.title} {article.content[:500]}" for article in articles]
        
        # Perform batch sentiment analysis
        sentiment_results = analyzer.analyze_batch(texts)
        
        # Save sentiment results
        for article, result in zip(articles, sentiment_results):
            sentiment = Sentiment(
                article_id=article.id,
                sentiment_score=result['sentiment_score'],
                sentiment_label=result['sentiment_label'],
                confidence=result['confidence']
            )
            db.add(sentiment)
        
        db.commit()
        logger.info("Sentiment analysis complete")
    
    def _extract_stocks(self, db: Session, articles: List[Article]):
        """Extract stock tickers from articles"""
        logger.info(f"Extracting stock tickers from {len(articles)} articles...")
        
        for article in articles:
            self.screener.extract_and_save_stocks(db, article)
        
        logger.info("Stock extraction complete")
    
    def update_screening_signals(self, db: Session):
        """Update screening signals based on latest data"""
        logger.info("Updating screening signals...")
        signals = self.screener.generate_signals(db)
        logger.info(f"Updated {len(signals)} screening signals")
        return signals
