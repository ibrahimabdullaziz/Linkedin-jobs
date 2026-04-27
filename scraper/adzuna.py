import httpx
from typing import List
from loguru import logger
from models.job import Job
from config.settings import ADZUNA_APP_ID, ADZUNA_APP_KEY

COUNTRY_MAP = {
    "united arab emirates": "ae",
    "uae": "ae",
    "saudi arabia": "sa",
    "saudi": "sa",
    "ksa": "sa",
    "egypt": None, # adzuna doesn't support egypt natively
}

def resolve_country(location: str) -> str:
    loc = location.lower()
    for k, v in COUNTRY_MAP.items():
        if k in loc:
            return v
    return None

async def scrape_adzuna_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from Adzuna."""
    all_jobs = []
    
    country = resolve_country(location)
    if not country:
        logger.debug(f"Skipping Adzuna for location {location} (unsupported)")
        return all_jobs
        
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("Adzuna keys missing, skipping Adzuna.")
        return all_jobs

    logger.info(f"Scraping Adzuna for '{keyword}' in '{location}' ({country})")
    
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": max_results,
        "what": keyword,
        "content-type": "application/json",
        "max_days_old": 2
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            
            jobs = data.get("results", [])
            for item in jobs:
                job_id = f"adzuna_{item.get('id')}"
                title = item.get("title", "Unknown Title")
                company = item.get("company", {}).get("display_name", "Unknown Company")
                loc = item.get("location", {}).get("display_name", location)
                job_url = item.get("redirect_url", "")
                posted_date = item.get("created", "")
                
                job = Job(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    job_url=job_url,
                    posted_date=posted_date,
                    source="Adzuna"
                )
                all_jobs.append(job)
    except Exception as e:
        logger.error(f"Error scraping Adzuna: {e}")
        
    logger.info(f"Adzuna found {len(all_jobs)} jobs.")
    return all_jobs
