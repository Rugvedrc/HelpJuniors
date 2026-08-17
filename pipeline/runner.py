from collections import defaultdict
from datetime import datetime
from models.profile import CandidateProfile
from sources.manager import SourceManager
from pipeline.deduplication import deduplicate_jobs
from pipeline.eligibility.base import evaluate_job_hard_eligibility
from pipeline.ranking import calculate_relevance_score
from pipeline.observability import ObservabilityTracker
from db.database import save_jobs_to_db


def run_job_discovery_pipeline():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("=" * 74)
    print(f"  PERSONAL JOB-DISCOVERY AGENT — Rugved Rajesh Chandekar")
    print(f"  Timestamp: {ts}")
    print("=" * 74)

    profile = CandidateProfile.load()
    tracker = ObservabilityTracker()
    source_mgr = SourceManager()

    # ── STAGE 1: DISCOVERY ────────────────────────────────────────────────
    print("\nSTAGE 1 — Discovery (multi-source)")
    raw_jobs, source_counts = source_mgr.discover_all_jobs()
    tracker.stats["source_counts"] = source_counts
    tracker.stats["urls_discovered"] = len(raw_jobs)

    print(f"\n  SOURCE BREAKDOWN:")
    for src, cnt in source_counts.items():
        status = "OK" if cnt > 0 else "0 (unavailable or no results)"
        print(f"    {src:20s}: {cnt} jobs  [{status}]")

    # ── STAGE 2: DEDUPLICATION ────────────────────────────────────────────
    print(f"\nSTAGE 2 — Deduplication ({len(raw_jobs)} raw jobs)")
    unique_jobs, dup_count = deduplicate_jobs(raw_jobs)
    tracker.stats["urls_deduplicated"] = dup_count
    tracker.stats["urls_extracted"] = len(unique_jobs)
    print(f"  Duplicates removed: {dup_count} | Unique: {len(unique_jobs)}")

    # ── STAGE 3: HARD ELIGIBILITY ─────────────────────────────────────────
    print(f"\nSTAGE 3 — Hard Eligibility Pipeline ({len(unique_jobs)} unique jobs)")
    eligible_jobs = []
    stretch_jobs = []
    all_processed = []

    rej_by_reason = defaultdict(int)

    for job in unique_jobs:
        res = evaluate_job_hard_eligibility(
            job,
            candidate_months_fulltime=profile.full_time_experience_months,
            candidate_months_intern=profile.internship_experience_months
        )
        job.eligibility_status = res.eligible
        job.rejection_reason = res.rejection_reason
        job.confidence_score = res.confidence

        if not res.eligible:
            reason = res.rejection_reason or "Unknown"
            # Categorise
            if not res.company_eligible:
                cat = "company"
            elif not res.role_eligible:
                cat = "role"
            elif res.rejection_reason and ("QUARANTINE" in res.rejection_reason or "location" in res.rejection_reason.lower()):
                cat = "location"
            elif not res.experience_eligible:
                cat = "experience"
            else:
                cat = "other"

            tracker.log_rejection(job.source_job_id, job.company, job.title, reason, cat)
            rej_by_reason[cat] += 1
        else:
            # ── STAGE 4: RANKING (eligible only) ────────────────────────────────────────
            job.relevance_score = calculate_relevance_score(job, profile)
            # Mark stretch roles (1-2 yrs preferred, 0 required)
            if res.experience_analysis and res.experience_analysis.is_stretch:
                job.stretch_eligible = True
                stretch_jobs.append(job)
            else:
                eligible_jobs.append(job)

        all_processed.append(job)

    eligible_jobs.sort(key=lambda x: x.relevance_score, reverse=True)
    stretch_jobs.sort(key=lambda x: x.relevance_score, reverse=True)
    tracker.stats["final_eligible_jobs"] = len(eligible_jobs)
    tracker.stats["final_stretch_jobs"] = len(stretch_jobs)

    # ── STAGE 5: PERSIST ALL (no limit) ────────────────────────────────────────────
    all_to_save = all_processed  # includes both eligible, stretch, and rejected
    print(f"\nSTAGE 4 — Persisting ALL {len(all_to_save)} records to SQLite (no limit)")
    save_jobs_to_db(all_to_save)

    # ── FINAL DISTRIBUTION ────────────────────────────────────────────────
    company_dist = defaultdict(int)
    for j in eligible_jobs:
        company_dist[j.company] += 1

    # ── OBSERVABILITY REPORT ──────────────────────────────────────────────
    print("\n" + "=" * 74)
    print("  PIPELINE OBSERVABILITY REPORT")
    print("=" * 74)
    print(f"  SOURCE COUNTS:")
    for src, cnt in source_counts.items():
        print(f"    {src:20s}: {cnt}")
    print(f"\n  DISCOVERY:")
    print(f"    URLs Discovered : {tracker.stats['urls_discovered']}")
    print(f"    Duplicates      : {tracker.stats['urls_deduplicated']}")
    print(f"    Unique Processed: {tracker.stats['urls_extracted']}")
    print(f"\n  REJECTIONS:")
    print(f"    Company (non-product/unknown) : {rej_by_reason['company']}")
    print(f"    Role (non-tech/senior)        : {rej_by_reason['role']}")
    print(f"    Location (foreign/unknown)    : {rej_by_reason['location']}")
    print(f"    Experience mismatch           : {rej_by_reason['experience']}")
    print(f"    Other                         : {rej_by_reason['other']}")
    print(f"\n  FINAL ELIGIBLE JOBS: {len(eligible_jobs)}")
    print(f"  STRETCH ROLES (1-2 yrs preferred): {len(stretch_jobs)}")
    if company_dist:
        print(f"\n  FINAL DISTRIBUTION BY COMPANY:")
        for company, cnt in sorted(company_dist.items(), key=lambda x: -x[1])[:20]:
            print(f"    {company:35s}: {cnt}")
    print("=" * 74)

    # ── TEXT CATALOG ──────────────────────────────────────────────────────
    lines = [
        "=" * 74,
        f"  ELIGIBLE JOBS — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Candidate: Rugved Rajesh Chandekar | B.Tech IT 2026 | Entry Level India",
        f"  Total Eligible: {len(eligible_jobs)}",
        "=" * 74, ""
    ]
    for idx, j in enumerate(eligible_jobs, 1):
        lines.append(f"#{idx:03d} | [{j.company}] {j.title}  (Match: {j.relevance_score:.0f}%)")
        lines.append(f"  Source   : {j.source}")
        lines.append(f"  Location : {j.location}")
        lines.append(f"  Exp      : {j.experience_text}")
        lines.append(f"  URL      : {j.canonical_url}")
        if j.qualifications:
            lines.append(f"  Quals    : {j.qualifications[:300]}")
        lines.append("-" * 74)

    with open("pristine_india_dev_0to2yrs_jobs.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  Text catalog saved: pristine_india_dev_0to2yrs_jobs.txt")

    return eligible_jobs


if __name__ == "__main__":
    run_job_discovery_pipeline()
