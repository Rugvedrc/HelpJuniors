import json
import os
from typing import Tuple

# ATS sources whose jobs are already restricted to known product companies
TRUSTED_PRODUCT_SOURCES = {"Greenhouse", "Lever", "Ashby"}

_COMPANY_DATA = None


def _load():
    global _COMPANY_DATA
    if _COMPANY_DATA is not None:
        return _COMPANY_DATA
    path = "config/companies.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _COMPANY_DATA = json.load(f)
    else:
        _COMPANY_DATA = {"product_companies": [], "service_companies": []}
    return _COMPANY_DATA


def classify_company(company_name: str, source: str = "") -> Tuple[str, bool, str]:
    """
    Classifies company as PRODUCT, SERVICE, or UNKNOWN.
    Returns: (company_type, is_eligible, reasoning)

    Jobs sourced from trusted ATS (Greenhouse/Lever/Ashby) are treated as PRODUCT
    unless they match the service blacklist.
    """
    data = _load()
    service_list = [s.lower() for s in data.get("service_companies", [])]
    product_list = [p.lower() for p in data.get("product_companies", [])]

    if not company_name:
        return "UNKNOWN", False, "Company name missing (Quarantined)"

    norm = company_name.lower().strip()

    # 1. Always check service blacklist first
    for s in service_list:
        if s in norm or norm in s:
            return "SERVICE", False, f"Service/Outsourcing Company ({company_name})"

    # 2. Trusted ATS sources → treat as PRODUCT unless blacklisted
    if source in TRUSTED_PRODUCT_SOURCES:
        return "PRODUCT", True, f"Product Company via trusted ATS ({source}): {company_name}"

    # 3. Check product whitelist
    for p in product_list:
        p_lower = p.lower()
        if p_lower in norm or norm in p_lower or norm == p_lower:
            return "PRODUCT", True, f"Whitelisted Product Company ({company_name})"

    # 4. Amazon is always product
    if "amazon" in norm or "aws" in norm:
        return "PRODUCT", True, f"Amazon/AWS (Product Company)"

    # 5. Unknown — quarantine for review
    return "UNKNOWN", False, f"Unknown company '{company_name}' — Quarantined for review"
