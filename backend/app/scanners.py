from io import BytesIO

from PIL import Image

from .pii import pii_findings  # re-exported for backwards compatibility
from .uploads import check_image_size

MAX_PDF_PAGES = 200
MAX_TEXT_CHARS = 5_000_000

GPS_IFD = 0x8825  # EXIF pointer to the GPS sub-block (decimal 34853)
GPS_LATITUDE, GPS_LONGITUDE = 2, 4


def _finding(title, category, risk_category, severity, evidence, recommendation):
    return {
        "title": title,
        "category": category,
        "risk_category": risk_category,
        "severity": severity,
        "evidence": evidence,
        "recommendation": recommendation,
    }


def scan_image(data: bytes):
    findings = []
    details = {"format": None, "width": None, "height": None, "metadata": []}
    with Image.open(BytesIO(data)) as image:
        check_image_size(image.width, image.height)
        details.update({"format": image.format, "width": image.width, "height": image.height})
        exif = image.getexif()
        if exif:
            for key, value in exif.items():
                # Avoid displaying raw binary metadata.
                if isinstance(value, (str, int, float)):
                    details["metadata"].append({"tag": str(key), "value": str(value)[:120]})
            gps = {}
            try:
                gps = dict(exif.get_ifd(GPS_IFD))
            except Exception:
                gps = {}
            if GPS_LATITUDE in gps and GPS_LONGITUDE in gps:
                findings.append(_finding(
                    "GPS location found in image metadata", "location metadata",
                    "precise_location", "High",
                    "Image metadata contains latitude and longitude fields.",
                    "Remove location metadata before sharing if it is not needed."))
            elif GPS_IFD in exif:
                findings.append(_finding(
                    "GPS metadata block present but no coordinates found",
                    "location metadata", "device_metadata", "Low",
                    "A GPS block exists but latitude/longitude fields were not found.",
                    "Consider sharing a metadata-cleaned copy."))
            findings.append(_finding(
                "Image contains EXIF metadata", "device metadata", "device_metadata", "Low",
                f"{len(exif)} EXIF fields detected.",
                "Consider sharing a metadata-cleaned copy."))
    return details, findings


def scan_pdf(data: bytes):
    import fitz  # PyMuPDF; imported lazily so other scanners work without it

    findings = []
    notes = []
    text_parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        if doc.needs_pass:
            findings.append(_finding(
                "PDF is password-protected; contents were not scanned",
                "scan limitation", None, "Low",
                "VAJRA cannot read encrypted PDFs.",
                "Scan an unprotected copy if you want its contents checked."))
            return {"pages": None, "encrypted": True, "metadata": {}}, findings
        raw_meta = doc.metadata or {}
        pages = len(doc)
        total = 0
        for index, page in enumerate(doc):
            if index >= MAX_PDF_PAGES:
                notes.append(f"Only the first {MAX_PDF_PAGES} pages were scanned.")
                break
            page_text = page.get_text()
            total += len(page_text)
            text_parts.append(page_text)
            if total > MAX_TEXT_CHARS:
                notes.append("Text scanning stopped at a size limit.")
                break
    text = "\n".join(text_parts)
    if pages and not text.strip():
        notes.append("No extractable text layer found; scanned/image-only pages are not "
                     "analysed because OCR is not implemented.")
    findings.extend(pii_findings(text))
    metadata = {k: str(v)[:150] for k, v in raw_meta.items() if v}
    if any(raw_meta.get(k) for k in ("author", "title", "subject", "keywords")):
        findings.append(_finding(
            "Document author or descriptive metadata is present", "document metadata",
            "device_metadata", "Low", "One or more document properties are populated.",
            "Review document properties before publishing."))
    details = {"pages": pages, "metadata": metadata}
    if notes:
        details["notes"] = notes
    return details, findings


def scan_docx(data: bytes):
    from docx import Document

    doc = Document(BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" ".join(cell.text for cell in row.cells))
    for section in doc.sections:  # headers/footers often hold names and phone numbers
        for part in (section.header, section.footer):
            parts.extend(p.text for p in part.paragraphs)
    text = "\n".join(parts)[:MAX_TEXT_CHARS]
    findings = pii_findings(text)
    props = doc.core_properties
    metadata = {
        "author": props.author, "last_modified_by": props.last_modified_by,
        "title": props.title, "subject": props.subject,
    }
    if any(metadata.values()):
        findings.append(_finding(
            "Document author or descriptive metadata is present", "document metadata",
            "device_metadata", "Low", "One or more document properties are populated.",
            "Review document properties before publishing."))
    return {"paragraphs": len(doc.paragraphs), "metadata": metadata}, findings
