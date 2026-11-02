import json
import asyncio
from evaluator import evaluate_answer
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from questions import QUESTIONS
from interviewer import generate_questions

router = APIRouter()

@router.websocket("/ws/interview")
async def interview_ws(websocket: WebSocket):
    await websocket.accept()
    questions = []
    answers = []
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            if data["type"] == "start":
                questions = await generate_questions(data["role"])
                answers = []
                if not questions:
                    await websocket.send_json(
                        {"type": "error", "message": "Role nahi mila"}
                    )
                    continue
                await websocket.send_json(
                    {"type": "question", "index": 0, "text": questions[0]}
                )
            elif data["type"] == "answer":
                if not questions:
                    await websocket.send_json(
                        {"type": "error", "message": "Pehle start bhejo"}
                    )
                    continue
                answers.append(data["text"])
                if len(answers) < len(questions):
                    i = len(answers)
                    await websocket.send_json(
                        {"type": "question", "index": i, "text": questions[i]}
                    )
            else:
                results = await asyncio.gather(
                    *(evaluate_answer(q, a) for q, a in zip(questions, answers))
                )
                scores = [r["score"] for r in results if r["score"] is not None]
                average = round(sum(scores) / len(scores), 1) if scores else None
                await websocket.send_json(
                    {
                        "type": "report",
                        "average": average,
                        "details": [
                            {"question": q, "answer": a, **r}
                           for q, a, r in zip(questions, answers, results)
                        ],
                   }
                )

    except WebSocketDisconnect:
        print("Client disconnect ho gya")            