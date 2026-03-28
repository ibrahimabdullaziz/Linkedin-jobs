import re
from loguru import logger

def is_from_today(date_str: str) -> bool:
    """
    Checks if a relative date string from LinkedIn indicates the job was posted today/within 24 hours.
    LinkedIn typically uses formats like:
    - "Just now"
    - "1 minute ago"
    - "5 hours ago"
    - "Today"
    - "1 day ago" -> this might be 24-48 hours, so we cautiously include it or exclude it depending on strictness.
    - "2 days ago" -> exclude
    - Default/Fallback handling
    """
    if not date_str:
        return False

    date_str = date_str.lower().strip()

    # Always accept these exact phrases
    if "just now" in date_str or "today" in date_str:
        return True

    # Accept minutes and hours
    if "minute" in date_str or "hour" in date_str:
        return True

    # If it's strictly "1 day ago", we might want to include it, 
    # but "2 days ago" or "month" should definitely be filtered out.
    if re.search(r'\b1 day ago\b', date_str):
        return True 

    if "day" in date_str and not re.search(r'\b1 day ago\b', date_str):
        # 2 days, 3 days etc...
        return False
        
    if "week" in date_str or "month" in date_str or "year" in date_str:
        return False

    # If we don't recognize it, but the LinkedIn API `f_TPR` param sent it, 
    # we might lean towards accepting it, but better safe than noisy.
    logger.debug(f"Unrecognized date format, defaulting to accept: '{date_str}'")
    return True
