import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
from extraction.json_ld import extract_schema_org_job_posting

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

def extract_job_content(url: str, existing_qualifications: str = "") -> Dict[str, Any]:
    """
    Tiered extraction strategy:
    1. Deterministic JSON-LD structured data
    2. Static HTML extraction using BeautifulSoup
    3. Retain API content if available
    """
    if existing_qualifications and len(existing_qualifications) > 100:
        return {
            "method": "API",
            "content": existing_qualifications
        }

    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            json_ld = extract_schema_org_job_posting(res.text)
            if json_ld and json_ld.get("description"):
                return {
                    "method": "JSON-LD",
                    "content": json_ld["description"],
                    "json_ld_data": json_ld
                }
            clean_html = BeautifulSoup(res.text, "html.parser").get_text(separator=" ").strip()
            return {
                "method": "Static HTML",
                "content": clean_html[:3000]
            }
    except Exception:
        pass

    return {
        "method": "Fallback",
        "content": existing_qualifications
    }
