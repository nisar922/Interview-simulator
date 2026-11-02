import json
from llm import ask_llm
from questions import QUESTIONS

SYSTEM = (
    "You are a technical interviewer. "
    "Reply with ONLY a JSON array of strings. No markdown, no extra text."
)

async def generate_questions(role: str, count: int = 3) -> list[str]:
    prompt = (
        f"Generate {count} short interview questions for a fresher "
        f"{role} developer. Use simple English."
    )
    try:
        raw = await ask_llm(SYSTEM, prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```")
        raw = raw.removesuffix("```").strip()
        questions = json.loads(raw)
        if isinstance(questions, list) and questions:
            return [str(q) for q in questions][:count]
    except Exception as e:
        print("LLM se sawal nahi bane:", e)
    return QUESTIONS.get(role, [])