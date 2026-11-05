import evaluator


def fake_llm(text):
    async def fake(system, user):
        return text

    return fake


async def test_valid_answer(monkeypatch):
    monkeypatch.setattr(
        evaluator,
        "ask_llm",
        fake_llm('{"score": 8, "feedback": "Good", "topic": "databases"}'),
    )
    result = await evaluator.evaluate_answer("Q?", "A")
    assert result == {"score": 8, "feedback": "Good", "topic": "databases"}


async def test_score_is_clamped_to_ten(monkeypatch):
    monkeypatch.setattr(
        evaluator,
        "ask_llm",
        fake_llm('{"score": 15, "feedback": "ok", "topic": "api"}'),
    )
    result = await evaluator.evaluate_answer("Q?", "A")
    assert result["score"] == 10


async def test_markdown_wrapper_is_removed(monkeypatch):
    monkeypatch.setattr(
        evaluator,
        "ask_llm",
        fake_llm('```json\n{"score": 5, "feedback": "ok", "topic": "api"}\n```'),
    )
    result = await evaluator.evaluate_answer("Q?", "A")
    assert result["score"] == 5


async def test_bad_output_gives_none_score(monkeypatch):
    monkeypatch.setattr(evaluator, "ask_llm", fake_llm("not json at all"))
    result = await evaluator.evaluate_answer("Q?", "A")
    assert result["score"] is None
    assert result["topic"] == "unknown"
