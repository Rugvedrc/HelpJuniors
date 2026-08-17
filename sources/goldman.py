import requests
from typing import List, Dict, Any, Tuple
from models.job import Job
from sources.base import SourceAdapter

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

# Finance companies that use SmartRecruiters as their ATS
# Format: (SmartRecruiters company ID, display name)
FINANCE_COMPANIES: List[Tuple[str, str]] = [
    ("GoldmanSachs", "Goldman Sachs"),
    ("JPMorganChase", "JP Morgan"),
    ("MorganStanley", "Morgan Stanley"),
    ("deshaw", "DE Shaw"),
]


class FinanceTechAdapter(SourceAdapter):
    """
    Fetches jobs from Goldman Sachs, JP Morgan, Morgan Stanley, DE Shaw
    via SmartRecruiters public API (no auth required).
    Endpoint: https://api.smartrecruiters.com/v1/companies/{id}/postings
    Filters by country=IN (India).
    """

    @property
    def source_name(self) -> str:
        return "Finance Tech (Goldman/JPM/MS/DE Shaw)"

    def _fetch_one_company(self, sr_id: str, company_name: str) -> List[Dict[str, Any]]:
        url = f"https://api.smartrecruiters.com/v1/companies/{sr_id}/postings"
        params = {"country": "IN", "limit": 100, "offset": 0}
        results = []

        while True:
            try:
                res = requests.get(url, params=params, headers=HEADERS, timeout=15)
                if res.status_code == 404:
                    print(f"    [FinanceTech] {company_name}: Not found on SmartRecruiters (404)")
                    break
                if res.status_code != 200:
                    print(f"    [FinanceTech] {company_name}: HTTP {res.status_code}")
                    break
                data = res.json()
                jobs = data.get("content", [])
                if not jobs:
                    break
                for j in jobs:
                    j["_company_name"] = company_name
                    j["_sr_id"] = sr_id
                results.extend(jobs)

                total = data.get("totalFound", 0)
                params["offset"] += 100
                if params["offset"] >= total or params["offset"] >= 1000:
                    break
            except Exception as e:
                print(f"    [FinanceTech] {company_name}: Error — {e}")
                break

        return results

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        print(f"  [Finance Tech] Fetching from Goldman Sachs, JP Morgan, Morgan Stanley, DE Shaw...")
        all_jobs = []
        for sr_id, company_name in FINANCE_COMPANIES:
            jobs = self._fetch_one_company(sr_id, company_name)
            print(f"    [FinanceTech] {company_name}: {len(jobs)} jobs")
            all_jobs.extend(jobs)
        print(f"  [Finance Tech] Raw jobs fetched: {len(all_jobs)}")
        return all_jobs

    def normalize(self, j: Dict[str, Any]) -> Job:
        company = j.get("_company_name", "Goldman Sachs")
        job_id = j.get("id", "")
        title = j.get("name", "").strip()

        location_obj = j.get("location", {})
        city = location_obj.get("city", "") if isinstance(location_obj, dict) else ""
        location = f"{city}, India" if city else "India"

        job_url = j.get("ref", "")
        dept_obj = j.get("department", {})
        dept = dept_obj.get("label", "Engineering") if isinstance(dept_obj, dict) else "Engineering"

        return Job(
            source=self.source_name,
            source_job_id=f"sr_{job_id}",
            source_url=job_url,
            canonical_url=job_url,
            apply_url=job_url,
            company=company,
            company_normalized=company.lower().strip(),
            company_type="PRODUCT",
            title=title,
            title_normalized=title.lower(),
            description="",
            qualifications="",
            location=location,
            country="IN",
            city=city or "India",
            category=dept,
            date_posted=j.get("createdOn", ""),
            raw_source_data=j,
            extraction_method="SmartRecruiters API"
        )
