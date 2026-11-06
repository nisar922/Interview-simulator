import json
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from interviewer import generate_questions
from jobs import enqueue_evaluation, get_result
from resume_service import load_resume
from stt import transcribe


router = APIRouter()

MAX_AUDIO_BYTES = 5 * 1024 * 1024



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
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break


            if message.get("bytes") is not None:
                audio = message["bytes"]
                if not questions:
                    await websocket.send_json(
                        {"type": "error", "message": "Pehle start bhejo"}
                    )
                    continue
                if len(audio) > MAX_AUDIO_BYTES:
                    await websocket.send_json(
                        {"type": "error", "message": "Audio too long, please type"}
                    )
                    continue
                try:
                    text = await transcribe(audio)
                except Exception as e:
                    print("Transcription failed:", e)
                    await websocket.send_json(
                        {"type": "error", "message": "Could not transcribe, please type"}
                    )
                    continue
                await websocket.send_json({"type": "transcript", "text": text})
                continue

            data = json.loads(message["text"])


            if data["type"] == "start":
                role = data["role"]
                resume_text = None
                if data.get("resume_id"):
                    resume_text = await load_resume(data["resume_id"])
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
                        {"type": "processing", "interview_id": interview_id}
                    )
    except WebSocketDisconnect:
        print("Client disconnect ho gaya")