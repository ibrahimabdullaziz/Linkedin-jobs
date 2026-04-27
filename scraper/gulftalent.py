import httpx
import urllib.parse
from bs4 import BeautifulSoup
from typing import List
from loguru import logger
from models.job import Job

COUNTRY_MAP = {
    "uae": "united-arab-emirates", "united arab emirates": "united-arab-emirates", "dubai": "united-arab-emirates",
    "saudi arabia": "saudi-arabia", "riyadh": "saudi-arabia", "jeddah": "saudi-arabia",
    "egypt": "egypt", "cairo": "egypt"
}

def resolve_country(location: str) -> str:
    loc = location.lower()
    for k, slug in COUNTRY_MAP.items():
        if k in loc:
            return slug
    return None

async def scrape_gulftalent_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from GulfTalent."""
    all_jobs = []
    
    country_slug = resolve_country(location)
    if not country_slug:
        return all_jobs
        
    logger.info(f"Scraping GulfTalent for '{keyword}' in '{location}'")
    
    url = f"https://www.gulftalent.com/jobs/in-{country_slug}/all-industries/all-functions/1/"
    params = {"q": keyword}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers, timeout=20.0)
            if resp.status_code in (404, 403):
                return all_jobs
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.job_listing, article.job-listing, div[class*='job-item']")
            if not cards:
                cards = soup.select("div.listing")
                
            for card in cards[:max_results]:
                title_el = card.select_one("h3 a, h2 a, a.job-title, a[class*='title']")
                if not title_el:
                    continue
                    
                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                job_url = f"https://www.gulftalent.com{href}" if href.startswith("/") else href
                
                job_id = f"gulftalent_{title.replace(' ', '_')}"
                
                company_el = card.select_one("span.company, div.company, a[class*='company']")
                company = company_el.get_text(strip=True) if company_el else "Unknown Company"
                
                loc_el = card.select_one("span.location, div.location, span[class*='location']")
                loc = loc_el.get_text(strip=True) if loc_el else location
                
                date_el = card.select_one("span.date, time, span[class*='date']")
                posted_date = date_el.get("datetime", date_el.get_text(strip=True)) if date_el else ""
                
                job = Job(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    job_url=job_url,
                    posted_date=posted_date,
                    source="GulfTalent"
                )
                all_jobs.append(job)
    except Exception as e:
        logger.error(f"Error scraping GulfTalent: {e}")
        
    logger.info(f"GulfTalent found {len(all_jobs)} jobs.")
    return all_jobs
