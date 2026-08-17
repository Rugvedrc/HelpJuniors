from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Job(BaseModel):
    source: str
    source_job_id: str
    source_url: str
    canonical_url: str
    apply_url: str

    company: str
    company_normalized: str
    company_type: str = "PRODUCT"  # PRODUCT, SERVICE, UNKNOWN

    title: str
    title_normalized: str

    description: str = ""
    responsibilities: str = ""
    qualifications: str = ""
    preferred_qualifications: str = ""

    location: str = ""
    country: str = ""
    city: str = ""
    remote_type: str = "Onsite"  # Onsite, Hybrid, Remote

    employment_type: str = "Full-time"

    date_posted: Optional[str] = None
    date_updated: Optional[str] = None
    valid_through: Optional[str] = None

    min_experience_years: float = 0.0
    max_experience_years: float = 1.0
    experience_text: str = ""

    skills: List[str] = Field(default_factory=list)
    category: str = "Software Engineering"
    sub_category: str = "Backend"

    raw_source_data: Dict[str, Any] = Field(default_factory=dict)
    extraction_method: str = "API"

    discovered_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_seen_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_verified_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    active_status: str = "ACTIVE"  # ACTIVE, STALE, EXPIRED, REMOVED, UNKNOWN

    eligibility_status: bool = False
    rejection_reason: Optional[str] = None

    relevance_score: float = 0.0
    confidence_score: float = 1.0
    stretch_eligible: bool = False  # True = 1-2 yrs preferred (not required) — shown separately
