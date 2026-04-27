import httpx
import urllib.parse
from bs4 import BeautifulSoup
from typing import List
from loguru import logger
from models.job import Job

LOCATION_MAP = {
    "uae": "ae", "united arab emirates": "ae", "dubai": "ae",
    "saudi arabia": "sa", "riyadh": "sa", "jeddah": "sa",
    "egypt": "eg", "cairo": "eg"
}

def resolve_country(location: str) -> str:
    loc = location.lower()
    for k, code in LOCATION_MAP.items():
        if k in loc:
            return code
    return None

async def scrape_bayt_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from Bayt (MENA)."""
    all_jobs = []
    
    country_code = resolve_country(location)
    if not country_code:
        return all_jobs
        
    logger.info(f"Scraping Bayt for '{keyword}' in '{location}'")
    
    keywords_slug = urllib.parse.quote_plus(keyword)
    url = f"https://www.bayt.com/en/{country_code}/jobs/{keywords_slug}-jobs/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=20.0)
            if resp.status_code == 404:
                return all_jobs
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("li[data-js-job]")
            if not cards:
                cards = soup.select("div.has-pointer-d")
                
            for card in cards[:max_results]:
                title_el = card.select_one("h2.jb-title a, h2 a[data-js-aid]")
                if not title_el:
                    continue
                    
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job_url = f"https://www.bayt.com{href}" if href.startswith("/") else href
                
                # Try to get data-job-id if possible, else use URL
                job_id = card.get("data-job-id", f"bayt_{title}")
                if not job_id.startswith("bayt_"):
                    job_id = f"bayt_{job_id}"
                
                company_el = card.select_one("b.jb-company, span[data-js-aid='jobCompany']")
                company = company_el.get_text(strip=True) if company_el else "Unknown Company"
                
                loc_el = card.select_one("span.jb-loc, span[data-js-aid='jobLocation']")
                loc = loc_el.get_text(strip=True) if loc_el else location
                
                date_el = card.select_one("span.jb-date, time")
                posted_date = date_el.get("datetime", date_el.get_text(strip=True)) if date_el else ""
                
                job = Job(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    job_url=job_url,
                    posted_date=posted_date,
                    source="Bayt"
                )
                all_jobs.append(job)
    except Exception as e:
        logger.error(f"Error scraping Bayt: {e}")
        
    logger.info(f"Bayt found {len(all_jobs)} jobs.")
    return all_jobs
