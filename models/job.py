from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    job_id: str
    title: str
    company: str
    location: str
    job_url: str
    posted_date: str
    source: str = "LinkedIn"

    def to_telegram_markdown(self) -> str:
        """
        Formats the job entry into a Telegram MarkdownV2 compatible string.
        Escapes required characters properly.
        """
        # Telegram MarkdownV2 requires escaping the following characters:
        # _ * [ ] ( ) ~ ` > # + - = | { } . !
        
        def escape_md(text: str) -> str:
            if not text:
                return ""
            escape_chars = r"_*[]()~`>#+-=|{}.!"
            for char in escape_chars:
                text = text.replace(char, f"\\{char}")
            return text

        title_esc = escape_md(self.title)
        company_esc = escape_md(self.company)
        location_esc = escape_md(self.location)
        date_esc = escape_md(self.posted_date)
        
        # Build the new cleaner, bolder message string
        msg = f"*{title_esc}*\n"
        msg += f"🏢 {company_esc}\n"
        msg += f"📍 {location_esc}\n"
        msg += f"🕒 {date_esc}\n"
        msg += f"📌 via {escape_md(self.source)}\n\n"
        msg += f"[➡️ Apply Here]({self.job_url})"
        
        return msg
