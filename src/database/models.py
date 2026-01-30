from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Index
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
    
    __table_args__ = (
        Index('idx_published_date', 'published_date'),
        Index('idx_category', 'category'),
        Index('idx_sentiment_label', 'sentiment_label'),
        Index('idx_tickers', 'tickers'),
    )
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', sentiment='{self.sentiment_label}', tickers='{self.tickers}')>"

