import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from src.database.connection import get_db
from src.scraper.cnbc_scraper import CNBCScraper
from src.pipeline.data_pipeline import DataPipeline
from src.utils.config import SCRAPE_INTERVAL_HOURS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def scheduled_scrape_job():
    """Job to run periodic scraping"""
    try:
        logger.info("Starting scheduled scraping job...")
        
        scraper = CNBCScraper()
        pipeline = DataPipeline()

        from src.utils.config import MAX_ARTICLES_PER_SCRAPE
        max_pages = 1
        
        articles = scraper.scrape_all(
            max_articles_per_category=MAX_ARTICLES_PER_SCRAPE,
            max_pages=max_pages
        )
        logger.info(f"Scraped {len(articles)} articles")
        
        with get_db() as db:
            new_count = pipeline.process_articles(db, articles)
            logger.info(f"Processed {new_count} new articles")
        
        logger.info("Scheduled scraping job completed successfully")
        
    except Exception as e:
        logger.error(f"Scheduled scraping job failed: {e}")


def run_scheduler():
    """
    Run the scheduler
    
    By default, runs every SCRAPE_INTERVAL_HOURS
    """
    scheduler = BlockingScheduler()
    
    scheduler.add_job(
        scheduled_scrape_job,
        'interval',
        hours=SCRAPE_INTERVAL_HOURS,
        id='scrape_job',
        name='CNBC News Scraping Job',
        replace_existing=True
    )
    
    logger.info(f"Scheduler started. Will run every {SCRAPE_INTERVAL_HOURS} hour(s)")
    logger.info("Press Ctrl+C to exit")
    
    logger.info("Running initial scrape...")
    scheduled_scrape_job()
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == '__main__':
    run_scheduler()
