import asyncio
import logging
import uuid
from pathlib import Path
from urllib.parse import quote


import httpx
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .ai_engine import AIGenerationError, AIUnavailableError, analyze_privacy_scan
from .config import ALLOWED_ORIGINS, HIBP_API_KEY, MAX_UPLOAD_BYTES
from .risk import calculate_risk
from .sanitize import clean_image_bytes
from .scanners import scan_docx, scan_image, scan_pdf
from .schemas import FootprintRequest
from .uploads import UploadError, read_limited, validate_content

logger = logging.getLogger("vajra")

app = FastAPI(title="VAJRA Privacy API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED = {".png", ".jpg", ".jpeg", ".pdf", ".docx"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
_MULTIPART_OVERHEAD = 1024 * 1024


# Registered before CORS so that CORS stays outermost and error responses
# from this check still carry CORS headers.
@app.middleware("http")
async def reject_oversized_uploads(request, call_next):
    if request.url.path.startswith("/api/files/"):
        declared = request.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES + _MULTIPART_OVERHEAD:
            limit_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
            return JSONResponse(
                {"detail": f"File is larger than the {limit_mb} MB limit."}, status_code=413)
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # the frontend does not use cookies
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def home():
    return {"service": "VAJRA Privacy API", "status": "running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _scan_bytes(data: bytes, suffix: str):
    if suffix in IMAGE_SUFFIXES:
        return scan_image(data)
    if suffix == ".pdf":
        return scan_pdf(data)
    return scan_docx(data)


@app.post("/api/files/scan")
async def file_scan(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Supported formats: PNG, JPG, JPEG, PDF and DOCX.")
    try:
        # The file is processed in memory and not written to disk by VAJRA.
        content = await read_limited(file, MAX_UPLOAD_BYTES)
        validate_content(content, suffix)
        details, findings = await asyncio.to_thread(_scan_bytes, content, suffix)
    except UploadError as exc:
        raise HTTPException(exc.status_code, exc.message)
    except Exception:
        logger.exception("File scan failed")
        raise HTTPException(
            422, "Could not safely read this file. It may be corrupted, encrypted or unsupported.")
    finally:
        await file.close()
    return {
        "scan_id": str(uuid.uuid4()),
        "filename": file.filename,
        "file_type": suffix[1:].upper(),
        "details": details,
        "findings": findings,
        "risk": calculate_risk(findings),
        "notice": "Pattern matches are clues, not proof. OCR and complete visual redaction are not included in this MVP.",
    }


@app.post("/api/files/clean-image")
async def clean_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in IMAGE_SUFFIXES:
        raise HTTPException(400, "Metadata cleaning currently supports PNG and JPEG images.")
    try:
        content = await read_limited(file, MAX_UPLOAD_BYTES)
        validate_content(content, suffix)
        cleaned, fmt = await asyncio.to_thread(clean_image_bytes, content)
    except UploadError as exc:
        raise HTTPException(exc.status_code, exc.message)
    except Exception:
        logger.exception("Image cleaning failed")
        raise HTTPException(422, "Image cleaning failed. The file may be corrupted or unsupported.")
    finally:
        await file.close()
    out_suffix = ".png" if fmt == "PNG" else ".jpg"
    # Returned straight from memory: no cleaned copy is kept on the server.
    return Response(
        content=cleaned,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="vajra_cleaned{out_suffix}"',
            "Cache-Control": "no-store",
        },
    )


async def _hibp_lookup(email: str):
    """Return (finding_or_None, message). Never raises for network problems."""
    headers = {"hibp-api-key": HIBP_API_KEY, "user-agent": "VAJRA-Privacy-Research-MVP"}
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{quote(email, safe='')}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers, params={"truncateResponse": "true"})
    except httpx.HTTPError:
        logger.warning("HIBP request failed")
        return None, "Breach lookup could not reach the HIBP service. Try again later."
    if response.status_code == 200:
        try:
            names = [b.get("Name", "") for b in response.json() if isinstance(b, dict)]
        except ValueError:
            names = []
        names = [n for n in names if n]
        finding = {
            "title": f"Email appeared in {len(names)} breach record(s)",
            "category": "breach",
            "risk_category": "breach",
            "severity": "High",
            "evidence": ("Breach names reported by Have I Been Pwned: " + ", ".join(names[:10])
                         + (" and more." if len(names) > 10 else ".")),
            "recommendation": "Change reused passwords, enable MFA, and review affected accounts.",
        }
        return finding, "Live breach lookup completed through the configured HIBP API (source: haveibeenpwned.com)."
    if response.status_code == 404:
        return None, "HIBP reported no matching breach in its available dataset."
    if response.status_code == 401:
        return None, "HIBP rejected the configured API key."
    if response.status_code == 429:
        return None, "HIBP rate limit reached. Try again shortly."
    return None, f"HIBP lookup could not be completed (HTTP {response.status_code})."


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
            finding, message = await _hibp_lookup(payload.email)
            if finding:
                findings.append(finding)
            messages.append(message)
        else:
            messages.append("Live breach lookup is not configured. Add your own HIBP API key to backend/.env.")
    return {
        "scan_id": str(uuid.uuid4()),
        "submitted": {"email": payload.email, "username": payload.username, "profile_url": payload.profile_url},
        "findings": findings,
        "risk": calculate_risk(findings),
        "messages": messages,
        "notice": "This is not a complete internet-wide search. Only supported and authorized sources are checked.",
    }


@app.post("/api/ai/analyze")
async def ai_privacy_analysis(payload: dict = Body(...)):
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        raise HTTPException(400, "Invalid findings data.")

    # Allow-list of fields sent to the AI. Matched values ("evidence"), filenames
    # and submitted identifiers are never included.
    safe_findings = []
    for finding in findings[:30]:
        if not isinstance(finding, dict):
            continue
        safe_findings.append({
            "title": str(finding.get("title", ""))[:150],
            "category": str(finding.get("category", ""))[:80],
            "risk_category": str(finding.get("risk_category", ""))[:80],
            "severity": str(finding.get("severity", ""))[:30],
            "recommendation": str(finding.get("recommendation", ""))[:250],
        })

    # Recompute the score from the findings actually being explained rather than
    # trusting a client-supplied number.
    risk = calculate_risk(safe_findings)
    safe_data = {"risk": {"score": risk["score"], "level": risk["level"]}, "findings": safe_findings}

    try:
        analysis = await asyncio.wait_for(
            asyncio.to_thread(analyze_privacy_scan, safe_data), timeout=45)
    except AIUnavailableError:
        raise HTTPException(503, "AI explanations are not configured on this server.")
    except (AIGenerationError, asyncio.TimeoutError):
        raise HTTPException(502, "The AI service did not return an explanation. Your scan results are unaffected.")
    except Exception:
        logger.exception("AI analysis failed")
        raise HTTPException(502, "The AI service could not generate an explanation right now. Your scan results are unaffected.")
    return {"status": "success", "ai_analysis": analysis}
