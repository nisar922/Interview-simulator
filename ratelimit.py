import os
from fastapi import HTTPException, Request
from redis_client import redis_client

DISABLED = os.getenv("DISABLE_RATE_LIMIT") == "1"



async def allow(key: str, limit: int, window: int) -> bool:
    if DISABLED:
        return True
    redis_key = f"rl:{key}"
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(redis_key)
        pipe.expire(redis_key, window, nx=True)
        count, _ = await pipe.execute()
    return count <= limit



def limit_by_ip(name: str, limit: int, window: int):
    async def dependency(request: Request):
        ip = request.client.host if request.client else "unknown"
        if not await allow(f"{name}:{ip}", limit, window):
            raise HTTPException(status_code=429, detail="Too many requests, try later")


    return dependency