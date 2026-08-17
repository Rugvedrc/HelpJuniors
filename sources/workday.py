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
    "Accept": "application/json",
    "Content-Type": "application/json"
}


def clean_html(text: str) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()


# Configuration of official Workday-hosted enterprise career portals
DEFAULT_WORKDAY_SITES = [
    {"company": "Adobe", "host": "adobe.wd5.myworkdayjobs.com", "board": "external_experienced"},
    {"company": "Nvidia", "host": "nvidia.wd5.myworkdayjobs.com", "board": "NVIDIAExternalCareerSite"},
    {"company": "Salesforce", "host": "salesforce.wd12.myworkdayjobs.com", "board": "External_Career_Site"},
    {"company": "Target", "host": "target.wd5.myworkdayjobs.com", "board": "targetcareers"},
    {"company": "Autodesk", "host": "autodesk.wd1.myworkdayjobs.com", "board": "Ext"},
    {"company": "Workday", "host": "workday.wd5.myworkdayjobs.com", "board": "Workday"},
]


def load_workday_sites() -> List[Dict[str, str]]:
    path = "config/companies.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            sites = data.get("workday_sites", [])
            if sites:
                return sites
    return DEFAULT_WORKDAY_SITES


class WorkdayAdapter(SourceAdapter):
    """
    Direct official enterprise career portal adapter for companies using Workday CXS API.
    Fetches direct official postings straight from company careers portals (e.g. Adobe, Nvidia, Salesforce, Target, etc.).
    """
    def __init__(self):
        self.sites = load_workday_sites()

    @property
    def source_name(self) -> str:
        return "Workday Official Careers"

    def _fetch_company_jobs(self, item: Dict[str, str]) -> List[Dict[str, Any]]:
        company = item["company"]
        host = item["host"]
        board = item["board"]
        tenant = host.split(".")[0]
        url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"

        all_company_jobs = []
        offset = 0
        limit = 20

        while True:
            payload = {"limit": limit, "offset": offset, "searchText": "India"}
            try:
                res = requests.post(url, json=payload, headers=HEADERS, timeout=8)
                if res.status_code != 200:
                    break
                data = res.json()
                postings = data.get("jobPostings", [])
                if not postings:
                    break
                for p in postings:
                    p["_company_name"] = company
                    p["_host"] = host
                    all_company_jobs.append(p)
                offset += limit
                total = data.get("total", 0)
                if offset >= total or offset >= 1000:  # Full pagination
                    break
            except Exception as e:
                print(f"    [Workday Careers] {company}: Error — {e}")
                break

        return all_company_jobs

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        all_jobs = []
        print(f"  [Workday Official Careers] Fetching from {len(self.sites)} official enterprise career portals...")
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(self._fetch_company_jobs, item): item for item in self.sites}
            for future in as_completed(futures):
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception:
                    pass
        print(f"  [Workday Official Careers] Raw jobs fetched: {len(all_jobs)}")
        return all_jobs

    def normalize(self, j: Dict[str, Any]) -> Job:
        company = j.get("_company_name", "Unknown")
        host = j.get("_host", "")
        job_path = j.get("externalPath", "")
        canonical_url = f"https://{host}{job_path}" if job_path and host else ""

        bullet_fields = j.get("bulletFields", [])
        location = bullet_fields[0] if bullet_fields else "India"
        city = location.split(",")[0].strip() if "," in location else location

        title = j.get("title", "").strip()
        posted = j.get("postedOn", "")

        return Job(
            source=self.source_name,
            source_job_id=f"wd_{abs(hash(canonical_url or title))}",
            source_url=canonical_url,
            canonical_url=canonical_url,
            apply_url=canonical_url,
            company=company,
            company_normalized=company.lower().strip(),
            company_type="PRODUCT",  # Official enterprise career portal
            title=title,
            title_normalized=title.lower(),
            description=title,  # Standard snippet
            qualifications=title,
            location=location,
            country="",  # Location gate will verify
            city=city,
            category="Software Engineering",
            date_posted=posted,
            raw_source_data=j,
            extraction_method="Workday Official API"
        )
