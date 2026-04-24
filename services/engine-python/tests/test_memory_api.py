from fastapi.testclient import TestClient

from app.main import app


def test_memory_extract_endpoint_returns_dual_channel_candidates() -> None:
    client = TestClient(app)

    response = client.post(
        "/internal/memory/extract",
        json={
            "session_goal": "Draft a reply to Zhiguang about Java cache design.",
            "turns": [
                {
                    "role": "user",
                    "content": "Please keep the explanation concise and focused on Java implementation details.",
                },
                {
                    "role": "assistant",
                    "content": "I can draft a concise Java-focused reply.",
                },
            ],
            "selected_resource_paths": ["resource://zhiguang-java-cache-playbook/l2/s000/000"],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["candidate_count"] >= 3
    assert any(
        candidate["channel"] == "user"
        and candidate["memory_type"] == "explanation_preference"
        and "concise" in candidate["content"].lower()
        for candidate in payload["candidates"]
    )
    assert any(
        candidate["channel"] == "task_experience"
        and candidate["memory_type"] == "successful_resource"
        and candidate["content"] == "Helpful resource: resource://zhiguang-java-cache-playbook/l2/s000/000"
        for candidate in payload["candidates"]
    )


def test_session_summarize_endpoint_returns_goal_focused_summary() -> None:
    client = TestClient(app)

    response = client.post(
        "/internal/session/summarize",
        json={
            "session_goal": "Draft a reply to Zhiguang with a concise Java explanation.",
            "turns": [
                {"role": "user", "content": "Need a reply to Zhiguang with a concise Java explanation."},
                {"role": "assistant", "content": "I'll keep it concise and Java-focused."},
                {"role": "user", "content": "By the way, the weather is nice today."},
                {"role": "assistant", "content": "Yes, sunny afternoons are pleasant."},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert "Zhiguang" in payload["summary"]
    assert "concise Java" in payload["summary"]
    assert "weather" not in payload["summary"].lower()
