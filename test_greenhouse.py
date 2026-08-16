import requests
import json
from bs4 import BeautifulSoup

def fetch_greenhouse_jobs(board_token, company_name):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    try:
        res = requests.get(url, timeout=8)
        if res.status_code != 200:
            return []
        data = res.json()
        raw_jobs = data.get("jobs", [])
        
        parsed = []
        for j in raw_jobs:
            location = j.get("location", {}).get("name", "India")
            
            # Filter for India locations
            loc_lower = location.lower()
            if not ("india" in loc_lower or "in" in loc_lower or any(city in loc_lower for city in ["bengaluru", "bangalore", "hyderabad", "gurugram", "noida", "pune", "mumbai", "chennai"])):
                continue
                
            content_html = j.get("content", "")
            clean_text = BeautifulSoup(content_html, "html.parser").get_text(separator=" ").strip() if content_html else ""
            
            parsed.append({
                "job_id": f"gh_{j.get('id')}",
                "title": j.get("title", ""),
                "company": company_name,
                "location": location,
                "city": location.split(",")[0].strip() if "," in location else location,
                "category": j.get("departments", [{}])[0].get("name", "Engineering") if j.get("departments") else "Engineering",
                "posted_date_str": j.get("updated_at", "")[:10],
                "url": j.get("absolute_url", ""),
                "basic_qualifications": clean_text[:3000],
                "preferred_qualifications": "",
                "description": clean_text[:500]
            })
            
        return parsed
    except Exception as e:
        print(f"Error fetching Greenhouse board for {company_name}: {e}")
        return []

if __name__ == "__main__":
    groww_jobs = fetch_greenhouse_jobs("groww", "Groww")
    print(f"Fetched {len(groww_jobs)} India jobs from Groww Greenhouse API:")
    for g in groww_jobs[:5]:
        print(f"- [{g['job_id']}] {g['title']} | {g['location']} | URL: {g['url']}")
