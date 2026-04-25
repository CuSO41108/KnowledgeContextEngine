from __future__ import annotations

import os

import httpx


def test_demo_story_returns_personalized_traceable_answer() -> None:
    gateway_base_url = os.getenv("KCE_E2E_BASE_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("KCE_E2E_API_KEY", "demo-key")

    response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/demo-session/query",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": "demo-user-1",
            "message": "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?",
            "goal": "write a Zhiguang reply about Redis cache-aside",
        },
        timeout=10,
    )

    payload = response.json()
    resource = payload["usedContexts"]["resources"][0]

    assert response.status_code == 200
    assert "Zhiguang" in payload["answer"]
    assert resource["nodePath"] == "resource://z-zhiguang-redis-cache-playbook/l2/s001/000"
    assert resource["drilldownTrail"] == [
        "resource://z-zhiguang-redis-cache-playbook/l0/root",
        "resource://z-zhiguang-redis-cache-playbook/l1/s001",
        "resource://z-zhiguang-redis-cache-playbook/l2/s001/000",
    ]
    assert any(
        memory["channel"] == "task_experience"
        for memory in payload["usedContexts"]["memories"]
    )
    assert payload["usedContexts"]["resources"][0]["traceNodeId"]
