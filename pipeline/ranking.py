from datetime import datetime
from models.job import Job
from models.profile import CandidateProfile


TIER_1_COMPANIES = {
    "google", "microsoft", "amazon", "meta", "apple", "linkedin", "netflix",
    "goldman sachs", "jp morgan", "jpmorgan", "morgan stanley", "de shaw",
    "tower research", "two sigma", "jane street"
}

TIER_2_COMPANIES = {
    "adobe", "uber", "atlassian", "cisco", "salesforce", "oracle", "sap",
    "nvidia", "qualcomm", "intel", "ibm", "intuit", "servicenow", "workday",
    "razorpay", "groww", "swiggy", "zomato", "cred", "phonepe", "flipkart",
    "meesho", "freshworks", "postman", "browserstack", "walmart",
    "walmart global tech", "target", "paypal", "visa", "mastercard",
    "american express", "autodesk", "rubrik", "nutanix", "cohesity",
    "druva", "pure storage", "netapp", "sprinklr", "sarvam", "krutrim",
    "zepto", "navi", "slice", "fi money", "open financial"
}


def _days_since_posted(date_posted: str) -> int:
    """Returns number of days since job was posted. Returns 999 if unknown."""
    if not date_posted:
        return 999
    formats = [
        "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
        "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formats:
        try:
            posted_dt = datetime.strptime(date_posted[:19], fmt)
            return max(0, (datetime.now() - posted_dt).days)
        except ValueError:
            continue
    return 999


def calculate_relevance_score(job: Job, profile: CandidateProfile) -> float:
    """
    Ranks ONLY jobs that passed hard eligibility.

    Score components:
    - Role Match (30 pts): exact target role match in title vs generic pass
    - Experience Match (25 pts): 0 yrs required scores highest
    - Skills Match (25 pts): non-linear, depth bonus for 8+ skill matches
    - Company Tier (10 pts): Tier 1 > Tier 2 > other product
    - Freshness (10 pts): based on actual posting date, not always 10/10
    """
    score = 0.0
    company_lower = (job.company_normalized or job.company).lower()

    # ── 1. Role Match (30 pts) ───────────────────────────────────────────────
    title_lower = (job.title_normalized or job.title).lower()
    role_matched = any(target.lower() in title_lower for target in profile.target_roles)
    score += 30.0 if role_matched else 12.0

    # ── 2. Experience Match (25 pts) ─────────────────────────────────────────
    min_exp = job.min_experience_years or 0.0
    if min_exp == 0.0:
        score += 25.0   # Perfect: no experience required
    elif min_exp <= 1.0:
        score += 15.0   # Acceptable: up to 1 year required

    # ── 3. Skills Match (25 pts) — non-linear with depth bonus ──────────────
    text_lower = f"{title_lower} {job.qualifications.lower()} {job.description.lower()}"
    matched_skills = [s for s in profile.skills if s.lower() in text_lower]
    job.skills = matched_skills
    skill_count = len(matched_skills)

    if skill_count >= 8:
        score += 25.0
    elif skill_count >= 4:
        score += 20.0 + (skill_count - 4) * 1.25  # 20 → 25 for 4–8 matches
    elif skill_count >= 2:
        score += 12.0 + (skill_count - 2) * 4.0   # 12 → 20 for 2–4 matches
    elif skill_count == 1:
        score += 8.0
    # else: 0 pts

    # ── 4. Company Tier (10 pts) ─────────────────────────────────────────────
    if company_lower in TIER_1_COMPANIES or any(t in company_lower for t in TIER_1_COMPANIES):
        score += 10.0
    elif company_lower in TIER_2_COMPANIES or any(t in company_lower for t in TIER_2_COMPANIES):
        score += 8.0
    else:
        score += 5.0   # Other verified product companies

    # ── 5. Freshness (10 pts) — actually calculated from posting date ────────
    days_old = _days_since_posted(job.date_posted)
    if days_old <= 3:
        score += 10.0   # Posted in last 3 days — very fresh
    elif days_old <= 7:
        score += 8.0    # Posted this week
    elif days_old <= 14:
        score += 5.0    # Posted this fortnight
    elif days_old <= 30:
        score += 3.0    # Posted this month
    elif days_old == 999:
        score += 5.0    # Unknown date — neutral score
    else:
        score += 1.0    # Older than 30 days

    return round(min(100.0, score), 1)
