import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from interviewer import generate_questions
from jobs import enqueue_evaluation, get_result
from resume_service import load_resume

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
    role = ""
    user_id = "guest"
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            msg_type = data.get("type")

            if msg_type == "start":
                resume_text = None
                if data.get("resume_id"):
                    resume_text = await load_resume(data["resume_id"])
                role = data.get("role", "")
                user_id = data.get("user_id", "guest")
                questions = await generate_questions(role, resume=resume_text)
                answers = []
                if not questions:
                    await websocket.send_json(
                        {"type": "error", "message": "Role nahi mila"}
                    )
                    continue
                await websocket.send_json(
                    {"type": "question", "index": 0, "text": questions[0]}
                )
            elif msg_type == "answer":
                if not questions:
                    await websocket.send_json(
                        {"type": "error", "message": "Pehle start bhejo"}
                    )
                    continue
                answers.append(data.get("text", ""))
                if len(answers) < len(questions):
                    i = len(answers)
                    await websocket.send_json(
                        {"type": "question", "index": i, "text": questions[i]}
                    )
                else:
                    interview_id = await enqueue_evaluation(
                        questions, answers, role, user_id=user_id
                    )
                    await websocket.send_json(
                        {"type": "processing", "interview_id": interview_id}
                    )
            elif msg_type in ("finish", "submit"):
                if questions and answers:
                    interview_id = await enqueue_evaluation(
                        questions, answers, role, user_id=user_id
                    )
                    await websocket.send_json(
                        {"type": "processing", "interview_id": interview_id}
                    )
                else:
                    await websocket.send_json(
                        {"type": "error", "message": "Koi jawab nahi mile"}
                    )
            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Unknown message type: {msg_type}"}
                )

    except WebSocketDisconnect:
        print("Client disconnect ho gya")
