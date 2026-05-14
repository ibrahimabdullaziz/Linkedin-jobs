import httpx
import urllib.parse
import random
import asyncio
from bs4 import BeautifulSoup
from typing import List
from loguru import logger
from models.job import Job

EGYPT_LOCATIONS = {"egypt", "cairo", "alexandria", "giza", "مصر", "القاهرة"}

def is_egypt_location(location: str) -> bool:
    loc = location.lower()
    return any(kw in loc for kw in EGYPT_LOCATIONS)

async def scrape_wuzzuf_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from Wuzzuf (Egypt)."""
    all_jobs = []
    
    if not is_egypt_location(location):
        return all_jobs
        
    logger.debug(f"Scraping Wuzzuf for '{keyword}' in '{location}'")
    
    # Use the search URL format that Wuzzuf currently supports
    encoded_keyword = urllib.parse.quote_plus(keyword)
    url = f"https://wuzzuf.net/search/jobs/?q={encoded_keyword}&a%5B%5D=New&filters%5Bcountry%5D%5B0%5D=Egypt"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for attempt in range(3):
                resp = await client.get(url, headers=headers, timeout=20.0)
                
                if resp.status_code == 429:
                    wait_time = random.uniform(2.0, 4.0) * (2 ** attempt)
                    logger.warning(f"Wuzzuf rate limit (429) hit. Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    continue
                    
                if resp.status_code in (404, 403):
                    return all_jobs
                    
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Try multiple selector strategies — Wuzzuf changes their HTML frequently
                cards = []
                
                # Strategy 1: Job search result cards with data attributes
                cards = soup.select("div[data-search-result]")
                
                # Strategy 2: Common card container patterns
                if not cards:
                    cards = soup.select("div.css-pkv5jg, div.css-1gatmva")
                
                # Strategy 3: Look for job links with /jobs/p/ pattern
                if not cards:
                    cards = soup.select("div.css-1symr6o")
                
                # Strategy 4: Any div containing a job link
                if not cards:
                    job_links = soup.select("a[href*='/jobs/p/']")
                    cards = [link.find_parent("div", class_=True) for link in job_links if link.find_parent("div", class_=True)]
                
                for card in cards[:max_results]:
                    if not card:
                        continue
                        
                    # Find title link
                    title_el = card.select_one("a[href*='/jobs/p/']")
                    if not title_el:
                        title_el = card.select_one("h2 a")
                    if not title_el:
                        continue
                    
                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    job_url = f"https://wuzzuf.net{href}" if href.startswith("/") else href
                    
                    # Extract ID from URL or title
                    job_id = f"wuzzuf_{href.split('-')[-1]}" if '-' in href else f"wuzzuf_{title}"
                    
                    # Company — try multiple patterns
                    company_el = (
                        card.select_one("a[class*='company']") or
                        card.select_one("span[class*='company']") or
                        card.select_one("div > a[href*='/jobs/companies/']")
                    )
                    company = company_el.get_text(strip=True).replace("-", "").strip() if company_el else "Unknown Company"
                    
                    # Location
                    loc_el = (
                        card.select_one("span[class*='location']") or
                        card.select_one("a[class*='location']") or
                        card.select_one("span.css-5wys0k")
                    )
                    loc = loc_el.get_text(strip=True) if loc_el else "Egypt"
                    
                    # Date
                    date_el = card.select_one("time") or card.select_one("span[class*='ago']") or card.select_one("span[class*='date']")
                    posted_date = date_el.get("datetime", date_el.get_text(strip=True)) if date_el else ""
                    
                    job = Job(
                        job_id=job_id,
                        title=title,
                        company=company,
                        location=loc,
                        job_url=job_url,
                        posted_date=posted_date,
                        source="Wuzzuf"
                    )
                    all_jobs.append(job)
                
                break # Exit the retry loop if successful
                
    except Exception as e:
        logger.error(f"Error scraping Wuzzuf: {e}")
        
    logger.debug(f"Wuzzuf found {len(all_jobs)} jobs for '{keyword}'.")
    return all_jobs
