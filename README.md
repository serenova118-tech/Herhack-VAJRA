# VAJRA — Digital Privacy & Exposure Check (student prototype)

A runnable prototype for self-check tool. It combines:
- **File privacy scanning** for images, PDFs and DOCX files: metadata inspection plus simple pattern checks for personal data.
- A **small footprint check** that validates identifiers you type in and, if you supply your own key, looks up one email in Have I Been Pwned.
- A **transparent, rule-based risk score** with practical recommendations.
- An optional **AI explanation** (Google Gemini) that rewrites the scanner's findings in plain language.

## Status at a glance

| Area | Status | What it really does |
|---|---|---|
| Image EXIF inspection | Implemented | Reads EXIF via Pillow; flags GPS coordinates and the presence of EXIF fields. Does not read XMP/IPTC. |
| PDF scan | Implemented (text layer only) | Extracts text and document properties with PyMuPDF; first 200 pages; encrypted PDFs are reported as unscanned. No OCR. |
| DOCX scan | Implemented | Body, tables, headers/footers and core properties. |
| PII patterns | Implemented, heuristic | Email, Indian mobile, PAN-like, Aadhaar-like (Verhoeff checksum). Matches need human review; no names/addresses. |
| EXIF-cleaned image copy | Implemented (PNG/JPEG) | Re-encodes pixels into a new image, applies orientation, verifies no metadata remains, returns it from memory. |
| Risk score | Implemented (heuristic) | Fixed category weights, each category counted once. Not validated against any dataset. |
| HIBP breach lookup | Partially implemented | Only if you add your own API key; looks up one email; shows breach names. |
| Username / profile URL checks | **Format validation only** | Nothing is searched, crawled or verified. |
| AI assessment | Implemented, explanation only | Gemini explains findings the rules already produced; it does not detect anything. |
| Exposure insights page | Partially implemented | A list of findings; no relationship graph. |
| Social-platform discovery / impersonation detection | Planned | Not implemented. |
| OCR, visual redaction, PDF/DOCX metadata removal | Planned | Not implemented. |
| Accounts, history, deployment hardening | Planned | Not implemented. |

## Privacy behaviour (what the code actually does)
- **Uploaded files** are read and analysed in memory. VAJRA's own code does not write them to disk. The web framework may spool larger uploads to the operating system's temporary folder while a request is in progress (Starlette default, not independently measured here) and removes them afterwards.
- **Cleaned images** are returned directly from memory; no copy is kept on the server. (Earlier versions saved them to `tmp_clean/` and never deleted them.)
- **Scan results** are held in your browser session only; the server stores no history.
- **AI feature:** when you click *Generate AI Assessment*, finding titles, categories, severities, recommendations and the score are sent to Google's Gemini API. File contents, matched values, filenames and the identifiers you typed are not sent. Do not use this button if you are not comfortable with that.
- **Breach lookup:** if enabled, the email you enter is sent to Have I Been Pwned.
- The frontend loads two fonts from Google Fonts, so your browser contacts Google when the page loads.
- No passwords are requested. No claim of anonymity or legal compliance is made.

## Important scope and safety notes
This is a prototype, not a guarantee that all public information or fake accounts will be found, and a "no findings" result does not mean a file is safe. The footprint module does not scrape social networks or access private accounts. Only scan your own information or information you have permission to check; the consent checkbox is a reminder, not a technical control.

## 1. Requirements
- Windows 10/11
- Python 3.10+ (3.11 recommended)
- Node.js 20+ and npm
- VS Code

## 2. Open the project
1. Extract `VAJRA.zip`.
2. Open VS Code.
3. Select **File → Open Folder** and choose the `VAJRA` folder.

## 3. Start the backend
Open a VS Code terminal (**Terminal → New Terminal**) and run:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

If PowerShell blocks activation, run this once in that terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Then activate again.

Backend runs at http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

## 4. Start the frontend
Keep the backend terminal running. Open a **second** VS Code terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (usually http://localhost:5173).

## 5. Optional breach API and AI
The footprint scan works without an API key and will clearly say that live breach lookup is not configured. To enable it:
1. Obtain your own Have I Been Pwned API key from its official website and follow its terms.
2. Put it in `backend/.env` as `HIBP_API_KEY=your_key_here`.
3. Restart the backend.
Never put API keys in frontend code or commit `.env`.

For AI explanations, add `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) to `backend/.env`. Model names change; run `python check_models.py` from `backend/` to list what your key can use. Without a key the AI button returns a clear "not configured" message and everything else works.

## 6. Tests
From `backend/` (after `pip install -r requirements.txt`):
```powershell
python -m unittest discover -s tests -t . -v
```
Unit tests cover risk scoring, PII patterns, upload validation, image scanning/cleaning and DOCX scanning. HTTP-level tests in `tests/test_api.py` run when FastAPI is installed. There are no frontend tests and the Gemini and HIBP calls are not tested against the live services.

## 7. Known limitations
- No authentication, rate limiting or HTTPS: **do not deploy publicly as is.** Anyone who can reach the API could query breach status for any email.
- Pattern detection will miss data in images/scans (no OCR) and will miss names, addresses and free-text identifiers.
- The dashboard and report pages show the score of the latest single scan while listing findings from both scans (frontend behaviour; see docs).
- Score weights and thresholds are authors' judgement, not scientifically validated.

## 8. Troubleshooting
- `py` not found: install Python and tick **Add Python to PATH**, then reopen VS Code.
- `npm` not found: install Node.js LTS, then reopen VS Code.
- CORS/network error: ensure the backend is running on port 8000 and your frontend origin is listed in `VAJRA_ALLOWED_ORIGINS`.
- `ModuleNotFoundError`: activate the backend venv and run `pip install -r requirements.txt`.
- Port already in use: stop the old server with Ctrl+C or use another port.

## 9. Licences
PyMuPDF is distributed under AGPL-3.0 (or a commercial licence). That is fine for local study use, but review it before distributing or hosting VAJRA as a service. Other dependencies are permissive (verify against each package before release). See `docs/` for details.
