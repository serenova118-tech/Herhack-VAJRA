
import json
from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL


def analyze_privacy_scan(scan_data: dict) -> str:
    """
    Generate an AI explanation of VAJRA scan findings.
    Only sanitized findings and risk information are sent to Gemini.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key is missing from backend/.env")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are VAJRA, an AI-powered digital privacy and safety assistant.

Analyze the following cybersecurity privacy scan results.

SCAN DATA:
{json.dumps(scan_data, indent=2)}

YOUR TASK:
1. Explain the overall privacy risk in simple language.
2. Explain each detected finding and its possible impact.
3. Give practical, personalized steps to reduce the risks.
4. If there are no findings, clearly say:
   "No matching privacy issues were detected in this scan."
5. Explain that no findings does not guarantee complete online safety.
6. Never invent breaches, exposures, or scan results.
7. Do not claim that a username or profile was searched if it was not.
8. Keep the response clear, supportive and useful.

Use these headings:

### AI Privacy Assessment
### What Your Results Mean
### Recommended Actions
### Important Safety Note
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=800
        )
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text
