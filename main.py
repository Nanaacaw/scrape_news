"""
CLI Interface for CNBC News Scraper
"""
import argparse
import sys

from src.database.connection import init_database, get_db
from src.scraper.cnbc_scraper import CNBCScraper
from src.pipeline.data_pipeline import DataPipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)


def init_db_command():
    """Initialize database"""
    logger.info("Initializing database...")
    init_database()
    logger.info("Database initialized successfully!")


def scrape_command(args):
    """Run scraper"""
    logger.info("Starting scraper...")
    
    scraper = CNBCScraper()
    pipeline = DataPipeline()
    
    # Scrape articles
    if args.category == 'market':
        articles = scraper.scrape_market_news(max_articles=args.limit)
    else:  # all (which is now just market)
        articles = scraper.scrape_all(max_articles_per_category=args.limit)
    
    logger.info(f"Scraped {len(articles)} articles")
    
    # Process through pipeline
    with get_db() as db:
        new_count = pipeline.process_articles(db, articles)
        logger.info(f"Processed {new_count} new articles")


def analyze_command(args):
    """Run sentiment analysis on existing articles"""
    logger.info("Running sentiment analysis...")
    
    pipeline = DataPipeline()
    
    with get_db() as db:
        from src.database.models import Article
        
        # Get articles without sentiment
        articles = db.query(Article).filter(Article.sentiment_label.is_(None)).all()
        
        if not articles:
            logger.info("All articles already have sentiment analysis")
            return
        
        logger.info(f"Analyzing {len(articles)} articles...")
        pipeline._analyze_sentiments(db, articles)
        logger.info("Sentiment analysis complete!")


def search_command(args):
    """Search articles by ticker"""
    with get_db() as db:
        from src.database.models import Article
        from sqlalchemy import or_
        
        ticker = args.ticker.upper()
        
        # Search articles that contain the ticker
        articles = db.query(Article).filter(
            or_(
                Article.tickers.like(f'%{ticker}%'),
                Article.tickers == ticker
            ),
            Article.sentiment_label.isnot(None)
        ).order_by(Article.published_date.desc()).all()
        
        if not articles:
            print(f"\n❌ No articles found for ticker: {ticker}")
            return
        
        print(f"\n{'='*80}")
        print(f"SEARCH RESULTS: {ticker}")
        print(f"{'='*80}")
        print(f"Found {len(articles)} articles\n")
        
        # Calculate sentiment stats
        sentiments = [a.sentiment_score for a in articles if a.sentiment_score]
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            positive = len([a for a in articles if a.sentiment_label == 'positive'])
            negative = len([a for a in articles if a.sentiment_label == 'negative'])
            neutral = len([a for a in articles if a.sentiment_label == 'neutral'])
            
            print(f"📊 Sentiment Summary:")
            print(f"   Average: {avg_sentiment:+.2f} ({'Positive' if avg_sentiment > 0 else 'Negative' if avg_sentiment < 0 else 'Neutral'})")
            print(f"   Positive: {positive} ({positive/len(articles)*100:.1f}%)")
            print(f"   Negative: {negative} ({negative/len(articles)*100:.1f}%)")
            print(f"   Neutral:  {neutral} ({neutral/len(articles)*100:.1f}%)")
            print()
        
        # Show articles
        print(f"📰 Recent Articles:")
        print(f"{'-'*80}")
        
        for i, article in enumerate(articles[:args.limit], 1):
            sentiment_emoji = "✅" if article.sentiment_label == 'positive' else "❌" if article.sentiment_label == 'negative' else "➖"
            
            print(f"\n{i}. {sentiment_emoji} [{article.sentiment_label.upper()}] {article.title}")
            print(f"   Score: {article.sentiment_score:+.2f} | Confidence: {article.confidence:.0%}")
            print(f"   Published: {article.published_date.strftime('%d %b %Y') if article.published_date else 'N/A'}")
            print(f"   Tickers: {article.tickers or 'None'}")
            print(f"   URL: {article.url}")
        
        print(f"\n{'='*80}\n")


def stats_command(args):
    """Show database statistics"""
    with get_db() as db:
        from src.database.models import Article
        from sqlalchemy import func
        
        article_count = db.query(func.count(Article.id)).scalar()
        analyzed_count = db.query(func.count(Article.id)).filter(Article.sentiment_label.isnot(None)).scalar()
        
        avg_sentiment = db.query(func.avg(Article.sentiment_score)).filter(
            Article.sentiment_label.isnot(None)
        ).scalar() or 0
        
        print("\n" + "="*80)
        print("DATABASE STATISTICS")
        print("="*80)
        print(f"Total Articles:      {article_count}")
        print(f"Analyzed Articles:   {analyzed_count}")
        print(f"Average Sentiment:   {avg_sentiment:.2f}")
        print("="*80 + "\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='CNBC Market News Scraper & Sentiment Analysis'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Init command
    subparsers.add_parser('init', help='Initialize database')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape news articles')
    scrape_parser.add_argument(
        '--category',
        choices=['market', 'all'],
        default='all',
        help='Category to scrape (all = market only)'
    )
    scrape_parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum articles to scrape'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run sentiment analysis')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search articles by ticker')
    search_parser.add_argument(
        '--ticker',
        type=str,
        required=True,
        help='Stock ticker to search (e.g., BBRI, BBCA, TLKM)'
    )
    search_parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Maximum number of articles to display'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch dashboard')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'init':
            init_db_command()
        elif args.command == 'scrape':
            scrape_command(args)
        elif args.command == 'analyze':
            analyze_command(args)
        elif args.command == 'search':
            search_command(args)
        elif args.command == 'stats':
            stats_command(args)
        elif args.command == 'dashboard':
            import subprocess
            subprocess.run(['streamlit', 'run', 'src/dashboard/app.py'])
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
