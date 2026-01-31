from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(200))
    category = Column(String(100))
    published_date = Column(DateTime)
    scraped_date = Column(DateTime, default=datetime.now, nullable=False)
    
    tickers = Column(String(500))  
    sentiment_score = Column(Float)  
    sentiment_label = Column(String(20))
    confidence = Column(Float)  
    analyzed_date = Column(DateTime)
    
    # Active Learning / Feedback Loop fields
    is_corrected = Column(Boolean, default=False)
    corrected_label = Column(String(20), nullable=True)
    correction_date = Column(DateTime, nullable=True)
    
    # Relationship to per-ticker sentiment
    ticker_sentiments = relationship("TickerSentiment", back_populates="article", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_published_date', 'published_date'),
        Index('idx_category', 'category'),
        Index('idx_sentiment_label', 'sentiment_label'),
        Index('idx_tickers', 'tickers'),
    )
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', sentiment='{self.sentiment_label}')>"

class TickerSentiment(Base):
    """
    Stores specific sentiment for a ticker mentioned in an article.
    (Aspect-Based Sentiment Analysis)
    """
    __tablename__ = 'ticker_sentiments'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    ticker = Column(String(10), nullable=False, index=True)
    
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    confidence = Column(Float)
    
    # The snippet of text used to determine this sentiment
    context_text = Column(Text, nullable=True)
    
    article = relationship("Article", back_populates="ticker_sentiments")
    
    __table_args__ = (
        Index('idx_ts_ticker', 'ticker'),
        Index('idx_ts_article_ticker', 'article_id', 'ticker', unique=True),
    )
    
    def __repr__(self):
        return f"<TickerSentiment(ticker='{self.ticker}', score={self.sentiment_score}, label='{self.sentiment_label}')>"
