import asyncio
import urllib.parse
import httpx
from bs4 import BeautifulSoup
from typing import List
from loguru import logger
import random

from models.job import Job
from filters.date_filter import is_from_today
from config.settings import LINKEDIN_KEYWORDS

# Standard browser headers to avoid basic blocks
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def get_random_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

async def fetch_jobs_page(client: httpx.AsyncClient, keywords: str, location: str, start: int = 0) -> str:
    """Hits the LinkedIn Guest Jobs API endpoint."""
    encoded_keywords = urllib.parse.quote(keywords)
    encoded_location = urllib.parse.quote(location)
    
    # f_TPR=r86400 filters by past 24 hours
    url = (
        f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?"
        f"keywords={encoded_keywords}&location={encoded_location}&f_TPR=r86400&start={start}"
    )

    try:
        response = await client.get(url, headers=get_random_headers(), timeout=15.0)
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error scraping LinkedIn (Status {e.response.status_code}): {e}")
        return ""
    except Exception as e:
        logger.error(f"Request error scraping LinkedIn: {e}")
        return ""

def is_title_relevant(title: str) -> bool:
    title_lower = title.lower()
    keywords_lower = [k.lower() for k in LINKEDIN_KEYWORDS]
    
    # Accept if the title contains ANY of our target keywords
    for k in keywords_lower:
        if k in title_lower:
            return True
            
    # Also explicitly accept general software terms just to be safe
    general_terms = [ "developer", "programmer", "software", "backend", "frontend", "full stack", "tech lead", "architect", "qa", "tester"]
    for t in general_terms:
        if t in title_lower:
            return True
            
    return False

def parse_jobs(html: str) -> List[Job]:
    """Parses the HTML fragment returned by the Guest API."""
    jobs = []
    if not html:
        return jobs

    soup = BeautifulSoup(html, "lxml")
    job_cards = soup.find_all("li")

    for card in job_cards:
        try:
            # The base Job entity ID is usually in an attribute or URL
            job_div = card.find("div", class_="base-card")
            if not job_div:
                continue
            
            job_id = job_div.get("data-entity-urn", "").split(":")[-1]
            if not job_id:
                continue

            # Title
            title_elem = card.find("h3", class_="base-search-card__title")
            title = title_elem.text.strip() if title_elem else "Unknown Title"

            if not is_title_relevant(title):
                continue

            # Company
            company_elem = card.find("h4", class_="base-search-card__subtitle")
            company = company_elem.text.strip() if company_elem else "Unknown Company"

            # Location
            location_elem = card.find("span", class_="job-search-card__location")
            location = location_elem.text.strip() if location_elem else "Unknown Location"

            # Date
            date_elem = card.find("time")
            posted_date = date_elem.text.strip() if date_elem else ""

            # Apply date filter strictly on the client side just in case 'f_TPR' failed
            # If date format is totally unrecognized, the filter allows it to prevent misses.
            if posted_date and not is_from_today(posted_date):
                continue

            # URL
            url_elem = card.find("a", class_="base-card__full-link")
            job_url = url_elem["href"].split("?")[0] if url_elem and "href" in url_elem.attrs else f"https://www.linkedin.com/jobs/view/{job_id}"

            job = Job(
                job_id=job_id,
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                posted_date=posted_date
            )
            jobs.append(job)

        except Exception as e:
            logger.debug(f"Error parsing a job card: {e}")
            continue

    return jobs

async def scrape_linkedin_jobs(keyword: str, location: str, max_pages: int = 1) -> List[Job]:
    """
    Main scraping orchestration for LinkedIn.
    Scrapes multiple pages until no more jobs are found or max_pages is reached.
    """
    all_jobs = []
    logger.info(f"Scraping '{keyword}' in '{location}'")
    
    async with httpx.AsyncClient() as client:
        for page in range(max_pages):
            start_idx = page * 25 # LinkedIn API returns 25 results per page
            logger.debug(f"Fetching page {page + 1} (start={start_idx})...")
            
            html = await fetch_jobs_page(client, keyword, location, start=start_idx)
            if not html.strip():
                logger.debug("No more HTML returned. Ending pagination.")
                break
                
            jobs = parse_jobs(html)
            if not jobs:
                logger.debug("No valid jobs parsed from HTML fragment. Ending pagination.")
                break
                
            all_jobs.extend(jobs)
            
            # Respectful delay between pages
            if page < max_pages - 1:
                await asyncio.sleep(random.uniform(2.0, 4.0))

    logger.info(f"Scrape complete. Found {len(all_jobs)} today's jobs.")
    return all_jobs
