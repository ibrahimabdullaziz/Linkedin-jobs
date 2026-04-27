import httpx
import urllib.parse
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
        
    logger.info(f"Scraping Wuzzuf for '{keyword}' in '{location}'")
    
    url = "https://wuzzuf.net/search/jobs/"
    params = {
        "q": keyword,
        "a[]": "New",
        "l[]": "Egypt"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers, timeout=20.0)
            if resp.status_code == 404:
                return all_jobs
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div[class*='css-'][data-search-result]")
            if not cards:
                cards = soup.select("div.css-1gatmva, article.css-1xaesre")
            
            for card in cards[:max_results]:
                title_el = card.select_one("h2 a, h3 a, a[class*='css-'][data-pk]")
                if not title_el:
                    title_el = card.select_one("a[href*='/jobs/p/']")
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job_url = f"https://wuzzuf.net{href}" if href.startswith("/") else href
                
                # Extract ID from URL or title
                job_id = f"wuzzuf_{href.split('-')[-1]}" if '-' in href else f"wuzzuf_{title}"
                
                company_el = card.select_one("a[class*='company'], span[class*='company'], div[class*='company']")
                company = company_el.get_text(strip=True).replace("-", "").strip() if company_el else "Unknown Company"
                
                loc_el = card.select_one("span[class*='location'], a[class*='location']")
                loc = loc_el.get_text(strip=True) if loc_el else "Egypt"
                
                date_el = card.select_one("span[class*='ago'], time, span[class*='date']")
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
    except Exception as e:
        logger.error(f"Error scraping Wuzzuf: {e}")
        
    logger.info(f"Wuzzuf found {len(all_jobs)} jobs.")
    return all_jobs
