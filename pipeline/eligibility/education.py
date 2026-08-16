import re
from typing import Tuple, Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel

def clean_html(text: str) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()

class EducationAnalysis(BaseModel):
    btech_eligible: bool = True
    phd_mandatory: bool = False
    masters_mandatory: bool = False
    confidence: float = 1.0
    reason: str = ""

PHD_MANDATORY_PATTERNS = [
    r'\bph\.?d\.?\s*(degree\s*)?required\b',
    r'\bdoctorate\s*(degree\s*)?required\b',
    r'\bmust\s*have\s*(a\s*)?ph\.?d\.?\b',
    r'\bph\.?d\.?\s*in\s*(computer science|machine learning|ai|statistics)\s*required\b'
]

MASTERS_MANDATORY_PATTERNS = [
    r'\bmaster\'?s\s*(degree\s*)?required\b',
    r'\bm\.?tech\.?\s*(degree\s*)?required\b',
    r'\bm\.?s\.?\s*in\s*(computer science|cs|ai)\s*required\b',
    r'\bmust\s*have\s*(a\s*)?master\'?s\b'
]

BACHELORS_ACCEPT_PATTERNS = [
    r'\bbachelor\'?s\b', r'\bb\.?tech\b', r'\bb\.?e\.?\b', r'\bb\.?s\.?\b',
    r'\bbachelor\'?s\s*or\s*higher\b', r'\bbachelor\'?s,\s*master\'?s\b',
    r'\bb\.?tech\s*\/\s*m\.?tech\b', r'\bundergraduate\b'
]

def analyze_education_requirement(jd_text: str, title: str = "") -> EducationAnalysis:
    text_lower = f"{title.lower()} {clean_html(jd_text).lower()}"

    has_bachelors_accepted = any(re.search(pat, text_lower) for pat in BACHELORS_ACCEPT_PATTERNS)
    has_phd_mandatory = any(re.search(pat, text_lower) for pat in PHD_MANDATORY_PATTERNS)
    has_masters_mandatory = any(re.search(pat, text_lower) for pat in MASTERS_MANDATORY_PATTERNS)

    # 1. PhD Mandatory Check
    if has_phd_mandatory and not has_bachelors_accepted:
        return EducationAnalysis(
            btech_eligible=False,
            phd_mandatory=True,
            masters_mandatory=False,
            confidence=0.98,
            reason="Ineligible: Job strictly requires a PhD / Doctorate degree"
        )

    # 2. Master's / M.Tech Mandatory Check
    if has_masters_mandatory and not has_bachelors_accepted:
        return EducationAnalysis(
            btech_eligible=False,
            phd_mandatory=False,
            masters_mandatory=True,
            confidence=0.95,
            reason="Ineligible: Job strictly requires a Master's / M.Tech degree (Bachelor's/B.Tech not accepted)"
        )

    # 3. Eligible for B.Tech / Bachelor's Candidates
    return EducationAnalysis(
        btech_eligible=True,
        phd_mandatory=False,
        masters_mandatory=False,
        confidence=1.0,
        reason="Eligible: B.Tech / Bachelor's degree candidates accepted"
    )

def verify_education_eligibility(jd_text: str, title: str = "") -> Tuple[bool, EducationAnalysis, str]:
    analysis = analyze_education_requirement(jd_text, title)
    return analysis.btech_eligible, analysis, analysis.reason
