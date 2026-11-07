import json


from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from interviewer import generate_questions
from jobs import enqueue_evaluation, get_result
from ratelimit import allow
from resume_service import load_resume
from stt import transcribe


router = APIRouter()

MAX_AUDIO_BYTES = 5 * 1024 * 1024
MAX_ANSWER_CHARS = 2000
INTERVIEWS_PER_HOUR = 5
AUDIO_CLIPS_PER_HOUR = 40



@router.get("/interviews/{interview_id}")
async def interview_result(interview_id: str):
    result = await get_result(interview_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    return result



async def send_error(websocket: WebSocket, message: str):
    await websocket.send_json({"type": "error", "message": message})



@router.websocket("/ws/interview")
async def interview_ws(websocket: WebSocket):
    await websocket.accept()
    ip = websocket.client.host if websocket.client else "unknown"
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
                    await send_error(websocket, "Pehle start bhejo")
                    continue
                if len(audio) > MAX_AUDIO_BYTES:
                    await send_error(websocket, "Audio too long, please type")
                    continue
                if not await allow(f"audio:{ip}", AUDIO_CLIPS_PER_HOUR, 3600):
                    await send_error(websocket, "Voice limit reached, please type")
                    continue
                try:
                    text = await transcribe(audio)
                except Exception as e:
                    print("Transcription failed:", e)
                    await send_error(websocket, "Could not transcribe, please type")
                    continue
                await websocket.send_json({"type": "transcript", "text": text})
                continue

            try:
                data = json.loads(message.get("text") or "")
                if not isinstance(data, dict):
                    raise ValueError
            except ValueError:
                await send_error(websocket, "Invalid message")
                continue


            kind = data.get("type")

            if kind == "start":
                if not await allow(f"start:{ip}", INTERVIEWS_PER_HOUR, 3600):
                    await send_error(websocket, "Too many interviews, try later")
                    continue
                role = str(data.get("role", "")).strip()[:50]
                if not role:
                    await send_error(websocket, "Role nahi mila")
                    continue
                resume_id = data.get("resume_id")
                resume_text = await load_resume(str(resume_id)) if resume_id else None
                questions = await generate_questions(role, resume=resume_text)
                answers = []
                if not questions:
                    await send_error(websocket, "Role nahi mila")
                    continue
                await websocket.send_json(
                    {"type": "question", "index": 0, "text": questions[0]}
                )


            elif kind == "answer":
                if not questions:
                    await send_error(websocket, "Pehle start bhejo")
                    continue
                text = str(data.get("text", "")).strip()[:MAX_ANSWER_CHARS]
                if not text:
                    continue
                answers.append(text)
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
                    questions = []
                    answers = []
    except WebSocketDisconnect:
        print("Client disconnect ho gaya")