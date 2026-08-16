from models.job import Job
from models.profile import CandidateProfile

def calculate_relevance_score(job: Job, profile: CandidateProfile) -> float:
    """
    Ranks ONLY jobs that passed hard eligibility.
    Score components:
    - Role Match (30%)
    - Experience Match (25%)
    - Skills Match (25%)
    - Company Tier (10%)
    - Freshness (10%)
    """
    score = 0.0

    # 1. Role Match (30%)
    title_lower = job.title_normalized
    for target in profile.target_roles:
        if target.lower() in title_lower:
            score += 30.0
            break
    else:
        score += 15.0

    # 2. Experience Match (25%)
    if job.min_experience_years == 0.0:
        score += 25.0
    elif job.min_experience_years <= 1.0:
        score += 15.0

    # 3. Skills Match (25%)
    text_lower = f"{job.title_normalized} {job.qualifications.lower()} {job.description.lower()}"
    matched_skills = [s for s in profile.skills if s.lower() in text_lower]
    job.skills = matched_skills
    skill_ratio = min(1.0, len(matched_skills) / 4.0)
    score += skill_ratio * 25.0

    # 4. Company Match (10%)
    tier_boost = 10.0 if job.company in ["Amazon", "Microsoft", "Google", "Razorpay", "Groww", "Flipkart", "Adobe", "Uber", "Atlassian"] else 7.0
    score += tier_boost

    # 5. Freshness (10%)
    score += 10.0

    return round(min(100.0, score), 1)
