import asyncio
import json

from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from evaluator import evaluate_answer
from jobs import QUEUE, RESULT_TTL
from redis_client import redis_client
from db import SessionLocal
from models import AnswerRecord, Interview

MAX_ATTEMPTS = 3

async def save_to_db(job: dict, report: dict):
    async with SessionLocal() as session:
        session.add(
            Interview(
                id=job["id"],
                user_id=job.get("user_id", "guest"),
                role=job.get("role", "unknown"),
                status="done",
                average=report["average"],
                answers=[
                    AnswerRecord(
                        question=d["question"],
                        answer=d["answer"],
                        score=d["score"],
                        feedback=d["feedback"],
                        topic=d["topic"],
                    )
                    for d in report["details"]
                ],
            )
        )
        await session.commit()


async def process(job: dict):
    questions = job.get("questions", [])
    answers = job.get("answers", job.get("answer", []))
    results = await asyncio.gather(
        *(evaluate_answer(q, a) for q, a in zip(questions, answers))
    )
    scores = [r["score"] for r in results if r.get("score") is not None]
    if not scores:
        raise RuntimeError("LLM unavailable, no scores")
    report = {
        "status": "done",
        "average": round(sum(scores) / len(scores), 1),
        "details": [
            {"question": q, "answer": a, **r}
            for q, a, r in zip(questions, answers, results)
        ],
    }
    await redis_client.set(
        f"result:{job['id']}", json.dumps(report), ex=RESULT_TTL
    )
    await save_to_db(job, report)

async def main():
    print("Worker started, waiting for jobs...")
    while True:
        try:
            item = await redis_client.brpop(QUEUE, timeout=5)
        except (RedisTimeoutError, RedisConnectionError) as e:
            print("Redis problem, retrying", e)
            await asyncio.sleep(2)
            continue

        if item is None:
            continue

        job = json.loads(item[1])
        try:
            await process(job)
            print("Done:", job["id"])
        except Exception as e:
            job["attempts"] = job.get("attempts", 0) + 1
            print(f"Failed ({job['attempts']}/{MAX_ATTEMPTS}):", e)
            if job["attempts"] < MAX_ATTEMPTS:
                await asyncio.sleep(2 * job["attempts"])
                await redis_client.lpush(QUEUE, json.dumps(job))
            else:
                await redis_client.set(
                    f"result:{job['id']}",
                    json.dumps({"status": "failed"}),
                    ex=RESULT_TTL,
                )

if __name__ == "__main__":
    asyncio.run(main())
