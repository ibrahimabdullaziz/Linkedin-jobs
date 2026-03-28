import asyncio
import sys
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import LOG_LEVEL, SCRAPE_INTERVAL_MINUTES, LINKEDIN_KEYWORDS, LINKEDIN_LOCATIONS
from database.repository import JobRepository
from scraper.linkedin import scrape_linkedin_jobs
from telegram_bot.notifier import TelegramNotifier

# Configure Loguru
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

async def scrape_and_notify(repo: JobRepository, notifier: TelegramNotifier):
    """Main pipeline execution for a single scrape cycle."""
    logger.info("Starting scheduled scrape cycle for multiple keywords and locations...")
    
    # 1. Scrape all combinations
    scraped_jobs = []
    for loc in LINKEDIN_LOCATIONS:
        for key in LINKEDIN_KEYWORDS:
            # Setting max_pages=1 to keep things quick since we have many combinations
            jobs = await scrape_linkedin_jobs(keyword=key, location=loc, max_pages=1)
            scraped_jobs.extend(jobs)
            # Short sleep between different searches to avoid rate limits
            await asyncio.sleep(2)
    
    if not scraped_jobs:
        logger.info("No jobs found this cycle across any combination.")
        return

    # 2. Store & Dedupe
    new_jobs_count = 0
    for job in scraped_jobs:
        if repo.insert_job(job):
            new_jobs_count += 1
            
    logger.info(f"Deduplication complete. {new_jobs_count} brand new jobs added to database.")

    # 3. Retrieve Pending & Notify
    unsent_jobs = repo.get_unsent_jobs()
    if unsent_jobs:
        await notifier.send_job_alerts(unsent_jobs, repo)
    else:
        logger.info("No unsent jobs pending for Telegram.")
        
    # 4. Cleanup old rows
    repo.cleanup_old_jobs(days=14)

async def main():
    repo = JobRepository()
    notifier = TelegramNotifier()

    await notifier.send_startup_message()

    logger.info("Running initial scrape cycle before scheduling...")
    await scrape_and_notify(repo, notifier)

    logger.info(f"Initializing APScheduler. Interval: {SCRAPE_INTERVAL_MINUTES} minutes.")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scrape_and_notify, 'interval', minutes=SCRAPE_INTERVAL_MINUTES, args=[repo, notifier])
    
    scheduler.start()
    
    try:
        # Keep the main thread alive for asyncio scheduler
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Graceful shutdown initiated.")
        scheduler.shutdown()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")
