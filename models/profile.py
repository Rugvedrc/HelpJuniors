import json
import os
from typing import List
from pydantic import BaseModel, Field

class CandidateProfile(BaseModel):
    name: str = "Candidate Profile"
    graduation_year: int = 2026
    full_time_experience_months: int = 2
    internship_experience_months: int = 8
    target_locations: List[str] = Field(default_factory=lambda: ["India", "Bengaluru", "Hyderabad", "Pune", "Gurugram", "Noida", "Mumbai", "Remote"])
    target_company_types: List[str] = Field(default_factory=lambda: ["PRODUCT"])
    target_roles: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)

    @classmethod
    def load(cls, path: str = "config/candidate_profile.json") -> "CandidateProfile":
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cls(**data)
        return cls()
