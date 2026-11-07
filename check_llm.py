import asyncio
from llm import ask_llm

async def main():
    try:
        reply = await ask_llm(
            "tum ek strict backend interviewer ho.",
            "ek chhota interview sawal pucho.",
        )
        print(reply)
    except Exception as e:
        print("ERROR TYPE:", type(e).__name__)
        print("MESSAGE:",e)    

asyncio.run(main())    