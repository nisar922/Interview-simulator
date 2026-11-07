import asyncio

from fastapi import APIRouter, HTTPException, UploadFile, Depends

from resume_service import extract_text, save_resume

from ratelimit import limit_by_ip

router = APIRouter()

MAX_BYTES = 2 * 1024 * 1024

@router.post("/resume", dependencies=[Depends(limit_by_ip("resume", 10, 3600))])
async def upload_resume(file: UploadFile):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 2 MB)")
    try:
        text = await asyncio.to_thread(extract_text, data)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read this PDF")
    if not text:
        raise HTTPException(status_code=400, detail="No text found (scanned PDF?)")
    resume_id = await save_resume(text)
    return {"resume_id": resume_id, "chars": len(text)}