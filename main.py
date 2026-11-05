from contextlib import asynccontextmanager

from fastapi import FastAPI
import models
from db import init_db
from routers import interview, stats, resume

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        print(f"Database init warning: {e}")
    yield

app = FastAPI(title="Smart Interview Simulator", lifespan=lifespan)

app.include_router(interview.router)
app.include_router(stats.router)
app.include_router(resume.router)


@app.get("/health")
def health():
    return {"status": "ok"}
