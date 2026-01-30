from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta

from src.database.models import Article
from src.api.models.schemas import StatsOverview, TopTickersResponse, TopTicker, HealthResponse
from src.api.dependencies import get_db
from src.utils.helpers import get_stock_name

router = APIRouter(prefix="/api/stats", tags=["Statistics"])

@router.get("/overview", response_model=StatsOverview)
def get_overview(db: Session = Depends(get_db)):
    """
    Get overall statistics
    """
    total_articles = db.query(func.count(Article.id)).scalar()
    
    articles_with_tickers = db.query(Article).filter(Article.tickers.isnot(None)).all()
    unique_tickers = set()
    for article in articles_with_tickers:
        if article.tickers:
            tickers = article.tickers.split(",")
            unique_tickers.update(tickers)
    
    sources = db.query(
        Article.source,
        func.count(Article.id)
    ).group_by(Article.source).all()
    sources_dict = {source: count for source, count in sources}
    
    sentiments = db.query(
        Article.sentiment_label,
        func.count(Article.id)
    ).filter(Article.sentiment_label.isnot(None)).group_by(Article.sentiment_label).all()
    sentiment_dict = {label: count for label, count in sentiments}
    
    last_article = db.query(Article).order_by(desc(Article.scraped_date)).first()
    last_updated = last_article.scraped_date if last_article else datetime.now()
    
    return StatsOverview(
        total_articles=total_articles,
        total_tickers=len(unique_tickers),
        sources=sources_dict,
        sentiment_distribution=sentiment_dict,
        last_updated=last_updated
    )

@router.get("/tickers", response_model=TopTickersResponse)
def get_top_tickers(
    limit: int = Query(10, ge=1, le=50),
    days: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get most mentioned tickers
    """
    query = db.query(Article).filter(Article.tickers.isnot(None))
    
    if days:
        date_from = datetime.now() - timedelta(days=days)
        query = query.filter(Article.published_date >= date_from)
    
    articles = query.all()
    
    ticker_stats = {}
    for article in articles:
        if not article.tickers:
            continue
        
        tickers = article.tickers.split(",")
        for ticker in tickers:
            ticker = ticker.strip()
            if ticker not in ticker_stats:
                ticker_stats[ticker] = {
                    "count": 0,
                    "scores": []
                }
            
            ticker_stats[ticker]["count"] += 1
            if article.sentiment_score is not None:
                ticker_stats[ticker]["scores"].append(article.sentiment_score)
    
    top_tickers = []
    for ticker, stats in ticker_stats.items():
        avg_sentiment = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0.0
        
        top_tickers.append(TopTicker(
            ticker=ticker,
            name=get_stock_name(ticker),
            article_count=stats["count"],
            avg_sentiment=round(avg_sentiment, 3)
        ))
    
    top_tickers.sort(key=lambda x: x.article_count, reverse=True)
    top_tickers = top_tickers[:limit]
    
    return TopTickersResponse(top_tickers=top_tickers)

@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    API health check
    """
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        timestamp=datetime.now()
    )

