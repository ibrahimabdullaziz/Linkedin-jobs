<div align="center">
  <h1>🚀 LinkedIn Job to Telegram Bot</h1>
  <p>An automated, zero-dependency scraper that natively extracts LinkedIn job matches and delivers them straight to your Telegram channel.</p>
</div>

<hr />

## 🌟 Overview
No API keys. No Selenium. No heavy browser automation. 
This bot utilizes LinkedIn's lightweight Guest API to fetch the latest job postings, filter out duplicates using embedded SQLite, and forward beautiful Markdown messages straight to your chat 24/7.

### ✨ Key Features
- **Stateless & Lightweight:** Uses standard HTTP GET requests (`httpx`) without requiring a LinkedIn account or login cookies.
- **Smart Filtering:** Extracts only "Today's" or recent listings to keep your feed relevant.
- **Multi-Location & Keyword Engine:** Can search an infinite combination of job titles (e.g. `frontend`, `node`, `react`) across multiple countries entirely automatically.
- **Deduplication:** Prevents spamming your channel with duplicate posts using a local SQLite persistence layer.
- **Async Execution:** Highly performant non-blocking asynchronous event loops.

---

## 🛠 Prerequisites & Configuration

The bot is controlled entirely by Environment Variables. You simply provide it the keywords and your Telegram bot credentials. 

### Environment Variables Required
| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token provided by `@BotFather` on Telegram. |
| `TELEGRAM_CHAT_ID` | Your chat or channel ID. **For channels, you must include the `-100` prefix!** |
| `LINKEDIN_KEYWORDS` | Comma-separated list of job titles (e.g., `frontend, fullstack, react`) |
| `LINKEDIN_LOCATIONS` | Comma-separated list of locations (e.g., `Egypt, Remote, Canada`) |
| `SCRAPE_INTERVAL_MINUTES` | Frequency of the scraping loop in minutes (e.g., `10`) |

---

## 🚀 Deployment (Production)

This project is built to live on free-tier cloud environments. It binds to no ports and operates as an isolated background worker.

### 🚄 Railway.app (Recommended Free Cloud Hosting)
1. Fork or clone this repository to your GitHub account.
2. Sign in to [Railway](https://railway.app/).
3. Click **New Project** → **Deploy from GitHub repo** and select `Linkedin-jobs`.
4. In the Railway project settings, go to the **Variables** tab.
5. Paste your Telegram tokens, keywords, and locations as new variables.
6. Railway will automatically install packages and continuously run the bot.

---

## 💻 Local Quick Start

If you want to run or test the bot locally on your PC:

1. **Create Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environments**
   Create a file named `.env` in the root folder and add your configuration:
   ```env
   TELEGRAM_BOT_TOKEN="your_token_here"
   TELEGRAM_CHAT_ID="-100..."
   LINKEDIN_KEYWORDS="frontend, fullstack, react"
   LINKEDIN_LOCATIONS="Egypt, Remote, United States"
   SCRAPE_INTERVAL_MINUTES=10
   LOG_LEVEL="INFO"
   ```

4. **Launch the Bot**
   ```bash
   python main.py
   ```

---

<div align="center">
  <i>Built for scale. Maintained for developers.</i>
</div>
