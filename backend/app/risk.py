from typing import Dict, List

# Heuristic category weights chosen by the authors. They are NOT statistically
# derived or validated. "profile_linking" is reserved: no scanner emits it yet.
WEIGHTS = {
    "precise_location": 25,
    "identity_document": 25,
    "direct_contact": 20,
    "breach": 20,
    "profile_linking": 10,
    "device_metadata": 8,
}

METHOD = "Transparent category-weighted MVP score"


def calculate_risk(findings: List[Dict]) -> dict:
    """Each risk category counts once, however many findings it has, so repeated
    matches do not inflate the score. Findings without a known risk_category
    (informational notes, unverified matches) do not affect the score.
    Pass the findings of several scans together to get one combined score.
    """
    used = []
    for finding in findings:
        category = finding.get("risk_category") if isinstance(finding, dict) else None
        if category in WEIGHTS and category not in used:
            used.append(category)
    score = min(100, sum(WEIGHTS[c] for c in used))
    if score < 25:
        level = "Low"
    elif score < 50:
        level = "Moderate"
    elif score < 75:
        level = "High"
    else:
        level = "Critical"
    return {
        "score": score,
        "level": level,
        "method": METHOD,
        "breakdown": [{"category": c, "points": WEIGHTS[c]} for c in used],
    }
