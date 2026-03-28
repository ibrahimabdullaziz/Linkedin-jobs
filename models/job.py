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
        
        # Build the message string
        msg = f"📍 *New Job Match* 📍\n\n"
        msg += f"💼 *Role:* {title_esc}\n"
        msg += f"🏢 *Company:* {company_esc}\n"
        msg += f"🌍 *Location:* {location_esc}\n"
        msg += f"📅 *Posted:* {date_esc}\n\n"
        msg += f"[Apply on LinkedIn]({self.job_url})"
        
        return msg
