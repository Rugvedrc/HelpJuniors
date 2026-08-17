import time
from typing import List, Dict, Any, Tuple
from models.job import Job
from sources.base import SourceAdapter
from sources.amazon import AmazonAdapter
from sources.workday import WorkdayAdapter
from sources.greenhouse import GreenhouseAdapter
from sources.lever import LeverAdapter
from sources.ashby import AshbyAdapter
from sources.searxng import SearXNGAdapter
from sources.google import GoogleAdapter
from sources.microsoft import MicrosoftAdapter
from sources.goldman import FinanceTechAdapter


class SourceManager:
    """
    Manager orchestrating job discovery across official company career portals
    (Amazon, Google, Microsoft, Goldman Sachs, JP Morgan, Morgan Stanley,
    Workday-hosted Enterprise portals, ATS boards: Greenhouse, Lever, Ashby)
    and SearXNG search fallback.
    """
    def __init__(self):
        self.adapters: List[SourceAdapter] = [
            AmazonAdapter(),           # Direct Official Career Portal
            GoogleAdapter(),           # Google Careers Official API
            MicrosoftAdapter(),        # Microsoft Careers Official API
            FinanceTechAdapter(),      # Goldman Sachs, JP Morgan, Morgan Stanley via SmartRecruiters
            WorkdayAdapter(),          # Workday Enterprise Career Portals (Adobe, Nvidia, Flipkart, etc.)
            GreenhouseAdapter(),       # ATS Board Provider
            LeverAdapter(),            # ATS Board Provider
            AshbyAdapter(),            # ATS Board Provider
            SearXNGAdapter(),          # Search Aggregator Backup (skips if unavailable)
        ]

    def discover_all_jobs(self) -> Tuple[List[Job], Dict[str, int]]:
        """
        Returns (all_canonical_jobs, per_source_counts).
        Each adapter runs independently with up to 3 attempts (1 + 2 retries).
        Failure in one does not stop others.
        Zero-return from a previously active adapter is logged as a warning.
        """
        all_jobs: List[Job] = []
        source_counts: Dict[str, int] = {}

        for adapter in self.adapters:
            source_name = adapter.source_name

            for attempt in range(3):  # 3 attempts total
                try:
                    raw_list = adapter.discover()
                    canonical = []
                    for r in raw_list:
                        try:
                            canonical.append(adapter.normalize(r))
                        except Exception:
                            pass  # Skip malformed records
                    all_jobs.extend(canonical)
                    source_counts[source_name] = len(canonical)

                    if len(canonical) == 0 and attempt < 2:
                        print(f"  ⚠️  [SourceManager] {source_name} returned 0 jobs (attempt {attempt+1}/3) — retrying in 3s...")
                        time.sleep(3)
                        continue  # Retry

                    break  # Success (even 0 results after all retries)

                except Exception as e:
                    print(f"  [SourceManager] {source_name} FAILED (attempt {attempt+1}/3): {e}")
                    if attempt < 2:
                        time.sleep(3)
                    else:
                        source_counts[source_name] = 0
                        print(f"  ❌ [SourceManager] {source_name} failed all 3 attempts — skipping.")

        return all_jobs, source_counts
