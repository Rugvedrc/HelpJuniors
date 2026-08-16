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


def load_tokens() -> List[Dict[str, str]]:
    path = "config/companies.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("greenhouse_tokens", [])
    return []


class GreenhouseAdapter(SourceAdapter):
    def __init__(self):
        self.board_tokens = load_tokens()

    @property
    def source_name(self) -> str:
        return "Greenhouse"

    def _fetch_one(self, item: Dict[str, str]) -> List[Dict[str, Any]]:
        token = item["token"]
        company = item["company"]
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 404:
                return []  # Company not on Greenhouse
            if res.status_code != 200:
                print(f"    [Greenhouse] {company}: HTTP {res.status_code}")
                return []
            data = res.json()
            jobs = data.get("jobs", [])
            for j in jobs:
                j["_company_name"] = company
                j["_source_token"] = token
            return jobs
        except Exception as e:
            print(f"    [Greenhouse] {company}: Error — {e}")
            return []

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        all_jobs = []
        print(f"  [Greenhouse] Fetching from {len(self.board_tokens)} company boards...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self._fetch_one, item): item for item in self.board_tokens}
            for future in as_completed(futures):
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception:
                    pass
        print(f"  [Greenhouse] Raw jobs fetched: {len(all_jobs)}")
        return all_jobs

    def normalize(self, j: Dict[str, Any]) -> Job:
        company = j.get("_company_name", "Unknown")
        location_obj = j.get("location", {})
        location = location_obj.get("name", "") if isinstance(location_obj, dict) else str(location_obj)
        city = location.split(",")[0].strip() if location else "India"

        content_html = j.get("content", "")
        full_text = clean_html(content_html)

        job_id = str(j.get("id", ""))
        url = j.get("absolute_url", "")
        departments = j.get("departments", [])
        dept = departments[0].get("name", "Engineering") if departments else "Engineering"

        return Job(
            source=self.source_name,
            source_job_id=f"gh_{job_id}",
            source_url=url,
            canonical_url=url,
            apply_url=url,
            company=company,
            company_normalized=company.lower().strip(),
            company_type="PRODUCT",  # All Greenhouse tokens are known product companies
            title=j.get("title", "").strip(),
            title_normalized=j.get("title", "").strip().lower(),
            description=full_text[:800],
            qualifications=full_text,
            location=location,
            country="",  # Will be verified by location classifier
            city=city,
            category=dept,
            date_posted=j.get("updated_at", "")[:10] if j.get("updated_at") else "",
            raw_source_data={k: v for k, v in j.items() if k not in ("content",)},
            extraction_method="Greenhouse API"
        )
