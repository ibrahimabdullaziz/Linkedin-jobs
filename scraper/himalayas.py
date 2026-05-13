import httpx
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List
from loguru import logger
from models.job import Job

async def scrape_himalayas_jobs(keyword: str, location: str, max_results: int = 20) -> List[Job]:
    """Scrape from Himalayas (remote jobs)."""
    all_jobs = []
    logger.debug(f"Scraping Himalayas for '{keyword}'")
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://himalayas.app/jobs/api?search={encoded_keyword}&limit={max_results}"
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=2)
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0)
            resp.raise_for_status()
            data = resp.json()
            
            jobs = data.get("jobs", [])
            for item in jobs[:max_results]:
                pub_date_raw = item.get("pubDate", "")
                
                # Filter: only keep jobs from the last 2 days
                if pub_date_raw:
                    try:
                        # pubDate can be ISO string or epoch timestamp
                        if isinstance(pub_date_raw, (int, float)):
                            pub_dt = datetime.fromtimestamp(pub_date_raw / 1000, tz=timezone.utc)
                        else:
                            pub_dt = datetime.fromisoformat(str(pub_date_raw).replace("Z", "+00:00"))
                        if pub_dt < cutoff:
                            continue
                    except (ValueError, TypeError, OSError):
                        pass  # Can't parse — include it to avoid missing jobs
                
                job_id = f"himalayas_{item.get('id')}"
                title = item.get("title", "Unknown Title")
                company = item.get("companyName", "Unknown Company")
                loc = item.get("locationRestrictions", "Remote")
                if isinstance(loc, list):
                    loc = ", ".join(loc)
                job_url = item.get("applicationLink", item.get("himalayasLink", ""))
                posted_date = str(pub_date_raw)
                
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
        
    logger.debug(f"Himalayas found {len(all_jobs)} recent jobs for '{keyword}'.")
    return all_jobs
