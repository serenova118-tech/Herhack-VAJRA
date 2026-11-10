import sys

from google import genai

from app.config import GEMINI_API_KEY

if not GEMINI_API_KEY:
    sys.exit("GEMINI_API_KEY is not set in backend/.env")

client = genai.Client(api_key=GEMINI_API_KEY)

print("\nAVAILABLE GEMINI MODELS:\n")

for model in client.models.list():
    actions = model.supported_actions or []

    if "generateContent" in actions:
        print(model.name)