import json
import os
import urllib.parse
import requests
from typing import List, Dict, Any
from models.job import Job
from sources.base import SourceAdapter

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

ROLES = [
    "software engineer", "SDE", "SDE I", "backend engineer", "python developer",
    "python engineer", "AI engineer", "ML engineer", "machine learning engineer",
    "data engineer", "data scientist", "SRE", "DevOps engineer", "cloud engineer",
    "platform engineer", "applied scientist", "GenAI engineer", "LLM engineer",
    "full stack engineer", "SDET", "automation engineer", "systems engineer",
]

EXP_QUALIFIERS = ['"new grad"', '"entry level"', '"0-1 years"', '"fresher"', '"2026"', ""]

ATS_SITES = [
    "site:boards.greenhouse.io",
    "site:jobs.lever.co",
    "site:ashbyhq.com",
]


def load_searxng_host() -> str:
    path = "config/sources.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f).get("searxng_host", "http://localhost:8080")
    return "http://localhost:8080"


class SearXNGAdapter(SourceAdapter):
    def __init__(self):
        self.host = load_searxng_host()
        self.available = None  # None = untested

    @property
    def source_name(self) -> str:
        return "SearXNG"

    def _check_available(self) -> bool:
        if self.available is not None:
            return self.available
        try:
            res = requests.get(f"{self.host}/", timeout=3)
            self.available = res.status_code < 500
        except Exception:
            self.available = False
        if not self.available:
            print(f"  [SearXNG] WARNING: SearXNG not reachable at {self.host}. Skipping.")
        return self.available

    def generate_queries(self) -> List[str]:
        queries = set()
        for role in ROLES:
            # Basic India role queries
            queries.add(f'"{role}" India')
            # ATS site queries
            for site in ATS_SITES:
                queries.add(f'{site} "{role}" India')
            # With experience qualifiers
            for qual in EXP_QUALIFIERS:
                if qual:
                    queries.add(f'"{role}" India {qual}')
        return list(queries)

    def _search_one(self, query: str) -> List[Dict[str, Any]]:
        encoded = urllib.parse.quote(query)
        url = f"{self.host}/search?q={encoded}&format=json&language=en&time_range=month"
        try:
            res = requests.get(url, headers=HEADERS, timeout=5)
            if res.status_code != 200:
                return []
            data = res.json()
            results = []
            for r in data.get("results", []):
                result_url = r.get("url", "")
                # Only ATS job URLs
                if any(d in result_url for d in ["greenhouse.io", "lever.co", "ashbyhq.com",
                                                   "amazon.jobs", "careers.microsoft.com",
                                                   "careers.google.com"]):
                    results.append({
                        "title": r.get("title", ""),
                        "url": result_url,
                        "content": r.get("content", ""),
                        "_query": query
                    })
            return results
        except Exception:
            return []

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        if not self._check_available():
            return []

        queries = self.generate_queries()
        print(f"  [SearXNG] Executing {len(queries)} queries...")
        seen_urls = set()
        all_results = []

        for q in queries:
            for r in self._search_one(q):
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)

        print(f"  [SearXNG] Discovered {len(all_results)} unique ATS URLs")
        return all_results

    def normalize(self, raw: Dict[str, Any]) -> Job:
        url = raw.get("url", "")
        title = raw.get("title", "Software Engineer")
        content = raw.get("content", "")

        # Attempt to infer company from URL
        company = "Unknown"
        if "greenhouse.io/embed/job_app" in url or "boards.greenhouse.io" in url:
            parts = url.split("/")
            company = parts[4].replace("-", " ").title() if len(parts) > 4 else "Unknown"
        elif "lever.co" in url:
            parts = url.split("/")
            company = parts[3].replace("-", " ").title() if len(parts) > 3 else "Unknown"
        elif "ashbyhq.com" in url:
            parts = url.split("/")
            company = parts[3].replace("-", " ").title() if len(parts) > 3 else "Unknown"

        return Job(
            source=self.source_name,
            source_job_id=f"sx_{abs(hash(url))}",
            source_url=url,
            canonical_url=url,
            apply_url=url,
            company=company,
            company_normalized=company.lower().strip(),
            company_type="UNKNOWN",  # Will be classified by company classifier
            title=title,
            title_normalized=title.lower(),
            description=content,
            qualifications=content,
            location="",  # Unknown — will be verified by location classifier
            country="",
            city="",
            category="Software Engineering",
            raw_source_data=raw,
            extraction_method="SearXNG"
        )
