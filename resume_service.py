import io
import uuid

from pypdf import PdfReader

from redis_client import redis_client

MAX_CHARS = 4000
RESUME_TTL = 60 * 60


def extract_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages[:5]]
    return "\n".join(pages).strip()[:MAX_CHARS]

async def save_resume(text: str) -> str:
    resume_id = uuid.uuid4().hex
    await redis_client.set(f"resume:{resume_id}", text, ex=RESUME_TTL)
    return resume_id

async def load_resume(resume_id: str) -> str | None:
    return await redis_client.get(f"resume:{resume_id}")