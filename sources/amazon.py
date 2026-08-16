import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.job import Job
from sources.base import SourceAdapter

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def clean_html(text: str) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()

class AmazonAdapter(SourceAdapter):
    def __init__(self, queries: List[str] = None):
        self.queries = queries or ["SDE", "software engineer", "developer", "applied scientist", "data engineer", "intern", "graduate", "2026"]

    @property
    def source_name(self) -> str:
        return "Amazon"

    def fetch_query(self, query: str) -> Dict[str, Dict[str, Any]]:
        url = "https://www.amazon.jobs/en/search.json"
        offset = 0
        limit = 100
        matched = {}
        while True:
            params = {"base_query": query, "country[]": "IND", "result_limit": limit, "offset": offset, "sort": "recent"}
            try:
                res = requests.get(url, params=params, headers=HEADERS, timeout=6)
                if res.status_code != 200:
                    break
                data = res.json()
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                for j in jobs:
                    job_id = j.get("id_icims") or j.get("id")
                    if job_id:
                        matched[job_id] = j
                offset += limit
                if offset >= data.get("hits", 0) or offset >= 50:
                    break
            except Exception:
                break
        return matched

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        raw_dict = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self.fetch_query, q): q for q in self.queries}
            for future in as_completed(futures):
                try:
                    raw_dict.update(future.result())
                except Exception:
                    pass
        return list(raw_dict.values())

    def normalize(self, j: Dict[str, Any]) -> Job:
        job_id = str(j.get("id_icims") or j.get("id"))
        url = f"https://www.amazon.jobs{j.get('job_path', '')}"
        loc = j.get("location", "India")
        city = loc.split(",")[2].strip() if len(loc.split(",")) >= 3 else loc

        basic = clean_html(j.get("basic_qualifications"))
        pref = clean_html(j.get("preferred_qualifications"))
        desc = clean_html(j.get("description_short"))

        return Job(
            source=self.source_name,
            source_job_id=f"amz_{job_id}",
            source_url=url,
            canonical_url=url,
            apply_url=url,
            company="Amazon",
            company_normalized="amazon",
            company_type="PRODUCT",
            title=j.get("title", "").strip(),
            title_normalized=j.get("title", "").strip().lower(),
            description=desc,
            qualifications=basic,
            preferred_qualifications=pref,
            location=loc,
            country="India",
            city=city,
            category=j.get("job_category", "Software Development"),
            date_posted=j.get("posted_date"),
            raw_source_data=j,
            extraction_method="API"
        )
