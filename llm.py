import os
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "openai/gpt-oss-20b"

async def ask_llm(system: str, user: str) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role":"system","content": system},
            {"role":"user","content": user},

        ],
    )
    return response.choices[0].message.content