from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.database.models import Article
from src.api.models.schemas import SearchResponse, ArticleResponse
from src.api.dependencies import get_db

router = APIRouter(prefix="/api/search", tags=["Search"])

@router.get("", response_model=SearchResponse)
def search_articles(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    search_in: str = Query("both", pattern="^(title|content|both)$"),
    db: Session = Depends(get_db)
):
    """
    Search articles by keyword
    """
    query = db.query(Article)
    
    search_term = f"%{q}%"
    
    if search_in == "title":
        query = query.filter(Article.title.like(search_term))
    elif search_in == "content":
        query = query.filter(Article.content.like(search_term))
    else:
        query = query.filter(
            or_(
                Article.title.like(search_term),
                Article.content.like(search_term)
            )
        )
    
    total = query.count()
    articles = query.limit(limit).all()
    
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
    
    return SearchResponse(
        query=q,
        total=total,
        articles=articles_response
    )
