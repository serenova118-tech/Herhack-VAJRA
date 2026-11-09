from typing import List, Dict

WEIGHTS = {
    "precise_location": 25,
    "identity_document": 25,
    "direct_contact": 20,
    "breach": 20,
    "profile_linking": 10,
    "device_metadata": 8,
}

def calculate_risk(findings: List[Dict]) -> dict:
    # Cap each category at its weight so repeated matches do not inflate the score.
    used = set()
    score = 0
    for finding in findings:
        category = finding.get("risk_category")
        if category in WEIGHTS and category not in used:
            score += WEIGHTS[category]
            used.add(category)
    score = min(100, score)
    if score < 25:
        level = "Low"
    elif score < 50:
        level = "Moderate"
    elif score < 75:
        level = "High"
    else:
        level = "Critical"
    return {"score": score, "level": level, "method": "Transparent category-weighted MVP score"}
