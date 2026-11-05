import json
import re

from llm import ask_llm

SYSTEM = (
    "You are a strict technical interviewer evaluating a fresher's answer. "
    "Reply with ONLY a JSON object with keys: "
    '"score" (integer 0-10), "feedback" (one short sentence), '
    '"topic" (one or two words, like "databases"). '
    "No markdown, no extra text."
)

def _clean(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        first_newline = raw.find("\n")
        if first_newline != -1:
            raw = raw[first_newline + 1:]
        else:
            raw = raw.removeprefix("```")
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()

async def evaluate_answer(question: str, answer: str) -> dict:
    prompt = f"Question: {question}\nCandidate answer: {answer}"
    try:
        cleaned = _clean(await ask_llm(SYSTEM, prompt))
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                raise
        score = max(0, min(10, int(data["score"])))
        return {
            "score": score,
            "feedback": str(data["feedback"]),
            "topic": str(data["topic"]),
        }
    except Exception as e:
        print("Evaluation fail:", e)
        return {"score": None, "feedback": "Evaluation unavailable", "topic": "unknown"}
