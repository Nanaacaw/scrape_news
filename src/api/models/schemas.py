from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    source: str
    category: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    scraped_date: datetime
    tickers: List[str] = []
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    confidence: Optional[float] = None
    analyzed_date: Optional[datetime] = None

    class Config:
        orm_mode = True

class ArticleListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    articles: List[ArticleResponse]

class TickerComparison(BaseModel):
    ticker: str
    name: str
    avg_sentiment: float
    article_count: int
    positive_ratio: float

class SentimentCompareResponse(BaseModel):
    period_days: int
    comparison: List[TickerComparison]

class SentimentTrendPoint(BaseModel):
    date: str
    avg_sentiment: float
    article_count: int
    positive: int
    neutral: int
    negative: int

class SentimentTrendResponse(BaseModel):
    ticker: str
    period_days: int
    data: List[SentimentTrendPoint]

class SentimentSummary(BaseModel):
    ticker: Optional[str] = None
    period_days: int
    total_articles: int
    sentiment_distribution: dict
    avg_sentiment_score: float
    top_positive: List[ArticleResponse]
    top_negative: List[ArticleResponse]

class SearchResponse(BaseModel):
    query: str
    total: int
    articles: List[ArticleResponse]

class TopTicker(BaseModel):
    ticker: str
    name: str
    article_count: int
    avg_sentiment: float

class TopTickersResponse(BaseModel):
    top_tickers: List[TopTicker]

class StatsOverview(BaseModel):
    total_articles: int
    total_tickers: int
    sources: dict
    sentiment_distribution: dict
    last_updated: datetime

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime

