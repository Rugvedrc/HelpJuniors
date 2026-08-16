import requests
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import multi_company_fetcher
import slm_classifier

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

def main():
    print("Executing Multi-Company Product Tech Jobs Pipeline for Freshers & 0-1 Yr Exp in India...")
    raw_jobs = multi_company_fetcher.fetch_all_product_jobs()
    print(f"Total candidate product jobs fetched: {len(raw_jobs)}")

    classified_jobs = []

    for j in raw_jobs:
        loc = (j.get("location") or "").lower()
        country_code = (j.get("country_code") or "").lower()
        
        # 1. Location check: Must be India
        is_india = country_code == "ind" or "in," in loc or "india" in loc or any(
            city in loc for city in ["bengaluru", "bangalore", "hyderabad", "chennai", "delhi", "pune", "gurugram", "noida", "mumbai"]
        )
        if not is_india:
            continue

        res = slm_classifier.classify_job_jd(j)
        if not res.get("eligible"):
            continue

        posted = j.get("posted_date_str", "")
        dt = parse_date(posted)
        job_id = j.get("job_id")
        url = j.get("url")
        basic = slm_classifier.clean_html(j.get("basic_qualifications", ""))
        pref = slm_classifier.clean_html(j.get("preferred_qualifications", ""))
        desc = slm_classifier.clean_html(j.get("description", ""))
        location_raw = j.get("location", "India")
        city = location_raw.split(",")[0].strip() if "," in location_raw else location_raw

        classified_jobs.append({
            "job_id": job_id,
            "company": j.get("company", "Product Company"),
            "company_type": "Product",
            "title": j.get("title", "").strip(),
            "location": location_raw,
            "city": city,
            "category": j.get("category", "Software Engineering"),
            "business_unit": j.get("business_unit", "Tech"),
            "posted_date_str": str(posted),
            "posted_timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "basic_qualifications": basic,
            "preferred_qualifications": pref,
            "description": desc,
            "exp_tier": res.get("exp_tier"),
            "min_exp_years": res.get("min_exp_years"),
            "ai_confidence": res.get("confidence"),
            "ai_reason": res.get("reason"),
            "posted_dt": dt
        })

    classified_jobs.sort(key=lambda x: x["posted_dt"], reverse=True)
    print(f"\nTOTAL VERIFIED PRODUCT TECH JOBS (FRESHERS / 0-1 YR EXP IN INDIA): {len(classified_jobs)}")

    db_rows = []
    txt_lines = [
        "==========================================================================",
        " MULTI-COMPANY PRODUCT TECH JOBS IN INDIA (FRESHERS & 0-1 YR EXP)",
        " STRICT RULES ENFORCED: 100% PRODUCT-BASED ONLY, ZERO 2+ YRS, ZERO SERVICE IT",
        " SORTED BY POSTED DATE (MOST RECENT FIRST)",
        f" Fetched At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f" Total Verified Product Openings: {len(classified_jobs)}",
        "==========================================================================",
        ""
    ]

    for idx, f in enumerate(classified_jobs, 1):
        db_rows.append(f)
        txt_lines.append(f"#{idx} | [{f['company']}] {f['title']}")
        txt_lines.append(f"Posted Date: {f['posted_date_str']} | Job ID: {f['job_id']}")
        txt_lines.append(f"Company: {f['company']} ({f['company_type']}) | Location: {f['location']}")
        txt_lines.append(f"Experience Tier: {f['exp_tier']} | AI Reason: {f['ai_reason']}")
        txt_lines.append(f"URL: {f['url']}")
        if f["description"]:
            txt_lines.append(f"Summary: {f['description']}")
        if f["basic_qualifications"]:
            txt_lines.append(f"Qualifications: {f['basic_qualifications']}")
        txt_lines.append("-" * 74)
        txt_lines.append("")

    with open("pristine_india_dev_0to2yrs_jobs.txt", "w", encoding="utf-8") as file_out:
        file_out.write("\n".join(txt_lines))

    df = pd.DataFrame(db_rows).drop(columns=["posted_dt"])
    conn = sqlite3.connect("jobs_india.db")
    df.to_sql("jobs", conn, if_exists="replace", index=False)
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON jobs(city);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON jobs(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_posted ON jobs(posted_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_tier ON jobs(exp_tier);")
    conn.commit()
    conn.close()

    print(f"Successfully saved {len(classified_jobs)} verified product tech roles to 'pristine_india_dev_0to2yrs_jobs.txt' and 'jobs_india.db'!")

if __name__ == "__main__":
    main()
