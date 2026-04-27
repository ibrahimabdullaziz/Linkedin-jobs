import httpx
import urllib.parse
from typing import List
from loguru import logger
from models.job import Job

async def scrape_himalayas_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from Himalayas (remote jobs)."""
    all_jobs = []
    logger.info(f"Scraping Himalayas for '{keyword}'")
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://himalayas.app/jobs/api?search={encoded_keyword}&limit={max_results}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            
            jobs = data.get("jobs", [])
            for item in jobs[:max_results]:
                job_id = f"himalayas_{item.get('id')}"
                title = item.get("title", "Unknown Title")
                company = item.get("companyName", "Unknown Company")
                loc = item.get("locationRestrictions", "Remote")
                if isinstance(loc, list):
                    loc = ", ".join(loc)
                job_url = item.get("applicationLink", item.get("himalayasLink", ""))
                posted_date = str(item.get("pubDate", ""))
                
                job = Job(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    job_url=job_url,
                    posted_date=posted_date,
                    source="Himalayas"
                )
                all_jobs.append(job)
    except Exception as e:
        logger.error(f"Error scraping Himalayas: {e}")
        
    logger.info(f"Himalayas found {len(all_jobs)} jobs.")
    return all_jobs
