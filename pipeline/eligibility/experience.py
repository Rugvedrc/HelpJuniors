import re
from typing import Tuple
from bs4 import BeautifulSoup
from models.eligibility import ExperienceAnalysis


def clean_html(text: str) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ").strip()


# Patterns that indicate THE JOB ITSELF is a new-grad/intern/entry-level position
NEW_GRAD_JOB_PATTERNS = [
    r'\bnew\s+grad\b', r'\bnew\s+graduate\b', r'\brecent\s+graduate\b',
    r'\b2026\s+(grad|graduate|batch)\b', r'\b(grad|graduate)\s*2026\b',
    r'\bcampus\s+(hire|recruit|hiring|recruitment)\b',
    r'\buniversity\s+(hire|recruit|graduate|grad)\b',
    r'\bentry[\s\-]level\b',
    r'\bfresh(er|ers|ly\s+graduated)?\b',
    r'\bfresh\s+graduate\b',
    r'\bno\s+experience\s+required\b',
    r'\bwithout\s+experience\b',
    r'\b0[\s\-–]1\s+years?\b',
    r'\b0[\s\-–]2\s+years?\b',
    r'\b0\s+to\s+[12]\s+years?\b',
    r'\bless\s+than\s+1\s+year\b',
    r'\bup\s+to\s+1\s+year\b',
    r'\brecently\s+graduated\b',
    r'\bgraduates?\s+(are\s+)?welcome\b',
    r'\bfreshers?\s+(are\s+)?(welcome|encouraged|invited)\b',
]

# Patterns that indicate THE JOB is an internship (not mentions of intern experience in senior roles)
# Note: deliberately excludes "internship program(s)" which is typically a company perk/context mention
INTERN_JOB_PATTERNS = [
    r'\binternship\s+(position|role|opportunity|opening)\b',  # singular, not "programs"
    r'\b(summer|winter|spring|full.year)\s+intern(ship)?\b',
    r'\bintern\s+(position|role|opening)\b',
    r'\bwe\s+(are\s+)?hiring\s+(a\s+)?intern\b',
    r'\bthis\s+(is\s+an?\s+)?internship\b',
    r'\binterning\s+at\b',
    r'\binterns?\s+will\s+(be\s+)?(responsible|work|join|gain)\b',
]

# Patterns indicating this IS a senior/experienced hire (not new grad)
SENIOR_ROLE_OVERRIDE_PATTERNS = [
    r'\b(senior|sr\.?|lead|principal|staff|architect|manager|director)\b'
]

# Contextual mentions — experience of team/company/tech, not candidate requirement
CONTEXTUAL_PATTERNS = [
    r'our\s+(engineering\s+)?(team|engineers?)\s+(has|have|with)\s+\d+\+?\s+years?\s+(of\s+)?(experience|expertise)',
    r'\d+\+?\s+years?\s+of\s+company\s+(history|experience)',
    r'built\s+over\s+\d+\+?\s+years?',
    r'founded\s+\d+\+?\s+years?\s+ago',
    r'\d+\+?\s+years?\s+in\s+(the\s+)?(market|industry)\s+(presence|leader)',
    r'platform\s+with\s+\d+\+?\s+years?\s+(of\s+)?experience',
    r'experience\s+with\s+\w+(\s+\w+)?\s+(for\s+)?\d+\+?\s+years?\s+(is\s+)?preferred',
]

# Pattern for a 0-start range
RANGE_0_START_PATTERN = r'\b0\s*[\-–]\s*([1-4])\s*(years?|yrs?|yr)\b'

# Technology experience (preferred mentions) — e.g. "2+ years of Python preferred"
TECH_EXP_PREFERRED_PATTERN = r'\d+\+?\s*years?\s*(of\s+)?(experience\s+with|working\s+with|using|in)\s+\w+(\s+\w+)?\s*(is\s+)?preferred'


def _strip_contextual(text: str) -> str:
    """Remove team/company/contextual experience mentions before numeric extraction."""
    cleaned = text
    for pat in CONTEXTUAL_PATTERNS:
        cleaned = re.sub(pat, ' ', cleaned, flags=re.IGNORECASE)
    return cleaned


def analyze_experience_requirement(jd_text: str, title: str = "") -> ExperienceAnalysis:
    raw_text = clean_html(jd_text)
    text_lower = raw_text.lower()
    title_lower = title.lower()
    combined = f"{title_lower} {text_lower}"

    # Strip contextual mentions before numeric parsing
    analysis_text = _strip_contextual(text_lower)

    # --- 1. Detect if THE JOB ITSELF is intern/new-grad positioned ---
    is_intern_job = any(re.search(p, combined, re.IGNORECASE) for p in INTERN_JOB_PATTERNS)
    is_new_grad_job = is_intern_job or any(re.search(p, combined, re.IGNORECASE) for p in NEW_GRAD_JOB_PATTERNS)

    # Override: if the title itself signals a senior role, suppress new-grad/intern detection
    # (e.g. a Senior Engineer JD that mentions "internship program" should NOT become entry-level)
    has_senior_title = any(re.search(p, title_lower, re.IGNORECASE) for p in SENIOR_ROLE_OVERRIDE_PATTERNS)
    if has_senior_title and is_new_grad_job:
        # Only keep new-grad if explicit hire signals are in the title too
        title_has_grad_signal = any(re.search(p, title_lower, re.IGNORECASE) for p in NEW_GRAD_JOB_PATTERNS)
        if not title_has_grad_signal:
            is_new_grad_job = False
            is_intern_job = False

    # --- 2. Check for 0-N year range starting at zero ---
    has_0_start_range = bool(re.search(RANGE_0_START_PATTERN, analysis_text))
    if has_0_start_range:
        is_new_grad_job = True

    # --- 3. Check welcome-grad / preferred signals ---
    has_welcome_grad = bool(re.search(
        r'new\s+grad(uate)?s?\s+(are\s+)?(welcome|encouraged|invited|considered)',
        analysis_text, re.IGNORECASE
    ))
    has_preferred_higher_exp = bool(re.search(
        r'\b([1-9]|10)\+?\s*(years?|yrs?)\s+(of\s+experience\s+)?(is\s+)?preferred\b',
        analysis_text, re.IGNORECASE
    ))

    # --- 4. Extract all numeric experience mentions ---
    # Pattern: N+ years [of] [X] experience [required/minimum/at least]
    EXP_PATTERN = re.compile(
        r'\b(\d+)\+?\s*(years?|yrs?|yr)\b'
        r'(?:\s+(?:of\s+)?(?:relevant|professional|industry|hands[\-\s]on|work|software|full[\-\s]time)?\s*experience)?'
        r'(?:\s*(?:required|minimum|at\s+least|is\s+required|is\s+mandatory))?',
        re.IGNORECASE
    )

    mandatory_min = 0.0
    preferred_years = None

    for m in EXP_PATTERN.finditer(analysis_text):
        val = float(m.group(1))
        if val == 0:
            continue

        # Skip if this match is part of a 0-N range
        snippet_start = max(0, m.start() - 5)
        snippet_end = min(len(analysis_text), m.end() + 5)
        surrounding = analysis_text[snippet_start:snippet_end]
        if re.search(r'\b0\s*[\-–]\s*' + str(int(val)), surrounding):
            continue

        # Get broader context window for intent classification
        ctx_start = max(0, m.start() - 60)
        ctx_end = min(len(analysis_text), m.end() + 60)
        context = analysis_text[ctx_start:ctx_end]

        is_preferred = bool(re.search(
            r'\bpreferred\b|\boptional\b|\bnice[\s-]to[\s-]have\b|\bdesirable\b|\bplus\b|\bbonus\b',
            context, re.IGNORECASE
        ))
        is_required = bool(re.search(
            r'\brequired\b|\bminimum\b|\bmust\s+have\b|\bat\s+least\b|\bmandatory\b|\bminimum\s+of\b',
            context, re.IGNORECASE
        ))

        if is_preferred and not is_required:
            if preferred_years is None or val < preferred_years:
                preferred_years = val
        elif is_required or not is_preferred:
            # Treat ambiguous (no qualifier) as potentially required if val >= 1
            if val >= 1.0 and val > mandatory_min:
                mandatory_min = val

    # --- 5. Semantic decision ---

    # Case A: job is clearly new-grad/intern AND no conflicting hard minimum
    if is_new_grad_job and not has_0_start_range:
        # "2+ required AND new graduates welcome" → the required minimum ALWAYS wins
        # Rule: "required" + any amount >= 1 → REJECT regardless of welcome signals
        if mandatory_min >= 1.0:
            return ExperienceAnalysis(
                min_required_experience_years=mandatory_min,
                max_required_experience_years=mandatory_min,
                required=True,
                preferred_experience_years=preferred_years,
                is_new_grad=False,
                is_intern=is_intern_job,
                confidence=0.97,
                reason=f"Requires {mandatory_min}+ yrs experience — explicit required minimum overrides new-grad signals"
            )
        # New grad signals win (no conflicting required minimum)
        return ExperienceAnalysis(
            min_required_experience_years=0.0,
            max_required_experience_years=1.0,
            required=False,
            preferred_experience_years=preferred_years,
            is_new_grad=True,
            is_intern=is_intern_job,
            confidence=0.97,
            reason="Entry-level/New-grad/Intern position (0 years min required)"
        )

    # Case B: 0-N range — entry level
    if has_0_start_range:
        return ExperienceAnalysis(
            min_required_experience_years=0.0,
            max_required_experience_years=2.0,
            required=False,
            preferred_experience_years=preferred_years,
            is_new_grad=True,
            is_intern=False,
            confidence=0.97,
            reason=f"0-N year range role: explicitly entry-level"
        )

    # Case C: only preferred, no mandatory
    if mandatory_min == 0.0 and preferred_years is not None:
        is_stretch_role = preferred_years >= 1.0  # 1+ yrs preferred = stretch
        return ExperienceAnalysis(
            min_required_experience_years=0.0,
            max_required_experience_years=1.0,
            required=False,
            preferred_experience_years=preferred_years,
            is_new_grad=True,
            is_intern=False,
            is_stretch=is_stretch_role,
            confidence=0.90,
            reason=f"{preferred_years}+ years preferred only — 0 years minimum required"
        )

    # Case D: mandatory minimum found
    if mandatory_min >= 1.0:
        return ExperienceAnalysis(
            min_required_experience_years=mandatory_min,
            max_required_experience_years=mandatory_min + 2.0,
            required=True,
            preferred_experience_years=preferred_years,
            is_new_grad=False,
            is_intern=False,
            confidence=0.93,
            reason=f"Requires {mandatory_min}+ years of experience"
        )

    # Case E: no experience signals at all → likely entry level
    return ExperienceAnalysis(
        min_required_experience_years=0.0,
        max_required_experience_years=1.0,
        required=False,
        preferred_experience_years=None,
        is_new_grad=True,
        is_intern=False,
        confidence=0.70,
        reason="No experience requirement detected — assumed entry-level"
    )


def evaluate_experience_eligibility(
    jd_text: str,
    title: str = "",
    candidate_months_fulltime: int = 2,
    candidate_months_intern: int = 8
) -> Tuple[bool, ExperienceAnalysis, str]:
    """
    Evaluate whether the candidate (2026 grad, ~2 mos fulltime, ~8 mos intern) is eligible.
    2 months fulltime does NOT satisfy '1+ years professional experience required'.
    """
    analysis = analyze_experience_requirement(jd_text, title)

    # ELIGIBLE: new grad / intern / 0-exp role
    if analysis.is_new_grad and analysis.min_required_experience_years == 0.0:
        return True, analysis, f"Eligible: {analysis.reason}"

    # INELIGIBLE: hard minimum of 1+ year
    if analysis.min_required_experience_years >= 1.0:
        return False, analysis, f"Ineligible: {analysis.reason}"

    # ELIGIBLE: 0 minimum required
    return True, analysis, f"Eligible: {analysis.reason}"
