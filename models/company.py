from typing import List, Optional
from pydantic import BaseModel, Field

class CompanyIdentity(BaseModel):
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    ats_domains: List[str] = Field(default_factory=list)
    company_type: str = "PRODUCT"  # PRODUCT, SERVICE, CONSULTING, STAFFING, RECRUITMENT, UNKNOWN
    tier: Optional[str] = None
    allowed: bool = True
