from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def generate_answer(prompt: str) -> str:
    response = client.models.generate_content(
        model="models/gemini-3.5-flash-lite",
        contents=prompt,
    )
    return response.text