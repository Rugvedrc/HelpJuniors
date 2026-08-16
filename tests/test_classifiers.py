import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.eligibility.experience import evaluate_experience_eligibility
from pipeline.eligibility.location import verify_location_eligibility
from pipeline.role import classify_role

PASS = 0
FAIL = 0

def check(label, got, want):
    global PASS, FAIL
    if got == want:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}  GOT={got!r}  WANT={want!r}")
        FAIL += 1

print("\n=== EXPERIENCE CLASSIFIER ===")
def exp(jd, title="Software Engineer"):
    ok, _, _ = evaluate_experience_eligibility(jd, title)
    return ok

check("New Grad → ACCEPT",            exp("Software Engineer New Grad role"),                            True)
check("2026 Graduate → ACCEPT",       exp("2026 Graduate Software Engineer"),                            True)
check("0-1 years → ACCEPT",           exp("0-1 years of experience required"),                           True)
check("0-2 years → ACCEPT",           exp("0-2 years of experience"),                                    True)
check("Entry level → ACCEPT",         exp("Entry-level position, no prior experience needed"),            True)
check("Fresher → ACCEPT",             exp("Freshers are welcome to apply"),                               True)
check("No exp required → ACCEPT",     exp("No experience required"),                                     True)
check("2+ preferred only → ACCEPT",   exp("2+ years preferred"),                                         True)
check("2+ preferred+newgrad → ACCEPT",exp("2+ years preferred, new graduates are welcome"),               True)
check("Team 5+ yrs → ACCEPT",         exp("Our engineering team has 5+ years of experience building systems."), True)
check("Py pref 2yr → ACCEPT",         exp("Experience with Python for 2+ years preferred"),               True)
check("1+ required → REJECT",         exp("Minimum 1 year of professional experience required"),          False)
check("1+ yrs required → REJECT",     exp("1+ years professional experience required"),                   False)
check("2+ required → REJECT",         exp("2+ years experience required"),                                False)
check("2+ req+newgrad → REJECT",      exp("2+ years required; new graduates are welcome"),                False)
check("1-2 yrs required → REJECT",    exp("1-2 years of experience required"),                            False)
check("Senior 5+ → REJECT",           exp("5+ years of software engineering experience required", "Senior Engineer"), False)
check("Internship program → NO Override", exp("5+ years experience required. We also run internship programs for students.", "Senior Software Engineer"), False)

print("\n=== LOCATION CLASSIFIER ===")
def loc(l):
    status, _ = verify_location_eligibility(l)
    return status

check("Bengaluru, India → ELIGIBLE",   loc("Bengaluru, Karnataka, India"),       "ELIGIBLE")
check("Hyderabad, India → ELIGIBLE",   loc("Hyderabad, Telangana, India"),       "ELIGIBLE")
check("India Remote → ELIGIBLE",       loc("India - Remote"),                    "ELIGIBLE")
check("Remote - India → ELIGIBLE",     loc("Remote - India"),                    "ELIGIBLE")
check("Remote, India → ELIGIBLE",      loc("Remote, India"),                     "ELIGIBLE")
check("United States → INELIGIBLE",    loc("United States"),                     "INELIGIBLE")
check("Canada → INELIGIBLE",           loc("Canada"),                            "INELIGIBLE")
check("Singapore → INELIGIBLE",        loc("Singapore"),                         "INELIGIBLE")
check("UK → INELIGIBLE",              loc("United Kingdom"),                     "INELIGIBLE")
check("Indiana US → INELIGIBLE",       loc("Indiana, United States"),            "INELIGIBLE")
check("Remote only → REVIEW",          loc("Remote"),                            "REVIEW")
check("Empty → REVIEW",                loc(""),                                  "REVIEW")

print("\n=== ROLE CLASSIFIER ===")
def role(title, desc=""):
    ok, _, _, _ = classify_role(title, "", desc)
    return ok

check("Software Engineer → ACCEPT",       role("Software Engineer"),            True)
check("Backend Engineer → ACCEPT",        role("Backend Engineer"),             True)
check("Python Developer → ACCEPT",        role("Python Developer"),             True)
check("AI Engineer → ACCEPT",             role("AI Engineer"),                  True)
check("ML Engineer → ACCEPT",             role("Machine Learning Engineer"),    True)
check("Data Engineer → ACCEPT",           role("Data Engineer"),                True)
check("SRE → ACCEPT",                     role("Site Reliability Engineer"),    True)
check("Platform Engineer → ACCEPT",       role("Platform Engineer"),            True)
check("DevOps Engineer → ACCEPT",         role("DevOps Engineer"),              True)
check("Applied Scientist → ACCEPT",       role("Applied Scientist"),            True)
check("GenAI Engineer → ACCEPT",          role("GenAI Engineer"),               True)
check("SDET → ACCEPT",                    role("Software Development Engineer in Test"), True)
check("Senior Software Eng → REJECT",     role("Senior Software Engineer"),     False)
check("Staff Engineer → REJECT",          role("Staff Engineer"),               False)
check("Engineering Manager → REJECT",     role("Engineering Manager"),          False)
check("Recruiter → REJECT",              role("Technical Recruiter"),           False)
check("Product Manager → REJECT",        role("Product Manager"),              False)
check("Mechanical Engineer → REJECT",    role("Mechanical Engineer"),           False)
check("Civil Engineer → REJECT",         role("Civil Engineer"),               False)

print(f"\n{'='*50}")
print(f"RESULTS: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("ALL TESTS PASSED ✓")
else:
    print(f"FAILURES: {FAIL}")
