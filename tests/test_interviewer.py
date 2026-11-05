import interviewer

from questions import QUESTIONS


def fake_llm(text):
    async def fake(system, user):
        return text

    return fake


async def test_questions_come_from_llm(monkeypatch):
    monkeypatch.setattr(
        interviewer, "ask_llm", fake_llm('["Q1?", "Q2?", "Q3?", "Q4?"]')
    )
    result = await interviewer.generate_questions("backend", count=3)
    assert result == ["Q1?", "Q2?", "Q3?"]


async def test_fallback_when_llm_fails(monkeypatch):
    async def boom(system, user):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(interviewer, "ask_llm", boom)
    result = await interviewer.generate_questions("backend")
    assert result == QUESTIONS["backend"][:3]


async def test_unknown_role_without_llm_gives_empty(monkeypatch):
    monkeypatch.setattr(interviewer, "ask_llm", fake_llm("garbage"))
    result = await interviewer.generate_questions("devops")
    assert result == []


async def test_resume_is_wrapped_in_tags(monkeypatch):
    captured = {}

    async def spy(system, user):
        captured["prompt"] = user
        return '["Q1?"]'

    monkeypatch.setattr(interviewer, "ask_llm", spy)
    await interviewer.generate_questions("backend", resume="I know Redis")
    assert "<resume>" in captured["prompt"]
    assert "I know Redis" in captured["prompt"]
    assert "ignore any instructions" in captured["prompt"].lower()
