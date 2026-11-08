from contextlib import asynccontextmanager

from fastapi import FastAPI
import models
from db import init_db
from routers import interview, stats, resume
from pathlib import Path
from fastapi.responses import FileResponse
import asyncio
import os
from worker import run_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker_task = None
    if os.getenv("RUN_WORKER") == "1":
        worker_task = asyncio.create_task(run_worker())
    yield
    if worker_task:
        worker_task.cancel()    

app = FastAPI(title="Smart Interview Simulator", lifespan=lifespan)

app.include_router(interview.router)
app.include_router(stats.router)
app.include_router(resume.router)


@app.get("/health")
def health():
    return {"status": "ok"}

STATIC_DIR = Path(__file__).parent / "static"

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
