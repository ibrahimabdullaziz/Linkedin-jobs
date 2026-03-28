from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
import asyncio
from typing import List
from loguru import logger

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from models.job import Job
from database.repository import JobRepository

class TelegramNotifier:
    def __init__(self):
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        if self.enabled:
            self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        else:
            logger.warning("Telegram credentials missing in .env. Notifications are DISABLED.")

    async def send_startup_message(self):
        if not self.enabled:
            return
        
        try:
            msg = "🤖 *LinkedIn Job Scraper Bot Started*\n\nRunning and checking for new jobs every few minutes\\."
            await self.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.info("Sent startup message to Telegram.")
        except TelegramError as e:
            logger.error(f"Failed to send startup message: {e}")

    async def send_job_alerts(self, jobs: List[Job], repository: JobRepository):
        if not self.enabled or not jobs:
            return

        logger.info(f"Sending {len(jobs)} jobs to Telegram.")

        # Optional: Summary message if there are many jobs
        if len(jobs) > 5:
            await self._send_text(f"🚀 Found *{len(jobs)} new jobs*\\! Sending them now\\.\\.\\.")

        for job in jobs:
            msg_text = job.to_telegram_markdown()
            success = await self._send_text(msg_text)
            
            if success:
                repository.mark_as_sent(job.job_id)
            
            # Avoid hitting rate limits (Telegram max ~30 msg/sec, but generally safer below 1 msg/sec)
            await asyncio.sleep(1.5)

        logger.info("Finished sending jobs to Telegram.")

    async def _send_text(self, text: str) -> bool:
        try:
            await self.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True
            )
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            # If rate limit exceeded, we can log it here.
            return False
