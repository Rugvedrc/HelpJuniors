import json
import os
import requests
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
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


def load_ashby_slugs() -> List[Dict[str, str]]:
    path = "config/companies.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("ashby_slugs", [])
    return []


class AshbyAdapter(SourceAdapter):
    def __init__(self):
        self.ashby_slugs = load_ashby_slugs()

    @property
    def source_name(self) -> str:
        return "Ashby"

    def _fetch_one(self, item: Dict[str, str]) -> List[Dict[str, Any]]:
        slug = item["slug"]
        company = item["company"]
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 404:
                return []
            if res.status_code != 200:
                print(f"    [Ashby] {company}: HTTP {res.status_code}")
                return []
            data = res.json()
            jobs = data.get("jobs", [])
            for j in jobs:
                j["_company_name"] = company
                j["_ashby_slug"] = slug
            return jobs
        except Exception as e:
            print(f"    [Ashby] {company}: Error — {e}")
            return []

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        all_jobs = []
        print(f"  [Ashby] Fetching from {len(self.ashby_slugs)} company boards...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._fetch_one, item): item for item in self.ashby_slugs}
            for future in as_completed(futures):
                try:
                    all_jobs.extend(future.result())
                except Exception:
                    pass
        print(f"  [Ashby] Raw jobs fetched: {len(all_jobs)}")
        return all_jobs

    def normalize(self, j: Dict[str, Any]) -> Job:
        company = j.get("_company_name", "Unknown")
        job_id = j.get("id", j.get("jobId", ""))
        url = j.get("jobUrl", j.get("applyUrl", ""))

        location = j.get("locationName", j.get("location", ""))
        city = location.split(",")[0].strip() if location else ""

        desc = clean_html(j.get("descriptionHtml", "")) or j.get("descriptionPlain", "")
        team = j.get("departmentName", j.get("teamName", "Engineering"))

        return Job(
            source=self.source_name,
            source_job_id=f"ab_{job_id}",
            source_url=url,
            canonical_url=url,
            apply_url=url,
            company=company,
            company_normalized=company.lower().strip(),
            company_type="PRODUCT",
            title=j.get("title", "").strip(),
            title_normalized=j.get("title", "").strip().lower(),
            description=desc[:800],
            qualifications=desc,
            location=location,
            country="",
            city=city,
            category=team,
            date_posted="",
            raw_source_data={k: v for k, v in j.items() if k not in ("descriptionHtml",)},
            extraction_method="Ashby API"
        )
