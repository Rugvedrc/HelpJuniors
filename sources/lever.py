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


def load_lever_slugs() -> List[Dict[str, str]]:
    path = "config/companies.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("lever_slugs", [])
    return []


class LeverAdapter(SourceAdapter):
    def __init__(self):
        self.lever_slugs = load_lever_slugs()

    @property
    def source_name(self) -> str:
        return "Lever"

    def _fetch_one(self, item: Dict[str, str]) -> List[Dict[str, Any]]:
        slug = item["slug"]
        company = item["company"]
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 404:
                return []
            if res.status_code != 200:
                print(f"    [Lever] {company}: HTTP {res.status_code}")
                return []
            jobs = res.json()
            if not isinstance(jobs, list):
                return []
            for j in jobs:
                j["_company_name"] = company
                j["_lever_slug"] = slug
            return jobs
        except Exception as e:
            print(f"    [Lever] {company}: Error — {e}")
            return []

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        all_jobs = []
        print(f"  [Lever] Fetching from {len(self.lever_slugs)} company boards...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._fetch_one, item): item for item in self.lever_slugs}
            for future in as_completed(futures):
                try:
                    all_jobs.extend(future.result())
                except Exception:
                    pass
        print(f"  [Lever] Raw jobs fetched: {len(all_jobs)}")
        return all_jobs

    def normalize(self, j: Dict[str, Any]) -> Job:
        company = j.get("_company_name", "Unknown")
        job_id = j.get("id", "")
        url = j.get("hostedUrl", j.get("applyUrl", ""))

        # Location
        categories = j.get("categories", {})
        location = categories.get("location", "")
        team = categories.get("team", "Engineering")
        city = location.split(",")[0].strip() if location else ""

        # Description text
        description_raw = j.get("descriptionPlain", "") or clean_html(j.get("description", ""))
        lists = j.get("lists", [])
        qualifications = ""
        for lst in lists:
            qualifications += lst.get("text", "") + "\n" + clean_html(lst.get("content", "")) + "\n"

        return Job(
            source=self.source_name,
            source_job_id=f"lv_{job_id}",
            source_url=url,
            canonical_url=url,
            apply_url=j.get("applyUrl", url),
            company=company,
            company_normalized=company.lower().strip(),
            company_type="PRODUCT",
            title=j.get("text", "").strip(),
            title_normalized=j.get("text", "").strip().lower(),
            description=description_raw[:800],
            qualifications=qualifications.strip() or description_raw,
            location=location,
            country="",
            city=city,
            category=team,
            date_posted="",
            raw_source_data={k: v for k, v in j.items() if k not in ("description",)},
            extraction_method="Lever API"
        )
