import httpx
from typing import List
from loguru import logger
from models.job import Job

async def scrape_arbeitnow_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from Arbeitnow."""
    all_jobs = []
    logger.info(f"Scraping Arbeitnow for '{keyword}'")
    
    url = "https://www.arbeitnow.com/api/job-board-api"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            
            jobs = data.get("data", [])
            count = 0
            for item in jobs:
                if count >= max_results:
                    break
                    
                title = item.get("title", "")
                # naive filter since API doesn't support search natively
                if keyword.lower() not in title.lower():
                    continue
                    
                job_id = f"arbeitnow_{item.get('slug')}"
                company = item.get("company_name", "Unknown Company")
                loc = item.get("location", "Remote")
                job_url = item.get("url", "")
                posted_date = str(item.get("created_at", ""))
                
                job = Job(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=loc,
                    job_url=job_url,
                    posted_date=posted_date,
                    source="Arbeitnow"
                )
                all_jobs.append(job)
                count += 1
    except Exception as e:
        logger.error(f"Error scraping Arbeitnow: {e}")
        
    logger.info(f"Arbeitnow found {len(all_jobs)} jobs.")
    return all_jobs
