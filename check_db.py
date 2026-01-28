"""
Quick database checker
"""
from src.database.connection import get_db
from src.database.models import Article, Sentiment
from sqlalchemy import func

print("\n" + "="*80)
print("DATABASE CHECK")
print("="*80)

with get_db() as db:
    # Count totals
    total_articles = db.query(func.count(Article.id)).scalar()
    analyzed_articles = db.query(func.count(Article.id)).filter(Article.sentiment_label.isnot(None)).scalar()
    
    print(f"\nTotal Articles:      {total_articles}")
    print(f"Analyzed Articles:   {analyzed_articles}")
    
    if total_articles > 0:
        # Get average sentiment
        avg_sentiment = db.query(func.avg(Article.sentiment_score)).filter(
            Article.sentiment_label.isnot(None)
        ).scalar()
        if avg_sentiment:
            print(f"Average Sentiment:   {avg_sentiment:.2f}")
        
        # Show recent articles
        print(f"\n{'='*80}")
        print("RECENT ARTICLES (Last 5)")
        print("="*80)
        
        articles = db.query(Article).order_by(Article.scraped_date.desc()).limit(5).all()
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   URL: {article.url[:70]}...")
            print(f"   Published: {article.published_date}")
            print(f"   Category: {article.category}")
            
            if article.sentiment_label:
                print(f"   Sentiment: {article.sentiment_label.upper()} "
                      f"(score: {article.sentiment_score:.2f}, "
                      f"confidence: {article.confidence:.2f})")
    else:
        print("\n⚠️ No articles found in database!")
        print("Run: python main.py scrape --limit 10 --generate-signals")

print("\n" + "="*80 + "\n")
