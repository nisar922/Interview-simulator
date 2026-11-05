import os
import asyncio
import random
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MOCK_LLM = os.getenv("MOCK_LLM", "0").lower() in ("1", "true", "yes")

_client = None

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
    
    client = get_client()
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""
