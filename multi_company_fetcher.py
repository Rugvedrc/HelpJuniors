import requests
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import company_whitelist

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def clean_html(text):
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()

def parse_date(date_str):
    if not date_str:
        return datetime.min
    formats = ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]
    cleaned = re.sub(r'\s+', ' ', date_str.strip())[:19]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass
    return datetime.min

def fetch_amazon_jobs(query):
    url = "https://www.amazon.jobs/en/search.json"
    offset = 0
    limit = 100
    matched_jobs = {}
    
    while True:
        params = {
            "base_query": query,
            "country[]": "IND",
            "result_limit": limit,
            "offset": offset,
            "sort": "recent"
        }
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=6)
            if res.status_code != 200:
                break
            data = res.json()
            jobs = data.get("jobs", [])
            if not jobs:
                break
            
            for j in jobs:
                job_id = j.get("id_icims") or j.get("id")
                if job_id:
                    matched_jobs[job_id] = {
                        "job_id": f"amz_{job_id}",
                        "company": "Amazon",
                        "company_type": "Product",
                        "title": j.get("title", "").strip(),
                        "location": j.get("location"),
                        "city": j.get("location", "").split(",")[2].strip() if len(j.get("location", "").split(",")) >= 3 else j.get("location"),
                        "category": j.get("job_category", "Software Development"),
                        "business_unit": j.get("business_category", "Amazon"),
                        "posted_date_str": j.get("posted_date"),
                        "url": f"https://www.amazon.jobs{j.get('job_path', '')}",
                        "basic_qualifications": clean_html(j.get("basic_qualifications")),
                        "preferred_qualifications": clean_html(j.get("preferred_qualifications")),
                        "description": clean_html(j.get("description_short")),
                        "country_code": j.get("country_code", "IND")
                    }

            offset += limit
            hits = data.get("hits", 0)
            if offset >= hits or offset >= 500:
                break
        except Exception:
            break
            
    return matched_jobs

def fetch_greenhouse_board(board_token, company_name):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return []
        data = res.json()
        raw_jobs = data.get("jobs", [])
        
        parsed = []
        for j in raw_jobs:
            location = j.get("location", {}).get("name", "India")
            loc_lower = location.lower()
            
            is_india = "india" in loc_lower or "in" in loc_lower or any(
                city in loc_lower for city in ["bengaluru", "bangalore", "hyderabad", "gurugram", "noida", "pune", "mumbai", "chennai"]
            )
            if not is_india:
                continue

            content_html = j.get("content", "")
            clean_text = clean_html(content_html) if content_html else ""

            parsed.append({
                "job_id": f"gh_{j.get('id')}",
                "company": company_name,
                "company_type": "Product",
                "title": j.get("title", "").strip(),
                "location": location,
                "city": location.split(",")[0].strip() if "," in location else location,
                "category": j.get("departments", [{}])[0].get("name", "Engineering") if j.get("departments") else "Engineering",
                "business_unit": company_name,
                "posted_date_str": j.get("updated_at", "")[:10],
                "url": j.get("absolute_url", ""),
                "basic_qualifications": clean_text[:3000],
                "preferred_qualifications": "",
                "description": clean_text[:500],
                "country_code": "IND"
            })
            
        return parsed
    except Exception as e:
        print(f"Error fetching Greenhouse for {company_name}: {e}")
        return []

def fetch_all_product_jobs():
    print("Fetching active jobs across Product-Based companies in India...")
    all_jobs = []

    # 1. Fetch Amazon Jobs
    amazon_queries = ["SDE", "software engineer", "developer", "applied scientist", "data engineer", "intern", "graduate", "2026"]
    amazon_results = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_amazon_jobs, q): q for q in amazon_queries}
        for future in as_completed(futures):
            try:
                res_dict = future.result()
                amazon_results.update(res_dict)
            except Exception:
                pass

    all_jobs.extend(list(amazon_results.values()))

    # 2. Fetch Greenhouse Product Companies (Razorpay, Groww, Meesho, etc.)
    greenhouse_boards = [
        ("razorpaysoftwareprivatelimited", "Razorpay"),
        ("groww", "Groww")
    ]
    for token, comp in greenhouse_boards:
        gh_list = fetch_greenhouse_board(token, comp)
        all_jobs.extend(gh_list)

    print(f"Successfully fetched {len(all_jobs)} candidate product-based jobs.")
    return all_jobs

if __name__ == "__main__":
    jobs = fetch_all_product_jobs()
    print(f"Total jobs fetched: {len(jobs)}")
