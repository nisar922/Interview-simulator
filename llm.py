import os
import asyncio
import random
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

MODEL = "openai/gpt-oss-20b"
MOCK_LLM = os.getenv("MOCK_LLM") == "1"

_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"], timeout=20.0, max_retries=1)

def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        _client = AsyncGroq(api_key=api_key)
    return _client

async def ask_llm(system: str, user: str) -> str:
    if MOCK_LLM:
        await asyncio.sleep(random.uniform(0.1, 0.5))
        if "JSON array" in system:
            return '["Question one?", "Question two?", "Question three?"]'
        return '{"score": 7, "feedback": "mock feedback", "topic": "mock"}'
    response = await _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content 
