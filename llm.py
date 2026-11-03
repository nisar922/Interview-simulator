import os
import asyncio
import random
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "openai/gpt-oss-20b"
MOCK_LLM = os.getenv("MOCK_LLM") == "1"

async def ask_llm(system: str, user: str) -> str:
    if MOCK_LLM:
        await asyncio.sleep(random.uniform(0.5, 1.5))
        if "JSON array" in system:
            return '["Question one?", "Question two?","Question three?"]'
        return'{"score": 7, "feedback":"mock feedback", "topic":"mock"}'
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content": system},
            {"role":"user","content": user},

        ],
    )
    return response.choices[0].message.content