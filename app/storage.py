"""Job storage using SQLite."""
import sqlite3
import json
from typing import Optional
from app.models import Job, JobStatus


class JobStorage:
    """Simple SQLite-based job storage."""
    
    def __init__(self, db_path: str = "jobs.db"):
        """Initialize the storage with SQLite database."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                description TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def create_job(self, job_id: str) -> Job:
        """Create a new job with queued status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (job_id, status)
            VALUES (?, ?)
        """, (job_id, JobStatus.QUEUED.value))
        conn.commit()
        conn.close()
        return Job(job_id=job_id, status=JobStatus.QUEUED)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT job_id, status, description, error
            FROM jobs
            WHERE job_id = ?
        """, (job_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        return Job(
            job_id=row[0],
            status=JobStatus(row[1]),
            description=row[2],
            error=row[3]
        )
    
    def update_job_status(self, job_id: str, status: JobStatus, 
                         description: Optional[str] = None,
                         error: Optional[str] = None):
        """Update job status and optionally description/error."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE jobs
            SET status = ?, description = ?, error = ?, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        """, (status.value, description, error, job_id))
        conn.commit()
        conn.close()


# Global storage instance
storage = JobStorage()

