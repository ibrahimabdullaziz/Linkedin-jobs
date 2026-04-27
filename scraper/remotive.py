import httpx
import urllib.parse
from typing import List
from loguru import logger
from models.job import Job

async def scrape_remotive_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from remotive (remote jobs). Ignoring location as it's remote first."""
    all_jobs = []
    logger.info(f"Scraping Remotive for '{keyword}'")
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://remotive.com/api/remote-jobs?search={encoded_keyword}&limit={max_results}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            
            jobs = data.get("jobs", [])
            for item in jobs[:max_results]:
                job_id = f"remotive_{item.get('id')}"
                title = item.get("title", "Unknown Title")
                company = item.get("company_name", "Unknown Company")
                loc = item.get("candidate_required_location", "Remote")
                job_url = item.get("url", "")
                posted_date = item.get("publication_date", "").split("T")[0]
                
                job = Job(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    job_url=job_url,
                    posted_date=posted_date,
                    source="Remotive"
                )
                all_jobs.append(job)
    except Exception as e:
        logger.error(f"Error scraping Remotive: {e}")
        
    logger.info(f"Remotive found {len(all_jobs)} jobs.")
    return all_jobs
