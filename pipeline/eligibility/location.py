import re
from typing import Tuple

INDIA_CITIES = {
    "bengaluru", "bangalore", "hyderabad", "pune", "gurugram", "gurgaon",
    "noida", "greater noida", "mumbai", "chennai", "delhi", "new delhi",
    "ncr", "kolkata", "ahmedabad", "jaipur", "kochi", "thiruvananthapuram",
    "chandigarh", "indore", "coimbatore", "nagpur", "bhubaneswar", "lucknow",
    "bhopal", "surat", "vadodara", "visakhapatnam", "vijayawada", "patna",
    "mysuru", "mysore", "mangaluru", "hubli", "belgaum", "navi mumbai",
    "thane", "belapur", "whitefield", "electronic city", "hsr layout",
    "koramangala", "madhapur", "gachibowli", "hitec city", "salt lake",
    "sector v", "ambattur", "tidel park", "cybercity", "dlf cyber city",
    "sambhajinagar", "aurangabad", "nashpur", "nagpur", "secunderabad",
    "yelahanka", "hebbal", "manyata", "panchkula", "mohali"
}

INDIA_SIGNALS = {
    "india", "bharat", "in - remote", "india remote", "remote - india",
    "remote, india", "india / remote", "india/remote", "pan india",
    "pan-india", "remote (india)", "india (remote)"
}

# Countries/regions that are definitively NOT India — hard reject
# NOTE: Do NOT use "in" as a check — it matches "Austin", "Berlin", "Finland" etc.
FOREIGN_REJECT = {
    "united states", "united kingdom", "uk", "usa", "u.s.a", "u.s.",
    "canada", "singapore", "germany", "australia", "france", "japan",
    "netherlands", "sweden", "switzerland", "denmark", "norway", "finland",
    "new zealand", "ireland", "spain", "italy", "brazil", "mexico",
    "poland", "czech", "romania", "ukraine", "israel", "uae", "dubai",
    "hong kong", "south korea", "taiwan", "china", "indonesia", "malaysia",
    "philippines", "thailand", "vietnam", "europe", "worldwide", "global",
    "austin", "seattle", "san francisco", "san jose", "new york",
    "london", "berlin", "paris", "toronto", "vancouver", "sydney",
    "melbourne", "dublin", "amsterdam", "stockholm", "zurich",
    "irvine", "bellevue", "redmond", "menlo park", "mountain view",
    "sunnyvale", "santa clara", "cupertino", "palo alto", "boston",
    "chicago", "los angeles", "denver", "atlanta", "dallas", "houston",
    "tel aviv", "singapore", "jakarta", "bangkok", "kuala lumpur",
    "manila", "ho chi minh", "beijing", "shanghai", "shenzhen", "seoul",
    "tokyo", "osaka", "moscow", "warsaw", "bucharest", "budapest",
    "barcelona", "madrid", "rome", "milan", "brussels", "vienna",
    "zurich", "geneva", "oslo", "copenhagen", "helsinki", "stockholm",
    "cape town", "johannesburg", "nairobi", "cairo", "lagos",
    "riyadh", "abu dhabi", "doha", "istanbul", "ankara"
}


def verify_location_eligibility(location: str) -> Tuple[str, str]:
    """
    Returns: (status, reasoning)
    status: "ELIGIBLE" | "INELIGIBLE" | "REVIEW"

    IMPORTANT: Does NOT use 'in' substring check — that incorrectly matches
    'Austin', 'Berlin', 'Finland', 'Dublin', 'Irvine' etc. as India.
    Only uses explicit city names and India signal phrases.
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

    # 3. Known India city keyword — ACCEPT
    for city in INDIA_CITIES:
        if city in loc_lower:
            return "ELIGIBLE", f"Matched India city ({city}): {location}"

    # 4. "Remote" alone with no country context — REVIEW (could be US-remote)
    if "remote" in loc_lower:
        return "REVIEW", f"Generic remote with no India confirmation: {location}"

    # 5. Everything else — REVIEW (quarantine, do not show to user)
    return "REVIEW", f"Location '{location}' cannot be confirmed as India-eligible"
