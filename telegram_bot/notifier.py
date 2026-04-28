import aiohttp
import asyncio
from typing import List
from loguru import logger

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from models.job import Job
from database.repository import JobRepository

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        if not self.enabled:
            logger.warning("Telegram credentials missing. Notifications are DISABLED.")

    async def send_startup_message(self):
        if not self.enabled:
            return
        
        try:
            msg = "🤖 *LinkedIn Job Scraper Bot Started*\n\nRunning and checking for new jobs every few minutes\\."
            timeout = aiohttp.ClientTimeout(total=120, connect=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                result = await self._send_text(session, msg)
                if result:
                    logger.info("Sent startup message to Telegram.")
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")

    async def send_job_alerts(self, jobs: List[Job], repository: JobRepository):
        if not self.enabled or not jobs:
            return

        logger.info(f"Sending {len(jobs)} jobs to Telegram.")

        # Use a single persistent aiohttp session for ALL messages
        timeout = aiohttp.ClientTimeout(total=120, connect=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:

            if len(jobs) > 5:
                await self._send_text(session, f"🚀 Found *{len(jobs)} new jobs*\\! Sending them now\\.\\.\\.")

            for job in jobs:
                msg_text = job.to_telegram_markdown()
                success = await self._send_text(session, msg_text)
                
                if success:
                    repository.mark_as_sent(job.job_id)
                
                # Avoid hitting Telegram rate limits
                await asyncio.sleep(2)

        logger.info("Finished sending jobs to Telegram.")

    async def _send_text(self, session: aiohttp.ClientSession, text: str, max_retries: int = 5) -> bool:
        """Send a message to Telegram using aiohttp (different network stack than httpx)."""
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True
        }

        for attempt in range(1, max_retries + 1):
            try:
                async with session.post(TELEGRAM_API_URL, json=payload) as response:
                    if response.status == 200:
                        return True
                    elif response.status == 429:
                        body = await response.json()
                        retry_after = body.get("parameters", {}).get("retry_after", 10)
                        logger.warning(f"Rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                    else:
                        body = await response.text()
                        logger.error(f"Telegram API error {response.status}: {body}")
                        return False

            except (aiohttp.ClientConnectorError, asyncio.TimeoutError, aiohttp.ServerDisconnectedError) as e:
                wait_time = attempt * 15  # 15s, 30s, 45s, 60s, 75s
                logger.warning(f"Attempt {attempt}/{max_retries} failed: {type(e).__name__}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Unexpected error: {type(e).__name__}: {e}")
                return False
        
        logger.error(f"Failed to send Telegram message after {max_retries} retries.")
        return False
