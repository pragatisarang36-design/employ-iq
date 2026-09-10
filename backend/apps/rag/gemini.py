"""Optional Gemini generation; retrieval and citations stay in Django."""
import os


def generate_grounded_answer(question: str, source_text: str, role_name: str | None = None) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = ("You are EmployIQ's career learning assistant. Use only the supplied curated context, "
                  "do not estimate placement probability, and give concise practical advice. "
                  f"Role: {role_name or 'not specified'}\nQuestion: {question}\nCurated context:\n{source_text}")
        response = client.models.generate_content(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt)
        return (response.text or "").strip() or None
    except Exception:
        # Django's cited deterministic fallback keeps the demo available when provider calls fail.
        return None
