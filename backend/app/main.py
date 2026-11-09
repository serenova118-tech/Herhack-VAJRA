from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
import httpx
import os
import uuid
import asyncio
from .ai_engine import analyze_privacy_scan

from .schemas import FootprintRequest
from .scanners import scan_image, scan_pdf, scan_docx
from .risk import calculate_risk
from .config import HIBP_API_KEY

app = FastAPI(title="VAJRA Privacy API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_BYTES = 10 * 1024 * 1024
ALLOWED = {".png", ".jpg", ".jpeg", ".pdf", ".docx"}
CLEAN_DIR = Path("tmp_clean")
CLEAN_DIR.mkdir(exist_ok=True)

@app.get("/")
def home():
    return {"service": "VAJRA Privacy API", "status": "running"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/files/scan")
async def file_scan(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Supported formats: PNG, JPG, JPEG, PDF and DOCX.")
    content = await file.read()
    if not content or len(content) > MAX_BYTES:
        raise HTTPException(400, "File is empty or larger than the 10 MB limit.")
    temp_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_path = Path(tmp.name)
        if suffix in {".png", ".jpg", ".jpeg"}:
            details, findings = scan_image(temp_path)
        elif suffix == ".pdf":
            details, findings = scan_pdf(temp_path)
        else:
            details, findings = scan_docx(temp_path)
        risk = calculate_risk(findings)
        return {
            "scan_id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_type": suffix[1:].upper(),
            "details": details,
            "findings": findings,
            "risk": risk,
            "notice": "Pattern matches are clues, not proof. OCR and complete visual redaction are not included in this MVP."
        }
    except Exception as exc:
        raise HTTPException(422, f"Could not safely read this file: {str(exc)[:180]}")
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)

@app.post("/api/files/clean-image")
async def clean_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(400, "Metadata cleaning currently supports PNG and JPEG images.")
    content = await file.read()
    if not content or len(content) > MAX_BYTES:
        raise HTTPException(400, "File is empty or larger than the 10 MB limit.")
    output = CLEAN_DIR / f"{uuid.uuid4()}{suffix}"
    try:
        from io import BytesIO
        with Image.open(BytesIO(content)) as image:
            clean = image.copy()
            clean.save(output, format="PNG" if suffix == ".png" else "JPEG", quality=95)
        return FileResponse(output, filename=f"vajra_cleaned{suffix}", media_type="application/octet-stream")
    except Exception as exc:
        output.unlink(missing_ok=True)
        raise HTTPException(422, f"Image cleaning failed: {str(exc)[:150]}")

@app.post("/api/footprint/scan")
async def footprint_scan(payload: FootprintRequest):
    if not any([payload.email, payload.username, payload.profile_url]):
        raise HTTPException(400, "Enter at least one email, username or public profile URL.")
    findings = []
    messages = []
    if payload.username:
        messages.append("Username recorded for a future supported-source lookup; this MVP does not scrape social platforms.")
    if payload.profile_url:
        messages.append("Profile URL format accepted. The page is not crawled or authenticated.")
    if payload.email:
        if HIBP_API_KEY:
            headers = {"hibp-api-key": HIBP_API_KEY, "user-agent": "VAJRA-Privacy-Research-MVP"}
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{payload.email}",
                    headers=headers,
                    params={"truncateResponse": "true"}
                )
            if response.status_code == 200:
                breaches = response.json()
                findings.append({
                    "title": f"Email appeared in {len(breaches)} breach record(s)",
                    "category": "breach",
                    "risk_category": "breach",
                    "severity": "High",
                    "evidence": "Breach names and dates are available from the official API response.",
                    "recommendation": "Change reused passwords, enable MFA, and review affected accounts."
                })
                messages.append("Live breach lookup completed through the configured HIBP API.")
            elif response.status_code == 404:
                messages.append("HIBP reported no matching breach in its available dataset.")
            else:
                messages.append(f"HIBP lookup could not be completed (HTTP {response.status_code}).")
        else:
            messages.append("Live breach lookup is not configured. Add your own HIBP API key to backend/.env.")
    return {
        "scan_id": str(uuid.uuid4()),
        "submitted": {"email": payload.email, "username": payload.username, "profile_url": payload.profile_url},
        "findings": findings,
        "risk": calculate_risk(findings),
        "messages": messages,
        "notice": "This is not a complete internet-wide search. Only supported and authorized sources are checked."
    }
@app.post("/api/ai/analyze")
async def ai_privacy_analysis(payload: dict = Body(...)):

    findings = payload.get("findings", [])
    risk = payload.get("risk", {})

    if not isinstance(findings, list):
        raise HTTPException(400, "Invalid findings data.")

    # Send only selected finding fields to AI.
    safe_findings = []

    for finding in findings[:30]:
        if not isinstance(finding, dict):
            continue

        safe_findings.append({
            "title": str(finding.get("title", ""))[:150],
            "category": str(finding.get("category", ""))[:80],
            "risk_category": str(finding.get("risk_category", ""))[:80],
            "severity": str(finding.get("severity", ""))[:30],
            "recommendation": str(
                finding.get("recommendation", "")
            )[:250]
        })

    safe_data = {
        "risk": {
            "score": risk.get("score", 0),
            "level": risk.get("level", "Unknown")
        },
        "findings": safe_findings
    }

    try:
        analysis = await asyncio.to_thread(
            analyze_privacy_scan,
            safe_data
        )

        return {
            "status": "success",
            "ai_analysis": analysis
        }

    except Exception as exc:
        raise HTTPException(
            502,
            f"AI analysis failed: {str(exc)[:200]}"
        )