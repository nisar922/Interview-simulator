import asyncio
import random

from llm import MOCK_LLM, _client

STT_MODEL = "whisper-larger-v3-turbo"

async def transcribe(audio: bytes) -> str:
    if MOCK_LLM:
        await asyncio.sleep(random.uniform(0.3, 0.8))
        return "this is a mock transcript."
    result = await _client.audio.transcriptions.create(
        file=("answer.webm",audio, "audio/webm"),
        model=STT_MODEL,
        language="en",
    )
    return result.text.strip()