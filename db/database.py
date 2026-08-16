import sqlite3
import pandas as pd
from typing import List
from datetime import datetime
from models.job import Job

DB_FILE = "jobs_india.db"

def init_db(reset: bool = False):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if reset:
        cursor.execute("DROP TABLE IF EXISTS jobs;")
        
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        source_job_id TEXT PRIMARY KEY,
        source TEXT,
        source_url TEXT,
        canonical_url TEXT,
        apply_url TEXT,
        company TEXT,
        company_normalized TEXT,
        company_type TEXT,
        title TEXT,
        title_normalized TEXT,
        description TEXT,
        responsibilities TEXT,
        qualifications TEXT,
        preferred_qualifications TEXT,
        location TEXT,
        country TEXT,
        city TEXT,
        remote_type TEXT,
        employment_type TEXT,
        date_posted TEXT,
        min_experience_years REAL,
        max_experience_years REAL,
        experience_text TEXT,
        skills TEXT,
        category TEXT,
        sub_category TEXT,
        active_status TEXT,
        eligibility_status INTEGER,
        rejection_reason TEXT,
        relevance_score REAL,
        confidence_score REAL,
        discovered_at TEXT
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_reads (
        chat_id INTEGER,
        source_job_id TEXT,
        read_at TEXT,
        PRIMARY KEY (chat_id, source_job_id)
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_eligibility ON jobs(eligibility_status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON jobs(city);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_relevance ON jobs(relevance_score);")
    conn.commit()
    conn.close()

def save_jobs_to_db(jobs: List[Job]):
    init_db(reset=False)  # Retain job_reads table
    conn = sqlite3.connect(DB_FILE)
    
    rows = []
    for j in jobs:
        rows.append({
            "source_job_id": j.source_job_id,
            "source": j.source,
            "source_url": j.source_url,
            "canonical_url": j.canonical_url,
            "apply_url": j.apply_url,
            "company": j.company,
            "company_normalized": j.company_normalized,
            "company_type": j.company_type,
            "title": j.title,
            "title_normalized": j.title_normalized,
            "description": j.description,
            "responsibilities": j.responsibilities,
            "qualifications": j.qualifications,
            "preferred_qualifications": j.preferred_qualifications,
            "location": j.location,
            "country": j.country,
            "city": j.city,
            "remote_type": j.remote_type,
            "employment_type": j.employment_type,
            "date_posted": j.date_posted,
            "min_experience_years": j.min_experience_years,
            "max_experience_years": j.max_experience_years,
            "experience_text": j.experience_text,
            "skills": ", ".join(j.skills),
            "category": j.category,
            "sub_category": j.sub_category,
            "active_status": j.active_status,
            "eligibility_status": 1 if j.eligibility_status else 0,
            "rejection_reason": j.rejection_reason,
            "relevance_score": j.relevance_score,
            "confidence_score": j.confidence_score,
            "discovered_at": j.discovered_at
        })
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_sql("jobs", conn, if_exists="replace", index=False)
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eligibility ON jobs(eligibility_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON jobs(city);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relevance ON jobs(relevance_score);")
        conn.commit()
        
    conn.close()

def get_eligible_jobs_from_db() -> pd.DataFrame:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM jobs WHERE eligibility_status = 1 ORDER BY relevance_score DESC", conn)
    conn.close()
    return df

def get_unread_eligible_jobs(chat_id: int) -> pd.DataFrame:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT j.* FROM jobs j
        LEFT JOIN job_reads r ON j.source_job_id = r.source_job_id AND r.chat_id = ?
        WHERE j.eligibility_status = 1 AND r.source_job_id IS NULL
        ORDER BY j.relevance_score DESC
    """
    df = pd.read_sql_query(query, conn, params=(chat_id,))
    conn.close()
    return df

def mark_all_jobs_read(chat_id: int) -> int:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    cursor.execute("""
        INSERT OR IGNORE INTO job_reads (chat_id, source_job_id, read_at)
        SELECT ?, source_job_id, ? FROM jobs WHERE eligibility_status = 1
    """, (chat_id, now_str))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

def get_quarantined_jobs_from_db() -> pd.DataFrame:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM jobs WHERE company_type = 'UNKNOWN' ORDER BY discovered_at DESC", conn)
    conn.close()
    return df

def get_rejected_jobs_from_db() -> pd.DataFrame:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM jobs WHERE eligibility_status = 0 ORDER BY discovered_at DESC", conn)
    conn.close()
    return df
