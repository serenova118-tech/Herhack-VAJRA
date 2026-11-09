import re
from pathlib import Path
from PIL import Image
import fitz
from docx import Document

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)")
PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.I)
AADHAAR_RE = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")

def pii_findings(text: str):
    findings = []
    patterns = [
        ("email", EMAIL_RE, "direct_contact", "Email address pattern detected"),
        ("phone", PHONE_RE, "direct_contact", "Possible Indian mobile number detected"),
        ("PAN-like", PAN_RE, "identity_document", "PAN-like pattern detected"),
        ("Aadhaar-like", AADHAAR_RE, "identity_document", "12-digit Aadhaar-like pattern detected"),
    ]
    for kind, pattern, category, message in patterns:
        matches = list(dict.fromkeys(pattern.findall(text)))
        for match in matches[:10]:
            findings.append({
                "title": message,
                "category": kind,
                "risk_category": category,
                "severity": "High" if category == "identity_document" else "Moderate",
                "evidence": f"Matched value: {match[:3]}••••",
                "recommendation": "Review whether this information needs to be visible before sharing."
            })
    return findings

def scan_image(path: Path):
    findings = []
    details = {"format": None, "width": None, "height": None, "metadata": []}
    with Image.open(path) as image:
        details.update({"format": image.format, "width": image.width, "height": image.height})
        exif = image.getexif()
        if exif:
            for key, value in exif.items():
                # Avoid displaying raw binary metadata.
                if isinstance(value, (str, int, float)):
                    details["metadata"].append({"tag": str(key), "value": str(value)[:120]})
            gps = exif.get(34853)
            if gps:
                findings.append({
                    "title": "GPS metadata may be present",
                    "category": "location metadata",
                    "risk_category": "precise_location",
                    "severity": "High",
                    "evidence": "Image contains a GPS metadata block.",
                    "recommendation": "Remove location metadata before sharing if it is not needed."
                })
            findings.append({
                "title": "Image contains EXIF metadata",
                "category": "device metadata",
                "risk_category": "device_metadata",
                "severity": "Low",
                "evidence": f"{len(exif)} EXIF fields detected.",
                "recommendation": "Consider sharing a metadata-cleaned copy."
            })
    return details, findings

def scan_pdf(path: Path):
    findings = []
    text = ""
    with fitz.open(path) as doc:
        metadata = doc.metadata or {}
        for page in doc:
            text += page.get_text() + "\n"
    findings.extend(pii_findings(text))
    return {"pages": len(fitz.open(path)), "metadata": {k: str(v)[:150] for k, v in metadata.items() if v}}, findings

def scan_docx(path: Path):
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            text += "\n" + " ".join(cell.text for cell in row.cells)
    findings = pii_findings(text)
    props = doc.core_properties
    metadata = {"author": props.author, "last_modified_by": props.last_modified_by, "title": props.title, "subject": props.subject}
    if any(metadata.values()):
        findings.append({
            "title": "Document author or descriptive metadata is present",
            "category": "document metadata",
            "risk_category": "device_metadata",
            "severity": "Low",
            "evidence": "One or more document properties are populated.",
            "recommendation": "Review document properties before publishing."
        })
    return {"paragraphs": len(doc.paragraphs), "metadata": metadata}, findings
