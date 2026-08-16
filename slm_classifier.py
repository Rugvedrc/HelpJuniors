import re
from bs4 import BeautifulSoup
import company_whitelist

def clean_html(text):
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()

def classify_job_jd(job):
    company = job.get("company", "Product Company")
    title = (job.get("title") or "").strip()
    title_lower = title.lower()
    category = (job.get("category") or job.get("job_category") or "").lower()
    basic_qual = clean_html(job.get("basic_qualifications", ""))
    pref_qual = clean_html(job.get("preferred_qualifications", ""))
    desc = clean_html(job.get("description", ""))
    
    # Combine full text of the entire job description
    full_text = f"{title} {category} {basic_qual} {pref_qual} {desc}".lower()

    # Rule 1: Product Company Verification
    is_prod, prod_reason = company_whitelist.is_product_company(company)
    if not is_prod:
        return {
            "eligible": False,
            "company_type": "Service",
            "exp_tier": "Excluded",
            "min_exp_years": 99,
            "confidence": 0.99,
            "reason": prod_reason
        }

    # Rule 2: HARDCORE EXP FILTER - ELIMINATE ANY JOB THAT MENTIONS 1+, 2+, 3+, ... 10+ YEARS ANYWHERE IN THE JD!
    # Matches patterns like "1+ year", "1+ yrs", "2+ years", "3+ yrs", "1 year", "2 years", "3 years", etc.
    exp_pattern = re.compile(r'\b([1-9]|10)\+?\s*(years?|yrs?|yr)\b', re.IGNORECASE)
    
    is_intern_or_grad = any(re.search(ptrn, title_lower) for ptrn in [r'\bintern\b', r'\binternship\b', r'\binterns\b', r'\bgrad\b', r'\bgraduate\b', r'\b2026\b', r'\bstudent\b', r'\bfresher\b'])

    if exp_pattern.search(full_text) and not is_intern_or_grad:
        match_str = exp_pattern.search(full_text).group(0)
        return {
            "eligible": False,
            "company_type": "Product",
            "exp_tier": "Excluded (Exp Mentioned)",
            "min_exp_years": 99,
            "confidence": 1.0,
            "reason": f"Hardcore Filter: Detected '{match_str}' requirement anywhere in JD"
        }

    # Rule 3: Tech / Dev Domain Verification ONLY
    tech_keywords = [
        "software", "sde", "developer", "backend", "front end", "full stack",
        "machine learning", "ml", "applied scientist", "data science", "data scientist",
        "data engineer", "sre", "devops", "systems engineer", "qa engineer", "quality assurance engineer",
        "python", "java", "c++", "sysdev", "salesforce developer", "engineering", "forward deployed"
    ]

    is_tech = any(tk in title_lower or tk in category for tk in tech_keywords)

    # Exclude non-tech support/marketing/design/finance associate/intern roles
    exclude_non_dev_keywords = [
        "copy writer", "graphic designer", "writer", "designer", "content", "recruiter",
        "hr", "sales", "finance", "legal", "accountant", "controllership", "operations associate",
        "program manager", "project manager"
    ]
    if any(nd in title_lower for nd in exclude_non_dev_keywords) and not any(k in title_lower for k in ["sde", "software", "developer", "engineer", "scientist"]):
        is_tech = False

    if not is_tech:
        return {
            "eligible": False,
            "company_type": "Product",
            "exp_tier": "Excluded",
            "min_exp_years": 99,
            "confidence": 0.99,
            "reason": "Non-Dev / Non-Tech Role (Excluded)"
        }

    # Rule 4: Reject Mid/Senior Level Titles (SDE II, SDE III, Senior, Lead, Manager)
    if not is_intern_or_grad:
        reject_senior = [
            r'\bii\b', r'\biii\b', r'\biv\b', r'\b2\b', r'\b3\b', r'\bsenior\b', r'\bsr\b',
            r'\blead\b', r'\bprincipal\b', r'\bstaff\b', r'\bmanager\b', r'\bdirector\b', r'\barchitect\b'
        ]
        if any(re.search(rs, title_lower) for rs in reject_senior):
            return {
                "eligible": False,
                "company_type": "Product",
                "exp_tier": "Excluded",
                "min_exp_years": 2,
                "confidence": 0.98,
                "reason": "Senior/Level II/III Title"
            }

    return {
        "eligible": True,
        "company_type": "Product",
        "exp_tier": "0 Yrs (Absolute Fresher / 2026 Grad)",
        "min_exp_years": 0,
        "confidence": 1.0,
        "reason": f"Hardcore Passed: Zero mentions of 1+, 2+, 3+ yrs experience anywhere in JD for {company}"
    }
