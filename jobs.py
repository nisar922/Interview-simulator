import json
import uuid

from redis_client import redis_client

QUEUE = "eval_queue"
RESULT_TTL = 60 * 60 * 24

async def enqueue_evaluation(questions: list, answers: list, role: str, user_id: str ="guest") -> str:
    interview_id = uuid.uuid4().hex
    job = {
        "id": interview_id,
        "user_id": user_id,
        "role": role,
        "questions": questions,
        "answer": answers,
        "attempts": 0,
    }
    await redis_client.set(
        f"result:{interview_id}", json.dumps({"status":"pending"}), ex=RESULT_TTL
    )
    await redis_client.lpush(QUEUE, json.dumps(job))
    return interview_id

async def get_result(interview_id: str):
    raw = await redis_client.get(f"result: {interview_id}")
    return json.loads(raw) if raw else None