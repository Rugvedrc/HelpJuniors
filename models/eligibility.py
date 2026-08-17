from typing import Optional
from pydantic import BaseModel, Field

class ExperienceAnalysis(BaseModel):
    min_required_experience_years: float = 0.0
    max_required_experience_years: float = 1.0
    required: bool = True
    preferred_experience_years: Optional[float] = None
    is_new_grad: bool = False
    is_intern: bool = False
    is_stretch: bool = False  # True = 1-2 yrs preferred (not required) — eligible but shown separately
    confidence: float = 1.0
    reason: str = ""

class EligibilityResult(BaseModel):
    eligible: bool = False
    company_eligible: bool = False
    company_type: str = "UNKNOWN"  # PRODUCT, SERVICE, UNKNOWN
    role_eligible: bool = False
    role_category: str = "Tech"
    experience_eligible: bool = False
    experience_analysis: Optional[ExperienceAnalysis] = None
    location_eligible: bool = False
    rejection_reason: Optional[str] = None
    confidence: float = 1.0
