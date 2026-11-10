"""Pattern-based PII detection (regular expressions plus light validation).

These are heuristics. A match is a clue that needs human review, not proof that
a value is a real identifier, and absence of a match proves nothing.
"""
import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
# Indian mobile numbers: optional +91 / 91 / 0 prefix, 10 digits starting 6-9,
# optionally written as 5+5 digits ("98765 43210").
PHONE_RE = re.compile(r"(?<!\d)(?:(?:\+91|91|0)[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
# PAN: 5 letters, 4 digits, 1 letter. The 4th letter encodes the holder type;
# the allowed set below follows commonly published descriptions of the format.
PAN_RE = re.compile(r"\b[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z]\b", re.I)
AADHAAR_RE = re.compile(r"(?<!\d)[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")

_MASK = "\u2022" * 5

# Verhoeff checksum tables (Aadhaar numbers carry a Verhoeff check digit).
_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_valid(number: str) -> bool:
    if not number.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def verhoeff_check_digit(number: str) -> int:
    """Check digit to append to `number` (used by tests to build valid samples)."""
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return _INV[c]


def _finding(title, category, risk_category, severity, match, recommendation):
    return {
        "title": title,
        "category": category,
        "risk_category": risk_category,
        "severity": severity,
        "evidence": f"Matched value: {match[:3]}{_MASK}",
        "recommendation": recommendation,
    }


def pii_findings(text: str):
    findings = []
    review = "Review whether this information needs to be visible before sharing."

    simple = [
        ("email", EMAIL_RE, "direct_contact", "Email address pattern detected"),
        ("phone", PHONE_RE, "direct_contact", "Possible Indian mobile number detected"),
        ("PAN-like", PAN_RE, "identity_document", "PAN-like pattern detected"),
    ]
    for kind, pattern, category, message in simple:
        for match in list(dict.fromkeys(pattern.findall(text)))[:10]:
            severity = "High" if category == "identity_document" else "Moderate"
            findings.append(_finding(message, kind, category, severity, match, review))

    for match in list(dict.fromkeys(AADHAAR_RE.findall(text)))[:10]:
        digits = re.sub(r"\D", "", match)
        if verhoeff_valid(digits):
            findings.append(_finding(
                "12-digit Aadhaar-like number detected (checksum valid)",
                "Aadhaar-like", "identity_document", "High", match, review))
        else:
            # Not scored: many 12-digit strings (order IDs, reference numbers)
            # are not Aadhaar numbers. A mistyped real number also lands here.
            findings.append(_finding(
                "12-digit number resembling an Aadhaar (checksum not valid)",
                "Aadhaar-like (unverified)", None, "Low", match,
                "Check whether this is an identity number; if so, treat it as sensitive."))
    return findings
