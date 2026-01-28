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
    elif args.category == 'investment':
        articles = scraper.scrape_investment_news(max_articles=args.limit)
    else:  # all
        articles = scraper.scrape_all(max_articles_per_category=args.limit)
    
    logger.info(f"Scraped {len(articles)} articles")
    
    # Process through pipeline
    with get_db() as db:
        new_count = pipeline.process_articles(db, articles)
        logger.info(f"Processed {new_count} new articles")
        
        if args.generate_signals:
            pipeline.update_screening_signals(db)


def analyze_command(args):
    """Run sentiment analysis on existing articles"""
    logger.info("Running sentiment analysis...")
    
    pipeline = DataPipeline()
    
    with get_db() as db:
        from src.database.models import Article
        
        # Get articles without sentiment
        articles = db.query(Article).filter(~Article.sentiment.has()).all()
        
        if not articles:
            logger.info("All articles already have sentiment analysis")
            return
        
        logger.info(f"Analyzing {len(articles)} articles...")
        pipeline._analyze_sentiments(db, articles)
        logger.info("Sentiment analysis complete!")


def screen_command(args):
    """Generate screening signals"""
    logger.info("Generating screening signals...")
    
    pipeline = DataPipeline()
    
    with get_db() as db:
        signals = pipeline.update_screening_signals(db)
        
        if args.show:
            from src.screening.screener import StockScreener
            screener = StockScreener()
            
            print("\n" + "="*80)
            print("SCREENING SIGNALS")
            print("="*80)
            
            for signal_type in ['BUY', 'SELL', 'HOLD']:
                results = screener.get_top_signals(db, signal_type=signal_type, limit=args.limit)
                
                if results:
                    print(f"\n{signal_type} Signals:")
                    print("-" * 80)
                    
                    for r in results:
                        print(f"  {r['ticker']:6} | {r['company_name'] or 'N/A':30} | "
                              f"Strength: {r['signal_strength']:4.2f} | "
                              f"Sentiment: {r['avg_sentiment']:5.2f} | "
                              f"Articles: {r['article_count']:3}")
            
            print("\n" + "="*80)


def stats_command(args):
    """Show database statistics"""
    with get_db() as db:
        from src.database.models import Article, Sentiment, Stock, ScreeningSignal
        from sqlalchemy import func
        
        article_count = db.query(func.count(Article.id)).scalar()
        sentiment_count = db.query(func.count(Sentiment.id)).scalar()
        stock_count = db.query(func.count(Stock.id)).scalar()
        signal_count = db.query(func.count(ScreeningSignal.id)).scalar()
        
        avg_sentiment = db.query(func.avg(Sentiment.sentiment_score)).scalar() or 0
        
        print("\n" + "="*80)
        print("DATABASE STATISTICS")
        print("="*80)
        print(f"Total Articles:      {article_count}")
        print(f"Analyzed Articles:   {sentiment_count}")
        print(f"Unique Stocks:       {stock_count}")
        print(f"Screening Signals:   {signal_count}")
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
        choices=['market', 'investment', 'all'],
        default='all',
        help='Category to scrape'
    )
    scrape_parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum articles per category'
    )
    scrape_parser.add_argument(
        '--generate-signals',
        action='store_true',
        help='Generate screening signals after scraping'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run sentiment analysis')
    
    # Screen command
    screen_parser = subparsers.add_parser('screen', help='Generate screening signals')
    screen_parser.add_argument(
        '--show',
        action='store_true',
        help='Display signals after generation'
    )
    screen_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of signals to show per type'
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
        elif args.command == 'screen':
            screen_command(args)
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
