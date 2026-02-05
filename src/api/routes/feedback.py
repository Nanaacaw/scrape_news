from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from src.database.models import Article
from src.api.dependencies import get_db
from src.utils.logger import get_logger

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])
logger = get_logger(__name__)

class FeedbackRequest(BaseModel):
    sentiment_label: str  # corrected label: positive, negative, neutral
    notes: Optional[str] = None

@router.post("/articles/{article_id}")
def submit_feedback(
    article_id: int, 
    feedback: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit manual feedback/correction for article sentiment.
    Used for Active Learning loop.
    """
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Validate label
    valid_labels = ['positive', 'negative', 'neutral']
    if feedback.sentiment_label not in valid_labels:
        raise HTTPException(status_code=400, detail=f"Invalid label. Must be one of {valid_labels}")
    
    # Update article with correction
    article.is_corrected = True
    article.corrected_label = feedback.sentiment_label
    article.correction_date = datetime.now()
    
    db.commit()
    
    logger.info(f"Feedback received for Article {article_id}: {article.sentiment_label} -> {feedback.sentiment_label}")
    
    return {
        "status": "success",
        "message": "Feedback recorded successfully",
        "article_id": article_id,
        "new_label": feedback.sentiment_label
    }
