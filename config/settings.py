import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# LinkedIn Scraping Settings (Comma-separated)
_keywords = os.getenv("LINKEDIN_KEYWORDS", "frontend, backend, fullstack, node, react, developer, tester, ui, ux, ai, .net, php, python, java, golang, go, c++, ruby, rust, angular, vue, django, spring, ios, android, flutter, react native, swift, kotlin, devops, machine learning, ml")
LINKEDIN_KEYWORDS = [k.strip() for k in _keywords.split(",") if k.strip()]

_locations = os.getenv("LINKEDIN_LOCATIONS", "Egypt, Saudi Arabia")
LINKEDIN_LOCATIONS = [loc.strip() for loc in _locations.split(",") if loc.strip()]

# Application Settings
try:
    SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "5"))
except ValueError:
    SCRAPE_INTERVAL_MINUTES = 5

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database Setting
DB_PATH = "jobs.db"
