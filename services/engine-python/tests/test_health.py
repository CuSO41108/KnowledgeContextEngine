from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_engine_metadata() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "engine-python",
        "mode": "standalone",
    }
