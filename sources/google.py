import requests
from typing import List, Dict, Any
from models.job import Job
from sources.base import SourceAdapter

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*"
}

GOOGLE_QUERIES = [
    "software engineer", "SDE", "backend engineer", "machine learning engineer",
    "data engineer", "site reliability engineer", "AI engineer", "research engineer",
    "cloud engineer", "devops engineer", "new grad", "university graduate", "2026",
    "applied scientist", "research scientist", "platform engineer", "llm", "genai"
]


class GoogleAdapter(SourceAdapter):
    """
    Fetches jobs from Google Careers official API.
    Endpoint: https://careers.google.com/api/jobs/search/
    Filters by location=India. Deduplicates by job ID across multiple queries.
    """

    @property
    def source_name(self) -> str:
        return "Google Careers"

    def _fetch_one_query(self, query: str) -> List[Dict[str, Any]]:
        url = "https://careers.google.com/api/jobs/search/"
        results = []
        page = 1

        while True:
            params = {
                "q": query,
                "location": "India",
                "page_size": 20,
                "page": page,
            }
            try:
                res = requests.get(url, params=params, headers=HEADERS, timeout=12)
                if res.status_code != 200:
                    break
                data = res.json()
                jobs = data.get("jobs", [])
                if not jobs:
                    break
                for j in jobs:
                    j["_query"] = query
                results.extend(jobs)
                count = data.get("count", 0)
                if page * 20 >= count or page >= 10:
                    break
                page += 1
            except Exception as e:
                print(f"    [Google Careers] Query '{query}': Error — {e}")
                break

        return results

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        print(f"  [Google Careers] Fetching jobs from Google Careers API...")
        seen_ids = set()
        all_results = []

        for query in GOOGLE_QUERIES:
            jobs = self._fetch_one_query(query)
            for j in jobs:
                job_id = j.get("id", j.get("job_id", ""))
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    all_results.append(j)

        print(f"  [Google Careers] Unique jobs fetched: {len(all_results)}")
        return all_results

    def normalize(self, j: Dict[str, Any]) -> Job:
        job_id = j.get("id", j.get("job_id", ""))
        title = j.get("title", "").strip()
        locations = j.get("locations", [])
        location = locations[0] if locations else "India"

        apply_url = j.get("apply_url", "")
        job_url = f"https://careers.google.com/jobs/results/{job_id}" if job_id else apply_url

        description = j.get("description", "")
        qualifications = j.get("qualifications", j.get("minimum_qualifications", ""))
        preferred = j.get("preferred_qualifications", "")
        full_text = f"{qualifications} {preferred} {description}"

        return Job(
            source=self.source_name,
            source_job_id=f"goog_{job_id}",
            source_url=job_url,
            canonical_url=job_url,
            apply_url=apply_url or job_url,
            company="Google",
            company_normalized="google",
            company_type="PRODUCT",
            title=title,
            title_normalized=title.lower(),
            description=description[:800],
            qualifications=full_text,
            preferred_qualifications=preferred,
            location=location,
            country="IN",
            city=location.split(",")[0].strip() if "," in location else location,
            category=j.get("category", "Software Engineering"),
            date_posted=j.get("modified", ""),
            raw_source_data=j,
            extraction_method="Google Careers API"
        )
