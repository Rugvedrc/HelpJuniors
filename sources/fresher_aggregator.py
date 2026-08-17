import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from models.job import Job
from sources.base import SourceAdapter

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*"
}

AGGREGATOR_FEEDS = [
    {"name": "Freshershunt", "url": "https://freshershunt.in/feed/"},
    {"name": "OffCampusJobs4u", "url": "https://offcampusjobs4u.com/feed/"},
    {"name": "Freshersnow", "url": "https://www.freshersnow.com/feed/"},
]

# Patterns to extract direct official apply URLs (Workday, Greenhouse, Lever, Ashby, Amazon, etc.)
OFFICIAL_URL_PATTERNS = [
    r'https?://[a-zA-Z0-9\.-]*myworkdayjobs\.com/[^\s\'"<>\)]+',
    r'https?://[a-zA-Z0-9\.-]*greenhouse\.io/[^\s\'"<>\)]+',
    r'https?://[a-zA-Z0-9\.-]*lever\.co/[^\s\'"<>\)]+',
    r'https?://[a-zA-Z0-9\.-]*ashbyhq\.com/[^\s\'"<>\)]+',
    r'https?://[a-zA-Z0-9\.-]*amazon\.jobs/[^\s\'"<>\)]+',
    r'https?://careers\.[a-zA-Z0-9\.-]+/[^\s\'"<>\)]+',
    r'https?://jobs\.[a-zA-Z0-9\.-]+/[^\s\'"<>\)]+',
    r'https?://[a-zA-Z0-9\.-]*smartrecruiters\.com/[^\s\'"<>\)]+',
]


def clean_html(text: str) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()


class FresherAggregatorAdapter(SourceAdapter):
    """
    Crawls RSS/XML feeds of leading Indian fresher job aggregators (Freshershunt, OffCampusJobs4u, Freshersnow)
    Extracts the DIRECT OFFICIAL ATS link (Workday, Greenhouse, Lever, Ashby, Amazon) and job metadata.
    """

    @property
    def source_name(self) -> str:
        return "Fresher Job Aggregators (Freshershunt/OffCampusJobs4u)"

    def _extract_official_url(self, content: str, default_url: str) -> str:
        """Finds direct official ATS URL (Workday/Greenhouse/Lever/Ashby) inside blog post HTML."""
        for pattern in OFFICIAL_URL_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                # Filter out share/social/generic links
                for m in matches:
                    if not any(x in m for x in ["whatsapp", "telegram", "facebook", "twitter", "linkedin.com/share"]):
                        return m.rstrip(".,;\"'")
        return default_url

    def _fetch_feed(self, feed_info: Dict[str, str]) -> List[Dict[str, Any]]:
        name = feed_info["name"]
        url = feed_info["url"]
        results = []

        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            if res.status_code != 200:
                print(f"    [Aggregator] {name}: HTTP {res.status_code}")
                return []

            # Parse XML/RSS
            soup = BeautifulSoup(res.content, "xml")
            items = soup.find_all("item")

            for item in items:
                title = item.find("title").text if item.find("title") else ""
                link = item.find("link").text if item.find("link") else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") else ""

                # Extract description and content:encoded
                desc = item.find("description").text if item.find("description") else ""
                content_encoded = item.find("content:encoded").text if item.find("content:encoded") else desc
                full_html = f"{desc} {content_encoded}"

                official_url = self.extract_official_url_from_html(full_html, link)

                results.append({
                    "title": title,
                    "feed_link": link,
                    "official_url": official_url,
                    "content": clean_html(full_html),
                    "full_html": full_html,
                    "pub_date": pub_date,
                    "feed_name": name
                })
        except Exception as e:
            print(f"    [Aggregator] {name} error: {e}")

        return results

    def extract_official_url_from_html(self, html: str, fallback_url: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            for pattern in OFFICIAL_URL_PATTERNS:
                if re.match(pattern, href):
                    return href
        # Fallback to regex regex search in full text
        return self._extract_official_url(html, fallback_url)

    def discover(self, **kwargs) -> List[Dict[str, Any]]:
        print(f"  [Fresher Aggregators] Fetching latest off-campus drives from Freshershunt, OffCampusJobs4u...")
        all_results = []
        for feed in AGGREGATOR_FEEDS:
            items = self._fetch_feed(feed)
            print(f"    [{feed['name']}] Found {len(items)} posts")
            all_results.extend(items)
        print(f"  [Fresher Aggregators] Total raw posts fetched: {len(all_results)}")
        return all_results

    def normalize(self, raw: Dict[str, Any]) -> Job:
        raw_title = raw.get("title", "")
        official_url = raw.get("official_url") or raw.get("feed_link", "")
        content = raw.get("content", "")

        # Infer company from title (e.g. "JioHotstar Off Campus Drive 2026 | SDE I Frontend")
        company = "Unknown"
        title = raw_title

        if "|" in raw_title:
            parts = raw_title.split("|")
            company_part = parts[0].strip()
            # Clean "Off Campus Drive 2026", "Hiring", etc.
            company = re.sub(r'(?i)\s*(off campus drive|hiring|recruitment|drive|2025|2026|2027|batch).*', '', company_part).strip()
            title = parts[1].strip() if len(parts) > 1 else raw_title
        elif " " in raw_title:
            company = raw_title.split(" ")[0].strip()

        # Infer location from title or content
        location = "India"
        loc_match = re.search(r'(?i)\b(bengaluru|bangalore|hyderabad|pune|mumbai|chennai|noida|gurugram|gurgaon|delhi|pan india|remote)\b', f"{raw_title} {content}")
        if loc_match:
            location = loc_match.group(1).title()

        return Job(
            source=f"Aggregator ({raw.get('feed_name', 'Fresher')})",
            source_job_id=f"agg_{abs(hash(official_url))}",
            source_url=official_url,
            canonical_url=official_url,
            apply_url=official_url,
            company=company or "Product",
            company_normalized=(company or "product").lower().strip(),
            company_type="PRODUCT",
            title=title or raw_title,
            title_normalized=(title or raw_title).lower().strip(),
            description=content[:800],
            qualifications=content,
            location=location,
            country="IN",
            city=location,
            category="Software Engineering",
            date_posted=raw.get("pub_date", ""),
            raw_source_data=raw,
            extraction_method="Fresher RSS Aggregator"
        )
