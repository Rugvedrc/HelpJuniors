import re
from typing import Tuple

# =============================================================================
# CATEGORY A — SOFTWARE ENGINEERING
# =============================================================================
CAT_A_KEYWORDS = [
    "software engineer", "software development engineer", "sde", "sde i", "sde 1",
    "software developer", "software development", "associate software engineer",
    "graduate software engineer", "graduate engineer", "entry level software engineer",
    "new grad software engineer", "backend engineer", "backend developer",
    "python developer", "python engineer", "api engineer",
    "application engineer", "application developer",
    "full stack engineer", "full stack developer", "fullstack",
    "systems engineer", "systems software", "software infrastructure",
    "software engineer - platform", "software engineer - infrastructure",
    "software engineer - cloud", "software engineer - ai",
    "software engineer - ml", "software engineer - data",
    "software engineer - backend", "software engineer - automation",
    "associate engineer", "junior software engineer", "junior developer",
    "junior engineer", "software trainee", "software intern",
    "engineering intern",  # e.g. "Engineering Intern" for SW roles
    "forward deployed engineer", "fde", "solutions engineer",
    "integration engineer", "api integration", "developer tools engineer",
    "developer experience engineer", "developer productivity",
    "production engineer", "technical solutions engineer",
    "platform developer", "technical engineer",
    # Finance/Investment Bank SWE titles (Goldman Sachs, JP Morgan, Morgan Stanley)
    "technology analyst", "technology associate", "analyst - technology",
    "analyst – technology", "analyst, technology", "engineering analyst",
    "technology analyst program",
    # Member of Technical Staff (Atlassian, Salesforce, Oracle, Databricks)
    "member of technical staff", "mts i", "mts 1",
    # Numbered junior variants
    "software engineer i", "software engineer 1",
    "engineer i", "developer i",
    # Graduate / Trainee titles (Cisco, Siemens, Honeywell India)
    "graduate engineer trainee", "engineer trainee", "technical trainee",
    "get ",  # GET = Graduate Engineer Trainee — note trailing space to avoid substring match
    "analyst programmer", "programmer analyst",
    # Other common junior titles
    "entry level engineer", "entry level developer", "entry level software",
    "junior software developer", "fresher software engineer",
    "software engineer new grad", "new grad engineer",
    # Walmart Global Tech specific
    "software development engineer i", "sde-i", "sde i ",
]

# =============================================================================
# CATEGORY B — AI / MACHINE LEARNING
# =============================================================================
CAT_B_KEYWORDS = [
    "ai engineer", "ai/ml engineer", "machine learning engineer", "ml engineer",
    "machine learning developer", "applied ml engineer", "applied scientist",
    "associate applied scientist", "ai developer", "generative ai engineer",
    "genai engineer", "gen ai", "llm engineer", "nlp engineer",
    "ai software engineer", "ml software engineer", "computer vision engineer",
    "deep learning engineer", "research engineer", "ai research engineer",
    "ai platform engineer", "ml platform engineer", "ml infrastructure engineer",
    "ai infrastructure", "machine learning scientist", "research scientist",
    "applied research", "foundation model", "language model engineer",
    "conversational ai", "dialogue systems", "speech engineer",
    "multimodal", "rlhf", "fine-tuning engineer", "prompt engineer",
    "ai automation engineer", "automation ai",
    # GenAI / RAG / Agentic AI
    "generative ai", "large language model", "agentic ai", "ai agent",
    "ai application engineer", "ai platform developer", "genai developer",
    "rag engineer", "vector database engineer", "ai backend engineer",
    "ml applications engineer", "ai solutions developer",
]

# =============================================================================
# CATEGORY C — DATA
# =============================================================================
CAT_C_KEYWORDS = [
    "data engineer", "junior data engineer", "associate data engineer",
    "data engineering", "analytics engineer", "data scientist",
    "junior data scientist", "associate data scientist",
    "machine learning data scientist", "applied data scientist",
    "data platform engineer", "data infrastructure engineer",
    "data pipeline engineer", "etl engineer", "big data engineer",
    "data developer", "data analyst engineer",
    "junior data analyst", "associate data analyst", "data operations engineer",
]

# =============================================================================
# CATEGORY D — CLOUD / DEVOPS / INFRASTRUCTURE
# =============================================================================
CAT_D_KEYWORDS = [
    "cloud engineer", "cloud developer", "devops engineer",
    "junior devops engineer", "associate devops engineer",
    "platform engineer", "platform software engineer",
    "infrastructure engineer", "infrastructure software engineer",
    "site reliability engineer", "sre", "associate sre", "junior sre",
    "reliability engineer", "production engineer",
    "cloud infrastructure engineer", "ml infrastructure engineer",
    "ai infrastructure engineer", "developer productivity engineer",
    "developer infrastructure engineer", "build engineer", "release engineer",
    "devsecops", "cloud architect", "systems reliability",
    "observability engineer", "monitoring engineer",
    "azure engineer", "aws engineer", "gcp engineer",
    "cloud infrastructure developer", "infrastructure developer",
    "platform reliability engineer", "mlops engineer", "ml ops engineer",
    "aiops engineer", "ai ops engineer",
]

# =============================================================================
# CATEGORY E — QA / SDET (engineering/automation only)
# =============================================================================
CAT_E_KEYWORDS = [
    "sdet", "software development engineer in test",
    "test automation engineer", "qa automation engineer",
    "automation engineer", "software engineer - test",
    "quality automation engineer", "test engineer",
    "software test engineer",
]

# =============================================================================
# CATEGORY F — SECURITY (software/cloud context)
# =============================================================================
CAT_F_KEYWORDS = [
    "security engineer", "cloud security engineer",
    "application security engineer", "security software engineer",
    "devsecops engineer", "appsec engineer",
    "product security engineer",
]

# =============================================================================
# CATEGORY G — OTHER ADJACENT (solutions, platform, adjacent SW roles)
# =============================================================================
CAT_G_KEYWORDS = [
    "solutions engineer", "technical solutions engineer",
    "developer tools", "developer experience",
    "platform developer", "software infrastructure engineer",
    "ai solutions engineer", "ml solutions engineer",
    "robotics software engineer", "embedded software",
    "firmware engineer", "compiler engineer",
    "distributed systems engineer",
    # Finance/Quant tech roles
    "quant developer", "quantitative developer", "quantitative engineer",
    "algo engineer", "algorithmic engineer", "quant software engineer",
    "systematic developer", "quant research engineer",
    # Technical but adjacent
    "technical analyst",  # NOT financial analyst — tech context
    "software consultant",
]

ALL_CATEGORIES = {
    "Software Engineering": CAT_A_KEYWORDS,
    "AI/ML Engineering": CAT_B_KEYWORDS,
    "Data Engineering": CAT_C_KEYWORDS,
    "Cloud/DevOps/Infrastructure": CAT_D_KEYWORDS,
    "Security Engineering": CAT_F_KEYWORDS,
    "Adjacent Engineering": CAT_G_KEYWORDS,
}

# =============================================================================
# NON-TECH REJECTION LIST — must match TITLE, not just any text
# =============================================================================
NON_TECH_TITLE_REJECT = [
    r'\bproduct\s+manager\b', r'\bproject\s+manager\b',
    r'\bbusiness\s+analyst\b', r'\bfinancial\s+analyst\b',
    r'\bmarketing\b', r'\bsales\b', r'\brecruiter\b', r'\brecruitment\b',
    r'\bhuman\s+resources\b', r'\bhr\s+\b',
    r'\bcontent\s+(writer|creator|manager)\b',
    r'\bgraphic\s+designer\b', r'\bux\s+designer\b', r'\bui\s+designer\b',
    r'\bproduct\s+designer\b',
    r'\bcustomer\s+(support|success|service)\b',
    r'\baccount\s+manager\b', r'\baccount\s+executive\b',
    r'\bbusiness\s+development\b',
    r'\boperations\s+(manager|associate|analyst)\b',
    r'\bsupply\s+chain\b',
    r'\bmanufacturing\s+engineer\b', r'\bprocess\s+engineer\b',
    r'\bcivil\s+engineer\b', r'\bmechanical\s+engineer\b',
    r'\belectrical\s+engineer\b', r'\bchemical\s+engineer\b',
    r'\bbiomedical\s+engineer\b', r'\baerospace\s+engineer\b',
    r'\bstructural\s+engineer\b', r'\benvironmental\s+engineer\b',
    r'\blocal\s+delivery\b', r'\bdelivery\s+partner\b',
    r'\blegal\b', r'\blawyer\b', r'\bcompliance\b',
    r'\bfinance\s+(manager|analyst|executive)\b',
    r'\baccountant\b', r'\bcontroller\b',
    # Consulting / management / non-dev roles that are not target SW engineering
    r'\bmanagement\s+consultant\b',
    r'\bengagement\s+manager\b',
    r'\bassociate\s+director\b',
    r'\bassistant\s+manager\b',
    r'\bfinancial\s+services\s+leader\b',
    r'\binsurance\s+analytics\s+leader\b',
    r'\bcorporate\s+finance\b',
    r'\bsales\s+engineer\b',  # presales, not SW dev
    r'\bsales\s+enablement\b',
    r'\bgtm\b',  # Go-to-market
    r'\bgrowth\s+engineer\b',  # growth/marketing, not SW dev
    r'\bmarketing\s+engineer\b',
    r'\btechnical\s+marketing\b',
    r'\bcredit\s+risk\b',  # Finance
    r'\brisk\s+(analyst|manager|engineer)\b',
    r'\bfraud\s+analyst\b',
    r'\bproduct\s+analyst\b',
    r'\bhead\s+of\b',  # C-level / senior leadership
    r'\bvp\s+of\b',  # VP roles
    r'\bsps\s+associate\b',  # Amazon Seller Partner Support = ops
    r'\bsupport\s+associate\b',
    r'\bbusiness\s+systems\s+analyst\b',
    r'\bpartner\s+operations\b',
    r'\bsolution\s+architect\b',
    r'\bstrategy\b',  # pure strategy roles
    r'don\'t\s+see\s+what',  # placeholder pool postings
    r'\btalent\s+pool\b',
]

# =============================================================================
# SENIORITY REJECTION — only match actual seniority role qualifiers
# =============================================================================
SENIORITY_TITLE_PATTERNS = [
    r'\bsenior\b', r'\bsr\.?\b', r'\blead\b', r'\bprincipal\b', r'\bstaff\b',
    r'\bmanager\b', r'\bdirector\b', r'\barchitect\b', r'\bhead\b',
    # Only reject III, IV, 3, 4+ numbered levels — NOT II/2 (used for junior at many companies)
    r'\b(sde|software\s+engineer|system\s+development\s+engineer|systems\s+development\s+engineer|site\s+reliability\s+engineer|sre|test|developer|engineer|scientist|data\s+engineer|ml\s+engineer|ai\s+engineer)[\s\-]+(iii|iv|3|4)\b',
    r'\bmts\s*[-\s]',  # MTS - prefix = Member of Technical Staff prefix (senior)
]

# Patterns that exempt a role from seniority rejection
SENIORITY_EXEMPT_PATTERNS = [
    r'\bnew\s+grad\b', r'\bentry[\s\-]level\b', r'\bfresh(er)?\b',
    r'\b2026\b', r'\bgraduate\b', r'\bintern\b',
    # Numbered level I / 1 = junior at most companies (SDE I, Engineer I, Software Engineer 1)
    r'\bengineer\s+i\b', r'\bsde\s+i\b', r'\bsde\s+1\b',
    r'\bsoftware\s+engineer\s+i\b', r'\bsoftware\s+engineer\s+1\b',
    r'\bdeveloper\s+i\b', r'\bdeveloper\s+1\b',
    r'\bmts\s+i\b', r'\bmts\s+1\b',
]


def classify_role(title: str, category: str = "", description: str = "") -> Tuple[bool, str, str, str]:
    """
    Returns: (is_eligible, category, sub_category, reasoning)
    Uses title + ATS category + description text for broader matching.
    """
    if not title:
        return False, "Unknown", "Unknown", "Job title is missing"

    title_lower = title.lower().strip()
    full_text = f"{title_lower} {category.lower()} {description.lower()[:500]}"

    # --- 1. Hard non-tech title rejection ---
    # Roles that are strictly non-target (support, QA, testing, voice, call center, sales, etc.)
    STRICT_NON_DEV_PATTERNS = [
        r'\bgtm\b', r'\bsales\s+engineer\b', r'\bmarketing\s+engineer\b',
        r'\btechnical\s+marketing\b', r'\bgrowth\s+engineer\b', r'\bsps\s+associate\b',
        r'\bsolutions\s+architect\b', r'\bpresales\b', r'\bproduct\s+analyst\b',
        r'\bassistant\s+manager\b', r'\bengagement\s+manager\b', r'\bmanagement\s+consultant\b',
        # Strict rejection for support, QA, testing, SDET, voice, call center, helpdesk, moderator
        r'\bsupport\b', r'\bhelpdesk\b', r'\bservice\s+desk\b', r'\bdesktop\s+support\b',
        r'\bqa\b', r'\bquality\b', r'\btesting\b', r'\btester\b', r'\btest\b', r'\bsdet\b',
        r'\bin\s+test\b', r'\bcontent\s+moderator\b', r'\bmoderation\b', r'\bvoice\b',
        r'\bcall\s+center\b', r'\btelecaller\b', r'\bcustomer\s+service\b'
    ]
    for pat in STRICT_NON_DEV_PATTERNS:
        if re.search(pat, title_lower, re.IGNORECASE):
            return False, "Non-Tech/Support", "Excluded Category", f"Strict Non-Dev/Support/QA/Testing role rejected: {title}"

    for pat in NON_TECH_TITLE_REJECT:
        if re.search(pat, title_lower, re.IGNORECASE):
            # Make sure no engineering override exists in title
            if not re.search(r'\b(software|data|ml|ai|cloud|backend|platform|sde|sre|engineer|developer|scientist)\b', title_lower):
                return False, "Non-Tech", "Non-Tech", f"Non-technical role: {title}"

    # --- 2. Seniority rejection (title-level, not description) ---
    has_seniority_exempt = any(re.search(p, title_lower) for p in SENIORITY_EXEMPT_PATTERNS)
    if not has_seniority_exempt:
        for pat in SENIORITY_TITLE_PATTERNS:
            if re.search(pat, title_lower, re.IGNORECASE):
                return False, "Senior Tech", "Senior Level", f"Senior/Lead/Staff role: {title}"

    # --- 3. Match against full dev taxonomy (title + category + short description) ---
    for cat_name, keywords in ALL_CATEGORIES.items():
        for kw in keywords:
            if kw in full_text:
                return True, cat_name, kw.title(), f"Matched '{kw}' in {cat_name}"

    # --- 4. Broad fallback: 'engineer' or 'developer' or 'scientist' ONLY
    #        Removed 'analyst' — too noisy (Financial Analyst, Business Analyst slip through)
    if re.search(r'\b(engineer|developer|scientist)\b', title_lower):
        # But not if it's a clearly non-SW domain
        non_sw_domains = r'\b(civil|mechanical|electrical|chemical|biomedical|manufacturing|process|structural|aerospace|environmental)\b'
        if not re.search(non_sw_domains, title_lower):
            return True, "Software Engineering", "Engineering", f"Broad engineering title match: {title}"

    # --- 5. Narrow analyst fallback: ONLY technology/technical/systems analyst passes
    #        (these are already in CAT_A_KEYWORDS but catches capitalization variants)
    if re.search(r'\b(technology|technical|software|systems)\s+analyst\b', title_lower):
        return True, "Software Engineering", "Technology Analyst", f"Technology analyst title match: {title}"

    return False, "Other", "Other", f"Role '{title}' does not match any target engineering domain"
