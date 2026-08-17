import requests
from typing import List, Dict, Any
from models.job import Job
from sources.base import SourceAdapter

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

MS_QUERIES = [
    "software engineer", "SDE", "backend engineer", "machine learning",
    "AI engineer", "data engineer", "site reliability", "cloud engineer",
    "new grad", "university", "2026", "applied scientist", "devops",
    "platform engineer", "python developer", "llm", "generative ai"
]


class MicrosoftAdapter(SourceAdapter):
    """
    Fetches jobs from Microsoft Careers official JSON search API.
    Endpoint: https://gcsservices.careers.microsoft.com/search/api/v1/search
    Filters by country India. Deduplicates across queries by jobId.
    """

    @property
    def source_name(self) -> str:
        return "Microsoft Careers"

    def _fetch_one_query(self, query: str) -> List[Dict[str, Any]]:
        url = "https://gcsservices.careers.microsoft.com/search/api/v1/search"
        results = []
        page = 1

        while True:
            params = {
                "q": query,
                "l": "en_us",
                "pg": page,
                "pgSz": 20,
                "o": "Relevance",
                "flt": "true",
                "lc": "India"
            }
            try:
                res = requests.get(url, params=params, headers=HEADERS, timeout=12)
                if res.status_code != 200:
                    break
                data = res.json()
                op_result = data.get("operationResult", {}).get("result", {})
                jobs = op_result.get("jobs", [])
                if not jobs:
                    break
                for j in jobs:
                    j["_query"] = query
                results.extend(jobs)

                total = op_result.get("totalJobs", 0)
                if page * 20 >= total or page >= 15:
                    break
                page += 1
            except Exception as e:
                print(f"    [Microsoft Careers] Query '{query}': Error — {e}")
                break

        return results

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        print(f"  [Microsoft Careers] Fetching jobs from Microsoft Careers API...")
        seen_ids = set()
        all_results = []

        for query in MS_QUERIES:
            jobs = self._fetch_one_query(query)
            for j in jobs:
                job_id = j.get("jobId", j.get("id", ""))
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    all_results.append(j)

        print(f"  [Microsoft Careers] Unique jobs fetched: {len(all_results)}")
        return all_results

    def normalize(self, j: Dict[str, Any]) -> Job:
        job_id = j.get("jobId", j.get("id", ""))
        title = j.get("title", "").strip()

        props = j.get("properties", {}) if isinstance(j.get("properties"), dict) else {}
        location_raw = props.get("primaryLocation", "India")
        if isinstance(location_raw, list):
            location = ", ".join(location_raw)
        else:
            location = str(location_raw) if location_raw else "India"

        job_url = f"https://jobs.careers.microsoft.com/global/en/job/{job_id}" if job_id else ""
        description = props.get("description", "")
        discipline = props.get("discipline", "Software Engineering")

        return Job(
            source=self.source_name,
            source_job_id=f"ms_{job_id}",
            source_url=job_url,
            canonical_url=job_url,
            apply_url=job_url,
            company="Microsoft",
            company_normalized="microsoft",
            company_type="PRODUCT",
            title=title,
            title_normalized=title.lower(),
            description=description[:800],
            qualifications=description,
            location=location,
            country="IN",
            city=location.split(",")[0].strip() if "," in location else location,
            category=discipline,
            date_posted=j.get("postingDate", ""),
            raw_source_data=j,
            extraction_method="Microsoft Careers API"
        )
