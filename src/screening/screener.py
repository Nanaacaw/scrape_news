"""
Stock Screening Engine
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.database.models import Article, Sentiment, Stock, ArticleStock, ScreeningSignal
from src.utils.config import MIN_SENTIMENT_SCORE, MIN_ARTICLES_FOR_SIGNAL, SIGNAL_TIMEFRAME_DAYS
from src.utils.logger import get_logger
from src.utils.helpers import extract_stock_tickers

logger = get_logger(__name__)

class StockScreener:
    """
    Stock screening engine based on sentiment analysis
    """
    
    def __init__(
        self,
        min_sentiment: float = MIN_SENTIMENT_SCORE,
        min_articles: int = MIN_ARTICLES_FOR_SIGNAL,
        timeframe_days: int = SIGNAL_TIMEFRAME_DAYS
    ):
        """
        Initialize screener
        
        Args:
            min_sentiment: Minimum absolute sentiment score for signal generation
            min_articles: Minimum number of articles required for signal
            timeframe_days: Number of days to look back for articles
        """
        self.min_sentiment = min_sentiment
        self.min_articles = min_articles
        self.timeframe_days = timeframe_days
    
    def generate_signals(self, db: Session) -> List[ScreeningSignal]:
        """
        Generate trading signals for all stocks based on recent sentiment
        
        Args:
            db: Database session
            
        Returns:
            List of screening signals
        """
        logger.info("Generating screening signals...")
        
        # Calculate time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.timeframe_days)
        
        # Get all stocks
        stocks = db.query(Stock).all()
        signals = []
        
        for stock in stocks:
            signal = self._generate_stock_signal(db, stock, start_date, end_date)
            if signal:
                signals.append(signal)
        
        # Save signals to database
        for signal in signals:
            db.add(signal)
        
        db.commit()
        logger.info(f"Generated {len(signals)} screening signals")
        
        return signals
    
    def _generate_stock_signal(
        self,
        db: Session,
        stock: Stock,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[ScreeningSignal]:
        """Generate signal for a single stock"""
        
        # Get recent articles mentioning this stock
        articles = db.query(Article).join(ArticleStock).filter(
            ArticleStock.stock_id == stock.id,
            Article.published_date >= start_date,
            Article.published_date <= end_date
        ).all()
        
        if len(articles) < self.min_articles:
            logger.debug(f"Insufficient articles for {stock.ticker}: {len(articles)} < {self.min_articles}")
            return None
        
        # Get sentiment scores for these articles
        sentiments = []
        for article in articles:
            if article.sentiment:
                sentiments.append(article.sentiment.sentiment_score)
        
        if not sentiments:
            return None
        
        # Calculate average sentiment
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Determine signal type
        signal_type, signal_strength = self._calculate_signal(avg_sentiment, sentiments)
        
        # Only create signal if strength is significant
        if abs(avg_sentiment) < self.min_sentiment:
            return None
        
        signal = ScreeningSignal(
            stock_id=stock.id,
            signal_type=signal_type,
            signal_strength=signal_strength,
            avg_sentiment=avg_sentiment,
            article_count=len(articles),
            timeframe_days=self.timeframe_days,
            generated_date=datetime.now()
        )
        
        logger.info(
            f"Signal for {stock.ticker}: {signal_type} "
            f"(strength={signal_strength:.2f}, avg_sentiment={avg_sentiment:.2f}, "
            f"articles={len(articles)})"
        )
        
        return signal
    
    def _calculate_signal(self, avg_sentiment: float, sentiments: List[float]) -> tuple:
        """
        Calculate signal type and strength
        
        Returns:
            (signal_type, signal_strength)
        """
        # Calculate sentiment consistency (lower std = more consistent)
        import numpy as np
        std_sentiment = np.std(sentiments)
        consistency = 1 / (1 + std_sentiment)  # 0 to 1, higher is more consistent
        
        # Signal strength combines average sentiment and consistency
        signal_strength = abs(avg_sentiment) * consistency
        
        # Determine signal type
        if avg_sentiment > self.min_sentiment:
            signal_type = 'BUY'
        elif avg_sentiment < -self.min_sentiment:
            signal_type = 'SELL'
        else:
            signal_type = 'HOLD'
        
        return signal_type, signal_strength
    
    def get_top_signals(
        self,
        db: Session,
        signal_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top screening signals
        
        Args:
            db: Database session
            signal_type: Filter by signal type (BUY, SELL, HOLD)
            limit: Maximum number of results
            
        Returns:
            List of signal dictionaries with stock information
        """
        query = db.query(ScreeningSignal).join(Stock)
        
        if signal_type:
            query = query.filter(ScreeningSignal.signal_type == signal_type.upper())
        
        # Order by signal strength (highest first)
        query = query.order_by(desc(ScreeningSignal.signal_strength))
        
        signals = query.limit(limit).all()
        
        results = []
        for signal in signals:
            results.append({
                'ticker': signal.stock.ticker,
                'company_name': signal.stock.company_name,
                'signal_type': signal.signal_type,
                'signal_strength': signal.signal_strength,
                'avg_sentiment': signal.avg_sentiment,
                'article_count': signal.article_count,
                'timeframe_days': signal.timeframe_days,
                'generated_date': signal.generated_date
            })
        
        return results
    
    def extract_and_save_stocks(self, db: Session, article: Article):
        """
        Extract stock tickers from article and save to database
        
        Args:
            db: Database session
            article: Article object
        """
        # Extract tickers from title and content
        text = f"{article.title} {article.content}"
        tickers = extract_stock_tickers(text)
        
        if not tickers:
            return
        
        logger.debug(f"Found tickers in article {article.id}: {tickers}")
        
        for ticker in tickers:
            # Get or create stock
            stock = db.query(Stock).filter(Stock.ticker == ticker).first()
            
            if not stock:
                stock = Stock(ticker=ticker)
                db.add(stock)
                db.flush()  # Get stock ID
            
            # Check if relationship already exists
            existing = db.query(ArticleStock).filter(
                ArticleStock.article_id == article.id,
                ArticleStock.stock_id == stock.id
            ).first()
            
            if not existing:
                article_stock = ArticleStock(
                    article_id=article.id,
                    stock_id=stock.id
                )
                db.add(article_stock)
        
        db.commit()
