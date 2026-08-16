from typing import List, Dict, Any, Tuple
from models.job import Job
from sources.base import SourceAdapter
from sources.amazon import AmazonAdapter
from sources.workday import WorkdayAdapter
from sources.greenhouse import GreenhouseAdapter
from sources.lever import LeverAdapter
from sources.ashby import AshbyAdapter
from sources.searxng import SearXNGAdapter


class SourceManager:
    """
    Manager orchestrating job discovery across official company career portals
    (Amazon, Workday-hosted Enterprise portals for Adobe, Nvidia, Salesforce, Target, etc.)
    and ATS boards (Greenhouse, Lever, Ashby).
    """
    def __init__(self):
        self.adapters: List[SourceAdapter] = [
            AmazonAdapter(),           # Direct Official Career Portal
            WorkdayAdapter(),          # Direct Official Enterprise Career Portals (Adobe, Nvidia, Salesforce, Target, etc.)
            GreenhouseAdapter(),       # ATS Board Provider
            LeverAdapter(),            # ATS Board Provider
            AshbyAdapter(),            # ATS Board Provider
            SearXNGAdapter(),          # Search Aggregator Backup
        ]

    def discover_all_jobs(self) -> Tuple[List[Job], Dict[str, int]]:
        """
        Returns (all_canonical_jobs, per_source_counts).
        Each adapter runs independently; failure in one does not stop others.
        """
        all_jobs: List[Job] = []
        source_counts: Dict[str, int] = {}

        for adapter in self.adapters:
            source_name = adapter.source_name
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
            except Exception as e:
                print(f"  [SourceManager] {source_name} FAILED: {e}")
                source_counts[source_name] = 0

        return all_jobs, source_counts
