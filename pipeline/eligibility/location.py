import re
from typing import Tuple

INDIA_CITIES = {
    "bengaluru", "bangalore", "hyderabad", "pune", "gurugram", "gurgaon",
    "noida", "mumbai", "chennai", "delhi", "kolkata", "ahmedabad",
    "jaipur", "kochi", "thiruvananthapuram", "chandigarh", "indore",
    "coimbatore", "nagpur", "bhubaneswar", "lucknow", "bhopal",
    "surat", "vadodara", "visakhapatnam", "vijayawada", "patna",
    "mysuru", "mysore", "mangaluru", "hubli", "belgaum"
}

INDIA_SIGNALS = {"india", "bharat", "in - remote", "india remote", "remote - india", "remote, india"}

# Countries/regions that are definitively NOT India
FOREIGN_REJECT = {
    "united states", "united kingdom", "uk", "usa", "u.s.a", "u.s.", "us ",
    "canada", "singapore", "germany", "australia", "france", "japan",
    "netherlands", "sweden", "switzerland", "denmark", "norway", "finland",
    "new zealand", "ireland", "spain", "italy", "brazil", "mexico",
    "poland", "czech", "romania", "ukraine", "israel", "uae", "dubai",
    "hong kong", "south korea", "taiwan", "china", "indonesia", "malaysia",
    "philippines", "thailand", "vietnam", "europe"
}


def verify_location_eligibility(location: str) -> Tuple[str, str]:
    """
    Returns: (status, reasoning)
    status: "ELIGIBLE" | "INELIGIBLE" | "REVIEW"
    """
    if not location or location.strip() == "":
        return "REVIEW", "No location provided — cannot confirm India eligibility"

    loc_lower = location.lower().strip()

    # 1. Explicit foreign rejection — HARD REJECT
    for foreign in FOREIGN_REJECT:
        if foreign in loc_lower:
            return "INELIGIBLE", f"Foreign location: {location}"

    # 2. Explicit India signal — ACCEPT
    for signal in INDIA_SIGNALS:
        if signal in loc_lower:
            return "ELIGIBLE", f"Confirmed India location: {location}"

    # 3. Known India city — ACCEPT
    for city in INDIA_CITIES:
        if city in loc_lower:
            return "ELIGIBLE", f"Matched India city ({city}): {location}"

    # 4. "Remote" alone with no country context — REVIEW, not India
    if "remote" in loc_lower:
        return "REVIEW", f"Generic remote with no India confirmation: {location}"

    # 5. Everything else — REVIEW
    return "REVIEW", f"Location '{location}' cannot be confirmed as India-eligible"
