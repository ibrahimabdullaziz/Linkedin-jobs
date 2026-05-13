import asyncio
import sys
import os
from aiohttp import web
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import LOG_LEVEL, SCRAPE_INTERVAL_MINUTES, LINKEDIN_KEYWORDS, LINKEDIN_LOCATIONS
from database.repository import JobRepository
from scraper.linkedin import scrape_linkedin_jobs
from scraper.remotive import scrape_remotive_jobs
from scraper.himalayas import scrape_himalayas_jobs
from scraper.wuzzuf import scrape_wuzzuf_jobs
from scraper.bayt import scrape_bayt_jobs
from scraper.gulftalent import scrape_gulftalent_jobs
from telegram_bot.notifier import TelegramNotifier

# Configure Loguru
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

# Concurrency control — prevents slamming APIs and hitting Railway log limits
MAX_CONCURRENT = 10

async def scrape_and_notify(repo: JobRepository, notifier: TelegramNotifier):
    """Main pipeline execution for a single scrape cycle."""
    logger.info(f"Starting scrape cycle — {len(LINKEDIN_KEYWORDS)} keywords × {len(LINKEDIN_LOCATIONS)} locations")
    
    scraped_jobs = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    async def rate_limited(coro):
        """Wrap a scraper coroutine with a semaphore for rate limiting."""
        async with semaphore:
            result = await coro
            await asyncio.sleep(0.3)  # Small delay between completions
            return result
    
    tasks = []
    
    # ── Location-AWARE scrapers (need to run per keyword × location) ──
    for loc in LINKEDIN_LOCATIONS:
        for key in LINKEDIN_KEYWORDS:
            tasks.append(rate_limited(scrape_linkedin_jobs(keyword=key, location=loc, max_pages=1)))
            tasks.append(rate_limited(scrape_wuzzuf_jobs(keyword=key, location=loc, max_results=10)))
            tasks.append(rate_limited(scrape_bayt_jobs(keyword=key, location=loc, max_results=10)))
            tasks.append(rate_limited(scrape_gulftalent_jobs(keyword=key, location=loc, max_results=10)))
    
    # ── Location-AGNOSTIC scrapers (only run once per keyword) ──
    for key in LINKEDIN_KEYWORDS:
        tasks.append(rate_limited(scrape_remotive_jobs(keyword=key, location="Remote", max_results=10)))
        tasks.append(rate_limited(scrape_himalayas_jobs(keyword=key, location="Remote", max_results=10)))

    logger.info(f"Dispatching {len(tasks)} scraper tasks (max {MAX_CONCURRENT} concurrent)...")
    
    # Run them concurrently (bounded by semaphore)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    error_count = 0
    for res in results:
        if isinstance(res, list):
            scraped_jobs.extend(res)
        elif isinstance(res, Exception):
            error_count += 1
            logger.error(f"A scraper failed with exception: {res}")
    
    logger.info(f"Scraping done. {len(scraped_jobs)} raw jobs collected, {error_count} errors.")
    
    if not scraped_jobs:
        logger.info("No jobs found this cycle across any source.")
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
    
    # --- Web Server for UptimeRobot (Render Fix) ---
    async def health_check(request):
        return web.Response(text="Bot is running!")

    app = web.Application()
    app.router.add_get('/', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Web server started on port {port} for UptimeRobot pings.")
    # -----------------------------------------------

    try:
        # Keep the main thread alive for asyncio scheduler and web server
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Graceful shutdown initiated.")
        scheduler.shutdown()
        await runner.cleanup()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")
