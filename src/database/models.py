"""
Database models for CNBC News Scraper
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Article(Base):
    """News article model"""
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    author = Column(String(200))
    category = Column(String(100))
    published_date = Column(DateTime)
    scraped_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationships
    sentiment = relationship("Sentiment", back_populates="article", uselist=False, cascade="all, delete-orphan")
    stocks = relationship("ArticleStock", back_populates="article", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_published_date', 'published_date'),
        Index('idx_category', 'category'),
    )
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>"

class Sentiment(Base):
    """Sentiment analysis results"""
    __tablename__ = 'sentiments'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), unique=True, nullable=False)
    sentiment_score = Column(Float, nullable=False)  # -1 (negative) to 1 (positive)
    sentiment_label = Column(String(20), nullable=False)  # positive, neutral, negative
    confidence = Column(Float, nullable=False)  # 0 to 1
    analyzed_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationship
    article = relationship("Article", back_populates="sentiment")
    
    def __repr__(self):
        return f"<Sentiment(article_id={self.article_id}, label='{self.sentiment_label}', score={self.sentiment_score:.2f})>"

class Stock(Base):
    """Stock/Company information"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(200))
    sector = Column(String(100))
    
    # Relationships
    articles = relationship("ArticleStock", back_populates="stock", cascade="all, delete-orphan")
    signals = relationship("ScreeningSignal", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock(ticker='{self.ticker}', name='{self.company_name}')>"

class ArticleStock(Base):
    """Many-to-many relationship between articles and stocks"""
    __tablename__ = 'article_stocks'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    
    # Relationships
    article = relationship("Article", back_populates="stocks")
    stock = relationship("Stock", back_populates="articles")
    
    __table_args__ = (
        Index('idx_article_stock', 'article_id', 'stock_id'),
    )

class ScreeningSignal(Base):
    """Stock screening signals based on sentiment analysis"""
    __tablename__ = 'screening_signals'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    signal_strength = Column(Float, nullable=False)  # 0 to 1
    avg_sentiment = Column(Float, nullable=False)
    article_count = Column(Integer, nullable=False)
    timeframe_days = Column(Integer, default=7)
    generated_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # Relationship
    stock = relationship("Stock", back_populates="signals")
    
    __table_args__ = (
        Index('idx_signal_date', 'generated_date'),
        Index('idx_signal_type', 'signal_type'),
    )
    
    def __repr__(self):
        return f"<ScreeningSignal(stock_id={self.stock_id}, signal='{self.signal_type}', strength={self.signal_strength:.2f})>"
