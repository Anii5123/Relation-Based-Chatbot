import google.generativeai as genai
import os
from dotenv import load_dotenv

# Force v1 endpoint (optional, usually not needed with latest SDK)
os.environ["GOOGLE_API_USE_V1_ENDPOINT_OVERRIDE"] = "true"

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Use model name directly (no "models/")
model = genai.GenerativeModel("gemini-2.0-flash")

response = model.generate_content("Hello from Gemini using v1!")
print(response.text)
