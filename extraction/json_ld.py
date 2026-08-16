import json
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

def extract_schema_org_job_posting(html_content: str) -> Optional[Dict[str, Any]]:
    """Extracts Schema.org JobPosting JSON-LD structured data from HTML if present."""
    if not html_content:
        return None
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            if not s.string:
                continue
            try:
                data = json.loads(s.string)
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    return {
                        "title": data.get("title"),
                        "description": BeautifulSoup(data.get("description", ""), "html.parser").get_text(separator=" ").strip(),
                        "datePosted": data.get("datePosted"),
                        "validThrough": data.get("validThrough"),
                        "company": data.get("hiringOrganization", {}).get("name") if isinstance(data.get("hiringOrganization"), dict) else data.get("hiringOrganization"),
                        "jobLocation": data.get("jobLocation"),
                        "employmentType": data.get("employmentType"),
                        "experienceRequirements": data.get("experienceRequirements")
                    }
            except Exception:
                pass
    except Exception:
        pass
    return None
