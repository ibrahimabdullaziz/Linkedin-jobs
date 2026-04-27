import sqlite3
from typing import List, Optional
from loguru import logger
from models.job import Job
from config.settings import DB_PATH

class JobRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes the database schema if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        company TEXT NOT NULL,
                        location TEXT,
                        job_url TEXT NOT NULL,
                        posted_date TEXT,
                        source TEXT DEFAULT 'LinkedIn',
                        scraped_at TEXT NOT NULL DEFAULT (datetime('now')),
                        sent_to_tg INTEGER NOT NULL DEFAULT 0
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_scraped_at ON jobs(scraped_at)")
                conn.commit()
                logger.debug("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def insert_job(self, job: Job) -> bool:
        """
        Inserts a new job into the database.
        Returns True if the job was inserted (it's new), False if it already existed.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO jobs (job_id, title, company, location, job_url, posted_date, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (job.job_id, job.title, job.company, job.location, job.job_url, job.posted_date, getattr(job, 'source', 'LinkedIn')))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Job ID already exists
            return False
        except Exception as e:
            logger.error(f"Error inserting job {job.job_id}: {e}")
            return False

    def mark_as_sent(self, job_id: str) -> None:
        """Marks a job as successfully sent to Telegram."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE jobs SET sent_to_tg = 1 WHERE job_id = ?", (job_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error marking job {job_id} as sent: {e}")

    def get_unsent_jobs(self) -> List[Job]:
        """Retrieves jobs that haven't been sent to Telegram yet."""
        jobs = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM jobs WHERE sent_to_tg = 0")
                rows = cursor.fetchall()
                for row in rows:
                    job = Job(
                        job_id=row['job_id'],
                        title=row['title'],
                        company=row['company'],
                        location=row['location'],
                        job_url=row['job_url'],
                        posted_date=row['posted_date'],
                        source=row['source'] if 'source' in row.keys() else 'LinkedIn'
                    )
                    jobs.append(job)
        except Exception as e:
            logger.error(f"Error retrieving unsent jobs: {e}")
        return jobs

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Removes job entries older than the specified number of days."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM jobs WHERE scraped_at < datetime('now', '-{days} days')")
                deleted_rows = cursor.rowcount
                conn.commit()
                return deleted_rows
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0
