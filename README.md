<div align="center">
  <h1>🚀 Multi-Board Job to Telegram Bot</h1>
  <p>An automated, zero-dependency async scraper that extracts job matches from 8+ major job boards (including MENA & Remote platforms) and delivers them straight to your Telegram channel.</p>
  <p><strong>Join the Channel:</strong> <a href="https://t.me/software_jobs_linkedin">t.me/software_jobs_linkedin</a></p>
</div>

<hr />

## Overview

No heavy browser automation required. 
This bot utilizes ultra-fast concurrent `httpx` requests to fetch the latest job postings from multiple job boards simultaneously. It filters out duplicates using embedded SQLite and forwards beautiful Markdown messages straight to your chat 24/7.

### 🌐 Supported Job Boards

1. **LinkedIn** (Guest API)
2. **Wuzzuf** (Egypt Focus)
3. **Bayt** (MENA: Egypt, KSA, UAE)
4. **GulfTalent** (Gulf: KSA, UAE)
5. **Adzuna** (UAE, KSA)
6. **Remotive** (Remote Global)
7. **Arbeitnow** (Remote Global)
8. **Himalayas** (Remote Global)

### Key Features

- **Massive Concurrency:** Uses `asyncio.gather` to scrape multiple boards, keywords, and locations simultaneously.
- **Smart Filtering & Limits:** Limits each board to the freshest jobs (e.g., max 10-20 per run) to keep your feed highly relevant.
- **Deduplication:** Prevents spamming your channel with duplicate posts using a local SQLite persistence layer.
- **Source Tracking:** Each Telegram message clearly indicates which board the job came from (e.g., `📌 via Wuzzuf`).
- **Stateless & Lightweight:** Operates as an isolated background worker perfect for free-tier cloud hosting.

---

## Prerequisites & Configuration

The bot is controlled entirely by Environment Variables. You simply provide it the keywords, locations, and your API credentials.

### Environment Variables Required

Create a `.env` file in the root folder:

| Variable                  | Description                                                                    |
| ------------------------- | ------------------------------------------------------------------------------ |
| `TELEGRAM_BOT_TOKEN`      | Token provided by `@BotFather` on Telegram.                                    |
| `TELEGRAM_CHAT_ID`        | Your chat or channel ID. **For channels, you must include the `-100` prefix!** |
| `LINKEDIN_KEYWORDS`       | Comma-separated list of job titles (e.g., `frontend, fullstack, react`)        |
| `LINKEDIN_LOCATIONS`      | Comma-separated list of locations (e.g., `Egypt, Saudi Arabia, United Arab Emirates`) |
| `SCRAPE_INTERVAL_MINUTES` | Frequency of the scraping loop in minutes (e.g., `10`)                         |
| `ADZUNA_APP_ID`           | (Optional) Free App ID from developer.adzuna.com                               |
| `ADZUNA_APP_KEY`          | (Optional) Free App Key from developer.adzuna.com                              |

---

## Deployment (Production)

This project is built to live on free-tier cloud environments. It binds to no ports and operates as an isolated background worker.

### Railway.app (Recommended Free Cloud Hosting)

1. Fork or clone this repository to your GitHub account.
2. Sign in to [Railway](https://railway.app/).
3. Click **New Project** → **Deploy from GitHub repo** and select your repo.
4. In the Railway project settings, go to the **Variables** tab.
5. Paste your Telegram tokens, Adzuna credentials, keywords, and locations as new variables.
6. Railway will automatically install packages and continuously run the bot.

---

## Local Quick Start

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
   Add your `.env` configuration as detailed above.

4. **Launch the Bot**
   ```bash
   python main.py
   ```

---

<div align="center">
  <i>Built for scale. Maintained for developers.</i>
</div>
