from models.job import Job
from models.eligibility import EligibilityResult
from pipeline.company import classify_company
from pipeline.role import classify_role
from pipeline.eligibility.experience import evaluate_experience_eligibility
from pipeline.eligibility.education import verify_education_eligibility
from pipeline.eligibility.location import verify_location_eligibility


def evaluate_job_hard_eligibility(
    job: Job,
    candidate_months_fulltime: int = 2,
    candidate_months_intern: int = 8
) -> EligibilityResult:
    """
    Sequential hard-eligibility gate. Order matters — cheap/fast checks first.
    1. Company (Product vs Service vs Unknown)
    2. Role (dev taxonomy, non-tech, seniority)
    3. Location (India hard filter)
    4. Education (B.Tech eligible; PhD/Master's required → reject)
    5. Experience (required vs preferred vs new-grad)
    """
    full_jd = " ".join(filter(None, [
        job.title, job.category,
        job.qualifications, job.preferred_qualifications, job.description
    ]))

    # ── 1. Company ──────────────────────────────────────────────────────────
    comp_type, comp_ok, comp_reason = classify_company(job.company, job.source)
    job.company_type = comp_type
    if not comp_ok:
        return EligibilityResult(
            eligible=False,
            company_eligible=False,
            company_type=comp_type,
            rejection_reason=comp_reason
        )

    # ── 2. Role ─────────────────────────────────────────────────────────────
    role_ok, category, sub_cat, role_reason = classify_role(
        job.title, job.category, job.description
    )
    job.category = category
    job.sub_category = sub_cat
    if not role_ok:
        return EligibilityResult(
            eligible=False,
            company_eligible=True,
            company_type=comp_type,
            role_eligible=False,
            rejection_reason=role_reason
        )

    # ── 3. Location ─────────────────────────────────────────────────────────
    loc_status, loc_reason = verify_location_eligibility(job.location)
    if loc_status == "INELIGIBLE":
        return EligibilityResult(
            eligible=False,
            company_eligible=True,
            company_type=comp_type,
            role_eligible=True,
            location_eligible=False,
            rejection_reason=loc_reason
        )
    if loc_status == "REVIEW":
        # Quarantine — do not show in main dashboard but keep in DB
        return EligibilityResult(
            eligible=False,
            company_eligible=True,
            company_type=comp_type,
            role_eligible=True,
            location_eligible=False,
            rejection_reason=f"QUARANTINE (location): {loc_reason}"
        )

    # ── 4. Education ────────────────────────────────────────────────────────
    edu_ok, _edu, edu_reason = verify_education_eligibility(full_jd, job.title)
    if not edu_ok:
        return EligibilityResult(
            eligible=False,
            company_eligible=True,
            company_type=comp_type,
            role_eligible=True,
            location_eligible=True,
            experience_eligible=False,
            rejection_reason=edu_reason
        )

    # ── 5. Experience ───────────────────────────────────────────────────────
    exp_ok, exp_analysis, exp_reason = evaluate_experience_eligibility(
        full_jd, job.title, candidate_months_fulltime, candidate_months_intern
    )
    job.min_experience_years = exp_analysis.min_required_experience_years
    job.max_experience_years = exp_analysis.max_required_experience_years
    job.experience_text = exp_analysis.reason

    if not exp_ok:
        return EligibilityResult(
            eligible=False,
            company_eligible=True,
            company_type=comp_type,
            role_eligible=True,
            location_eligible=True,
            experience_eligible=False,
            experience_analysis=exp_analysis,
            rejection_reason=exp_reason
        )

    # ── PASSED ALL GATES ────────────────────────────────────────────────────
    return EligibilityResult(
        eligible=True,
        company_eligible=True,
        company_type=comp_type,
        role_eligible=True,
        role_category=category,
        experience_eligible=True,
        experience_analysis=exp_analysis,
        location_eligible=True,
        rejection_reason=None,
        confidence=exp_analysis.confidence
    )
