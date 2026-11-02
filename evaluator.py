import json

from llm import ask_llm

SYSTEM = (
    "You are a strict technical interviewer evaluating a fresher's answer. "
    "Reply with ONLY a JSON object with keys: "
    '"score" (integer 0-10), "feedback" (one short sentence), '
    '"topic" (one or two words, like "databases"). '
    "No markdown, no extra text."
)

def _clean(raw: str) -> str:
    raw = raw.strip().removeprefix("```json").removeprefix("```")
    return raw.removesuffix("```").strip()

async def evaluate_answer(question: str, answer: str) -> dict:
    prompt = f"Question: {question}\nCandidate answer: {answer}"
    try:
        data = json.loads(_clean(await ask_llm(SYSTEM, prompt)))
        score = max(0, min(10, int(data["score"])))
        return {
            "score": score,
            "feedback": str(data["feedback"]),
            "topic": str(data["topic"]),
        }
    except Exception as e:
        print("Evaluation fail:", e)
        return {"score": None, "feedback": "Evaluation unavailable", "topic": "unknown"}