from fastapi import APIRouter
from sqlalchemy import func, select

from db import SessionLocal
from models import AnswerRecord, Interview


router = APIRouter()



@router.get("/users/{user_id}/weak-areas")
async def weak_areas(user_id: str):
    topic = func.lower(AnswerRecord.topic)
    query = (
        select(
            topic,
            func.avg(AnswerRecord.score),
            func.count(AnswerRecord.id),
        )
        .join(Interview, Interview.id == AnswerRecord.interview_id)
        .where(Interview.user_id == user_id, AnswerRecord.score.is_not(None))
        .group_by(topic)
        .order_by(func.avg(AnswerRecord.score))
    )
    async with SessionLocal() as session:
        rows = (await session.execute(query)).all()
    return [
        {"topic": t, "avg_score": round(float(avg), 1), "answers": n}
        for t, avg, n in rows
    ]



@router.get("/users/{user_id}/interviews")
async def history(user_id: str):
    query = (
        select(Interview)
        .where(Interview.user_id == user_id)
        .order_by(Interview.created_at.desc())
        .limit(20)
    )

    async with SessionLocal() as session:
        interviews = (await session.execute(query)).scalars().all()
    return [
        {
            "id": i.id,
            "role": i.role,
            "average": i.average,
            "created_at": i.created_at,
        }
        for i in interviews
    ]