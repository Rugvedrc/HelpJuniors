import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from pipeline.eligibility.experience import evaluate_experience_eligibility

def test_positive_cases():
    cases = [
        ("Software Engineer — New Grad", "Responsibilities: build backend services"),
        ("Software Engineer", "Basic qualifications: 0 years experience required"),
        ("Backend Engineer", "Qualifications: 0-1 years of experience in Python"),
        ("AI Engineer", "Targeting University Graduate students"),
        ("ML Engineer", "2026 Graduate candidates welcome"),
        ("SRE", "Entry Level position for freshers"),
        ("Software Developer", "Fresh graduates encouraged to apply")
    ]
    for title, text in cases:
        eligible, analysis, reason = evaluate_experience_eligibility(text, title)
        assert eligible == True, f"Failed positive case: {title} | {reason}"

def test_negative_cases():
    cases = [
        ("Senior Software Engineer", "5+ years of experience required"),
        ("Staff Engineer", "8+ years experience"),
        ("Engineering Manager", "10+ years experience"),
        ("Software Engineer", "2+ years of professional experience required"),
        ("Backend Engineer", "minimum 1 year of experience required")
    ]
    for title, text in cases:
        eligible, analysis, reason = evaluate_experience_eligibility(text, title)
        assert eligible == False, f"Failed negative case: {title} | {reason}"

def test_tricky_semantic_cases():
    # 1. Preferred higher exp with new grads welcome -> ACCEPT
    el1, _, r1 = evaluate_experience_eligibility("2+ years preferred, but new graduates are welcome", "Software Engineer")
    assert el1 == True, f"Failed tricky case 1: {r1}"

    # 2. Contextual team mention -> DO NOT REJECT
    el2, _, r2 = evaluate_experience_eligibility("Our engineering team has 5+ years of experience building scalable systems.", "Software Engineer")
    assert el2 == True, f"Failed tricky case 2: {r2}"

    # 3. 1 year experience preferred -> ACCEPT
    el3, _, r3 = evaluate_experience_eligibility("1 year experience preferred", "Software Engineer")
    assert el3 == True, f"Failed tricky case 3: {r3}"

    # 4. 1 year experience required -> REJECT
    el4, _, r4 = evaluate_experience_eligibility("1 year experience required", "Software Engineer")
    assert el4 == False, f"Failed tricky case 4: {r4}"

    # 5. 1-2 years experience -> REJECT (since min is 1 yr and no explicit new grad override)
    el5, _, r5 = evaluate_experience_eligibility("1-2 years experience required in Python", "Backend Engineer")
    assert el5 == False, f"Failed tricky case 5: {r5}"

    # 6. 0-2 years experience -> ACCEPT
    el6, _, r6 = evaluate_experience_eligibility("0-2 years experience required", "Software Engineer")
    assert el6 == True, f"Failed tricky case 6: {r6}"

if __name__ == "__main__":
    test_positive_cases()
    test_negative_cases()
    test_tricky_semantic_cases()
    print("ALL EXPERIENCE CLASSIFIER TEST FIXTURES PASSED PERFECTLY!")
