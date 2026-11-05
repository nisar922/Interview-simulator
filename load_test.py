import asyncio
import json
import math
import statistics
import sys
import time

import httpx
import websockets

WS_URL = "ws://127.0.0.1:8000/ws/interview"
HTTP_URL = "http://127.0.0.1:8000"


async def one_interview(client: httpx.AsyncClient):
    last_answer_at = time.perf_counter()
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps({"type": "start", "role": "backend"}))
        msg = json.loads(await ws.recv())
        while msg.get("type") == "question":
            await ws.send(json.dumps({"type": "answer", "text": "Sample answer"}))
            last_answer_at = time.perf_counter()
            msg = json.loads(await ws.recv())
        if msg.get("type") != "processing":
            return None
        interview_id = msg.get("interview_id")

    deadline = time.perf_counter() + 120
    while time.perf_counter() < deadline:
        r = await client.get(f"{HTTP_URL}/interviews/{interview_id}")
        if r.status_code == 200:
            status = r.json().get("status")
            if status == "done":
                return time.perf_counter() - last_answer_at
            if status == "failed":
                return None
        await asyncio.sleep(0.2)
    return None


async def main(n: int):
    async with httpx.AsyncClient() as client:
        start = time.perf_counter()
        results = await asyncio.gather(*(one_interview(client) for _ in range(n)))
        total = time.perf_counter() - start

    ok = sorted(r for r in results if r is not None)
    print(f"{len(ok)}/{n} interviews completed in {total:.1f}s")
    if ok:
        p95 = ok[max(0, math.ceil(0.95 * len(ok)) - 1)]
        print(
            f"report ready after last answer: median {statistics.median(ok):.2f}s, p95 {p95:.2f}s"
        )


if __name__ == "__main__":
    try:
        users = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    except ValueError:
        users = 10

    asyncio.run(main(users))
