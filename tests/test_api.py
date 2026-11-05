from fastapi.testclient import TestClient

from main import app

client = TestClient(app)
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
def test_resume_rejects_non_pdf():
    response = client.post(
        "/resume", files={"file": ("notes.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400