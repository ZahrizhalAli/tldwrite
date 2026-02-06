import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

print(os.getenv("GEMINI_API_KEY"))