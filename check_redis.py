import asyncio
from redis_client import redis_client

async def main():
    print(await redis_client.ping())
    await redis_client.set("hello","world")
    print(await redis_client.get("hello"))
    await redis_client.aclose()

asyncio.run(main())    