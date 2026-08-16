import hashlib
from typing import List, Tuple
from models.job import Job

def compute_job_fingerprint(job: Job) -> str:
    key = f"{job.company_normalized}_{job.title_normalized}_{job.city.lower()}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()

def deduplicate_jobs(jobs: List[Job]) -> Tuple[List[Job], int]:
    seen_ids = set()
    seen_urls = set()
    seen_fingerprints = set()

    unique_jobs: List[Job] = []
    duplicate_count = 0

    for j in jobs:
        if j.source_job_id in seen_ids:
            duplicate_count += 1
            continue
        if j.canonical_url in seen_urls:
            duplicate_count += 1
            continue
        fp = compute_job_fingerprint(j)
        if fp in seen_fingerprints:
            duplicate_count += 1
            continue

        seen_ids.add(j.source_job_id)
        seen_urls.add(j.canonical_url)
        seen_fingerprints.add(fp)
        unique_jobs.append(j)

    return unique_jobs, duplicate_count
