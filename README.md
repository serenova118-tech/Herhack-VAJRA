# VAJRA — AI-Powered Digital Privacy & Exposure Protection

A beginner-friendly, runnable MVP for a women-focused digital privacy companion. It combines:
- Digital footprint checks (safe MVP: validates user-provided identifiers and optionally checks an email with the Have I Been Pwned API when you supply your own API key).
- File privacy scanning for images, PDFs and DOCX files (metadata + text/PII checks; OCR is optional).
- A transparent, rule-based risk score and practical recommendations.
- A simple dashboard and exposure findings view.

## Important scope and safety notes
This is an MVP, not a guarantee that all public information or fake accounts will be found. The footprint module does not scrape social networks or access private accounts. It only checks the user's own submitted identifiers and the optional official breach API. Do not scan someone else's personal information without permission. No passwords are requested. Uploaded files are processed by the backend; this starter does not save them permanently.

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

## 5. Optional breach API
The footprint scan works without an API key and will clearly say that live breach lookup is not configured. To enable it:
1. Obtain your own Have I Been Pwned API key from its official website and follow its terms.
2. Put it in `backend/.env` as `HIBP_API_KEY=your_key_here`.
3. Restart the backend.
Never put API keys in frontend code or commit `.env`.

## 6. What currently works
- Dashboard with empty state and scan totals during the current browser session.
- Upload and scan PNG/JPG/JPEG, PDF and DOCX.
- Image EXIF metadata inspection.
- PDF text and metadata inspection.
- DOCX text and core properties inspection.
- Email, phone-like string, and Indian PAN/Aadhaar-like pattern detection (pattern matches need human verification; not identity verification).
- Download a separate image copy with EXIF metadata removed.
- User-submitted email/username/profile URL validation and optional HIBP email lookup.
- Transparent risk scoring and recommendations.
- Responsive rose-pink / rose-gold visual theme inspired by the supplied VAJRA logo.

## 7. Not yet implemented
- Reliable social-platform profile discovery or impersonation verification.
- OCR on screenshots/scanned PDFs (install and integrate OCR in a later phase).
- PDF/DOCX visual redaction and complete metadata sanitization.
- Persistent accounts, database, scan history and cloud deployment.
- LLM chat assistant. Add it only after the deterministic scan pipeline works; keep its API key on the backend.
- The frontend currently keeps results in browser memory only.

## 8. Troubleshooting
- `py` not found: install Python and tick **Add Python to PATH**, then reopen VS Code.
- `npm` not found: install Node.js LTS, then reopen VS Code.
- CORS/network error: ensure backend terminal is running on port 8000.
- `ModuleNotFoundError`: activate the backend venv and run `pip install -r requirements.txt`.
- Port already in use: stop the old server with Ctrl+C or use another port.

## 9. Suggested next development order
1. Add tests and improve PII recognizers.
2. Add OCR and PDF scanned-page support.
3. Add visual redaction with preview and re-scan verification.
4. Add authenticated storage and user-controlled retention.
5. Add exposure graph and AI explanations grounded only in scan findings.
