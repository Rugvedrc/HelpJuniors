import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from pipeline.eligibility.education import verify_education_eligibility

def test_education_positive_cases():
    cases = [
        ("Software Engineer", "Bachelor's degree in Computer Science or related field required"),
        ("SDE I", "B.Tech / M.Tech in CS/IT or equivalent experience"),
        ("Applied Scientist", "Bachelor's, Master's, or PhD in Machine Learning"),
        ("Backend Engineer", "B.E./B.Tech in Computer Science required"),
        ("AI Engineer", "Undergraduate degree in Computer Science")
    ]
    for title, text in cases:
        eligible, analysis, reason = verify_education_eligibility(text, title)
        assert eligible == True, f"Failed positive education case: {title} | {reason}"

def test_education_negative_cases():
    cases = [
        ("Research Scientist", "PhD degree required in Computer Science"),
        ("Applied Scientist II", "Doctorate degree required in Machine Learning"),
        ("ML Researcher", "Master's degree required in Artificial Intelligence")
    ]
    for title, text in cases:
        eligible, analysis, reason = verify_education_eligibility(text, title)
        assert eligible == False, f"Failed negative education case: {title} | {reason}"

if __name__ == "__main__":
    test_education_positive_cases()
    test_education_negative_cases()
    print("ALL EDUCATION CLASSIFIER TEST FIXTURES PASSED PERFECTLY!")
