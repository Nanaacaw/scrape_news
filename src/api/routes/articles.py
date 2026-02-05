from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from src.database.models import Article
from src.api.models.schemas import ArticleResponse, ArticleListResponse
from src.api.dependencies import get_db

router = APIRouter(prefix="/api/articles", tags=["Articles"])

@router.get("",response_model=ArticleListResponse)
def get_articles(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ticker: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None, pattern="^(positive|neutral|negative)$"),
    source: Optional[str] = Query(None, pattern="^(cnbc|bloomberg)$"),
    category: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get list of articles with filtering and pagination
    """
    query = db.query(Article)
    
    if ticker:
        ticker_upper = ticker.upper()
        query = query.filter(Article.tickers.like(f"%{ticker_upper}%"))
    
    if sentiment:
        query = query.filter(Article.sentiment_label == sentiment)
    
    if source:
        query = query.filter(Article.source == source)
    
    if category:
        query = query.filter(Article.category == category)
    
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from)
            query = query.filter(Article.published_date >= date_from_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to)
            query = query.filter(Article.published_date <= date_to_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
    
    total = query.count()
    
    articles = query.order_by(desc(Article.published_date)).offset(offset).limit(limit).all()
    
    articles_response = []
    for article in articles:
        article_dict = {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "category": article.category,
            "author": article.author,
            "published_date": article.published_date,
            "scraped_date": article.scraped_date,
            "tickers": article.tickers.split(",") if article.tickers else [],
            "sentiment_score": article.sentiment_score,
            "sentiment_label": article.sentiment_label,
            "confidence": article.confidence,
            "analyzed_date": article.analyzed_date
        }
        articles_response.append(ArticleResponse(**article_dict))
    
    return ArticleListResponse(
        total=total,
        limit=limit,
        offset=offset,
        articles=articles_response
    )

@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Get single article by ID
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        raise HTTPException(status_code=404, detail=f"Article with id {article_id} not found")
    
    article_dict = {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "source": article.source,
        "category": article.category,
        "author": article.author,
        "published_date": article.published_date,
        "scraped_date": article.scraped_date,
        "tickers": article.tickers.split(",") if article.tickers else [],
        "sentiment_score": article.sentiment_score,
        "sentiment_label": article.sentiment_label,
        "confidence": article.confidence,
        "analyzed_date": article.analyzed_date
    }
    
    return ArticleResponse(**article_dict)
