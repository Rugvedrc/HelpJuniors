import json
from typing import Dict, Any

class ObservabilityTracker:
    def __init__(self):
        self.stats: Dict[str, Any] = {
            "searches_executed": 0,
            "urls_discovered": 0,
            "urls_deduplicated": 0,
            "urls_extracted": 0,
            "api_jobs_greenhouse": 0,
            "api_jobs_amazon": 0,
            "web_jobs_discovered": 0,
            "rejected_non_product": 0,
            "rejected_non_tech": 0,
            "rejected_education_mismatch": 0,
            "rejected_experience_mismatch": 0,
            "rejected_location_mismatch": 0,
            "quarantined_unknown": 0,
            "final_eligible_jobs": 0,
            "rejection_log": []
        }

    def log_rejection(self, job_id: str, company: str, title: str, reason: str, category: str):
        self.stats["rejection_log"].append({
            "job_id": job_id,
            "company": company,
            "title": title,
            "reason": reason,
            "category": category
        })
        if category == "non_product":
            self.stats["rejected_non_product"] += 1
        elif category == "non_tech":
            self.stats["rejected_non_tech"] += 1
        elif category == "education":
            self.stats["rejected_education_mismatch"] += 1
        elif category == "experience":
            self.stats["rejected_experience_mismatch"] += 1
        elif category == "location":
            self.stats["rejected_location_mismatch"] += 1
        elif category == "quarantine":
            self.stats["quarantined_unknown"] += 1

    def print_summary(self):
        print("\n==========================================================================")
        print(" PIPELINE OBSERVABILITY & REJECTION METRICS SUMMARY")
        print("==========================================================================")
        print(f" URLs Discovered: {self.stats['urls_discovered']}")
        print(f" URLs Deduplicated: {self.stats['urls_deduplicated']}")
        print(f" Ingested Jobs: {self.stats['urls_extracted']}")
        print(f" Rejected (Non-Product Service IT): {self.stats['rejected_non_product']}")
        print(f" Rejected (Non-Tech/Senior Roles): {self.stats['rejected_non_tech']}")
        print(f" Rejected (Education Mismatch - Mandatory PhD/M.Tech): {self.stats['rejected_education_mismatch']}")
        print(f" Rejected (Experience Mismatch - 1+ or 2+ Yrs Required): {self.stats['rejected_experience_mismatch']}")
        print(f" Quarantined (Unknown Company): {self.stats['quarantined_unknown']}")
        print(f" FINAL ELIGIBLE JOBS FOR DASHBOARD: {self.stats['final_eligible_jobs']}")
        print("==========================================================================")
