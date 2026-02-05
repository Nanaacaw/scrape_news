from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from src.database.models import Article
from src.api.models.schemas import (
    SentimentSummary, SentimentTrendResponse, SentimentTrendPoint,
    SentimentCompareResponse, TickerComparison, ArticleResponse
)
from src.api.dependencies import get_db
from src.utils.helpers import get_stock_name

router = APIRouter(prefix="/api/sentiment", tags=["Sentiment"])

@router.get("/summary", response_model=SentimentSummary)
def get_sentiment_summary(
    ticker: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get sentiment summary statistics
    """
    query = db.query(Article).filter(Article.sentiment_label.isnot(None))
    
    date_from = datetime.now() - timedelta(days=days)
    query = query.filter(Article.published_date >= date_from)
    
    if ticker:
        ticker_upper = ticker.upper()
        query = query.filter(Article.tickers.like(f"%{ticker_upper}%"))
    
    articles = query.all()
    
    if not articles:
        return SentimentSummary(
            ticker=ticker,
            period_days=days,
            total_articles=0,
            sentiment_distribution={"positive": 0, "neutral": 0, "negative": 0},
            avg_sentiment_score=0.0,
            top_positive=[],
            top_negative=[]
        )
    
    distribution = {"positive": 0, "neutral": 0, "negative": 0}
    total_score = 0.0
    
    for article in articles:
        if article.sentiment_label:
            distribution[article.sentiment_label] = distribution.get(article.sentiment_label, 0) + 1
        if article.sentiment_score is not None:
            total_score += article.sentiment_score
    
    avg_score = total_score / len(articles) if articles else 0.0
    
    positive_articles = sorted(
        [a for a in articles if a.sentiment_score and a.sentiment_score > 0],
        key=lambda x: x.sentiment_score,
        reverse=True
    )[:5]
    
    negative_articles = sorted(
        [a for a in articles if a.sentiment_score and a.sentiment_score < 0],
        key=lambda x: x.sentiment_score
    )[:5]
    
    def to_article_response(article):
        return ArticleResponse(
            id=article.id,
            title=article.title,
            url=article.url,
            source=article.source,
            category=article.category,
            author=article.author,
            published_date=article.published_date,
            scraped_date=article.scraped_date,
            tickers=article.tickers.split(",") if article.tickers else [],
            sentiment_score=article.sentiment_score,
            sentiment_label=article.sentiment_label,
            confidence=article.confidence,
            analyzed_date=article.analyzed_date
        )
    
    return SentimentSummary(
        ticker=ticker,
        period_days=days,
        total_articles=len(articles),
        sentiment_distribution=distribution,
        avg_sentiment_score=round(avg_score, 3),
        top_positive=[to_article_response(a) for a in positive_articles],
        top_negative=[to_article_response(a) for a in negative_articles]
    )

@router.get("/trend", response_model=SentimentTrendResponse)
def get_sentiment_trend(
    ticker: str = Query(...),
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db)
):
    """
    Get sentiment trend over time for a specific ticker
    """
    ticker_upper = ticker.upper()
    date_from = datetime.now() - timedelta(days=days)
    
    articles = db.query(Article).filter(
        Article.tickers.like(f"%{ticker_upper}%"),
        Article.published_date >= date_from,
        Article.sentiment_label.isnot(None)
    ).all()
    
    if not articles:
        return SentimentTrendResponse(ticker=ticker_upper, period_days=days, data=[])
    
    daily_data = {}
    for article in articles:
        if not article.published_date:
            continue
        
        date_key = article.published_date.date().isoformat()
        
        if date_key not in daily_data:
            daily_data[date_key] = {
                "scores": [],
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }
        
        if article.sentiment_score is not None:
            daily_data[date_key]["scores"].append(article.sentiment_score)
        
        if article.sentiment_label:
            daily_data[date_key][article.sentiment_label] += 1
    
    trend_points = []
    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]
        avg_sentiment = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0.0
        
        trend_points.append(SentimentTrendPoint(
            date=date_str,
            avg_sentiment=round(avg_sentiment, 3),
            article_count=len(data["scores"]),
            positive=data["positive"],
            neutral=data["neutral"],
            negative=data["negative"]
        ))
    
    return SentimentTrendResponse(
        ticker=ticker_upper,
        period_days=days,
        data=trend_points
    )

@router.get("/compare", response_model=SentimentCompareResponse)
def compare_sentiments(
    tickers: str = Query(..., description="Comma-separated tickers, e.g., 'BBRI,BBCA,BMRI'"),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Compare sentiment across multiple tickers
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    date_from = datetime.now() - timedelta(days=days)
    
    comparisons = []
    
    for ticker in ticker_list:
        articles = db.query(Article).filter(
            Article.tickers.like(f"%{ticker}%"),
            Article.published_date >= date_from,
            Article.sentiment_label.isnot(None)
        ).all()
        
        if not articles:
            continue
        
        total = len(articles)
        positive_count = sum(1 for a in articles if a.sentiment_label == "positive")
        total_score = sum(a.sentiment_score for a in articles if a.sentiment_score is not None)
        avg_sentiment = total_score / total if total > 0 else 0.0
        positive_ratio = positive_count / total if total > 0 else 0.0
        
        comparisons.append(TickerComparison(
            ticker=ticker,
            name=get_stock_name(ticker),
            avg_sentiment=round(avg_sentiment, 3),
            article_count=total,
            positive_ratio=round(positive_ratio, 3)
        ))
    
    comparisons.sort(key=lambda x: x.avg_sentiment, reverse=True)
    
    return SentimentCompareResponse(
        period_days=days,
        comparison=comparisons
    )
