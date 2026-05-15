from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


def test_internal_routes_require_token_when_configured() -> None:
    original_token = settings.kce_internal_token
    settings.kce_internal_token = "test-internal-token"
    client = TestClient(app)

    try:
        missing_token_response = client.post(
            "/internal/session/summarize",
            json={
                "session_goal": "Draft a Zhiguang reply.",
                "turns": [{"role": "user", "content": "Keep it concise."}],
            },
        )
        wrong_token_response = client.post(
            "/internal/session/summarize",
            headers={"Authorization": "Bearer wrong"},
            json={
                "session_goal": "Draft a Zhiguang reply.",
                "turns": [{"role": "user", "content": "Keep it concise."}],
            },
        )
        correct_token_response = client.post(
            "/internal/session/summarize",
            headers={"Authorization": "Bearer test-internal-token"},
            json={
                "session_goal": "Draft a Zhiguang reply.",
                "turns": [{"role": "user", "content": "Keep it concise."}],
            },
        )
        health_response = client.get("/health")
    finally:
        settings.kce_internal_token = original_token

    assert missing_token_response.status_code == 401
    assert wrong_token_response.status_code == 401
    assert correct_token_response.status_code == 200
    assert health_response.status_code == 200
