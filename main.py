from fastapi import FastAPI
from routers import interview

app = FastAPI(title="Smart Interview Simulator")

app.include_router(interview.router)

@app.get("/health")
def health():
    return{"status":"ok"}