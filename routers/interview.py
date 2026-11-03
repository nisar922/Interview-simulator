import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from interviewer import generate_questions
import asyncio
from interviewer import generate_questions
from jobs import enqueue_evaluation, get_result

router = APIRouter()

@router.get("/interviews/{interview_id}")
async def interview_result(interview_id: str):
    result = await get_result(interview_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    return result

@router.websocket("/ws/interview")
async def interview_ws(websocket: WebSocket):
    await websocket.accept()
    questions = []
    answers = []
    role = " "
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            if data["type"] == "start":
                questions = await generate_questions(data["role"])
                role = data["role"]
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
                interview_id = await enqueue_evaluation(questions, answers, role)
                await websocket.send_json(
                    {"type":"processing", "interview_id": interview_id}
                )

    except WebSocketDisconnect:
        print("Client disconnect ho gya")            