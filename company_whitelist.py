# Registry of Top Product-Based Tech Companies in India & Ingestion Endpoints

PRODUCT_COMPANIES = {
    "Amazon": {"type": "Product", "tier": "FAANG / Big Tech"},
    "Microsoft": {"type": "Product", "tier": "Big Tech"},
    "Google": {"type": "Product", "tier": "FAANG / Big Tech"},
    "Adobe": {"type": "Product", "tier": "Tier-1 Product"},
    "Uber": {"type": "Product", "tier": "Tier-1 Product"},
    "Atlassian": {"type": "Product", "tier": "Tier-1 Product"},
    "Razorpay": {"type": "Product", "tier": "FinTech Unicorn", "greenhouse_token": "razorpaysoftwareprivatelimited"},
    "Groww": {"type": "Product", "tier": "FinTech Unicorn", "greenhouse_token": "groww"},
    "Flipkart": {"type": "Product", "tier": "E-Commerce Giant"},
    "Swiggy": {"type": "Product", "tier": "Unicorn"},
    "Zomato": {"type": "Product", "tier": "Unicorn"},
    "Cred": {"type": "Product", "tier": "FinTech Unicorn"},
    "PhonePe": {"type": "Product", "tier": "FinTech Unicorn"},
    "Meesho": {"type": "Product", "tier": "E-Commerce Unicorn"},
    "Paytm": {"type": "Product", "tier": "FinTech Giant"},
    "Zerodha": {"type": "Product", "tier": "FinTech Giant"},
    "Arcesium": {"type": "Product", "tier": "Quant / FinTech"},
    "DE Shaw": {"type": "Product", "tier": "Quant / FinTech"},
    "Goldman Sachs": {"type": "Product", "tier": "Investment Banking Tech"},
    "Walmart Global Tech": {"type": "Product", "tier": "Retail Tech Giant"},
    "PayPal": {"type": "Product", "tier": "FinTech Giant"},
    "Cisco": {"type": "Product", "tier": "Networking Tech Giant"},
    "Salesforce": {"type": "Product", "tier": "SaaS Giant"},
    "Oracle": {"type": "Product", "tier": "Database / Cloud Giant"}
}

SERVICE_COMPANIES_BLACKLIST = {
    "tcs", "tata consultancy services", "infosys", "wipro", "hcl", "hcltech",
    "cognizant", "cts", "accenture", "capgemini", "lti", "l&t infotech",
    "mindtree", "lti mindtree", "mphasis", "hexaware", "dxc", "dxc technology",
    "genpact", "tech mahindra", "persistent systems", "cyient", "birlasoft"
}

def is_product_company(company_name):
    if not company_name:
        return False, "Unknown Company"
    name_lower = company_name.lower().strip()
    
    # Blacklist Check
    for s in SERVICE_COMPANIES_BLACKLIST:
        if s in name_lower:
            return False, f"Service-Based IT Company ({company_name})"

    # Whitelist Check
    for p, info in PRODUCT_COMPANIES.items():
        if p.lower() in name_lower or name_lower in p.lower():
            return True, f"Whitelisted Product Company: {p} ({info['tier']})"

    return True, "Product-Based Tech Company"
