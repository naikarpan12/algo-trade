from fastapi.testclient import TestClient

from app.main import app


def test_health_defaults_to_paper_mode():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["trading_mode"] in ("paper", "live")
