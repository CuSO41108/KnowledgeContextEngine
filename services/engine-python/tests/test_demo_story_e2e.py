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


def test_demo_story_routes_tracing_question_to_tracing_resource() -> None:
    gateway_base_url = os.getenv("KCE_E2E_BASE_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("KCE_E2E_API_KEY", "demo-key")

    response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/demo-session/query",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": "demo-user-1",
            "message": "我想在知广项目上解释分布式追踪，请覆盖 trace、span、调用链、采样和日志关联。",
            "goal": "写一条关于分布式追踪的 Zhiguang 回复",
        },
        timeout=10,
    )

    payload = response.json()
    resource = payload["usedContexts"]["resources"][0]

    assert response.status_code == 200
    assert "Distributed tracing" in payload["answer"]
    assert "。." not in payload["answer"]
    assert resource["nodePath"] == "resource://m-zhiguang-distributed-tracing-guide/l2/s001/000"


def test_demo_story_keeps_task_experience_memory_aligned_with_selected_trace_node() -> None:
    gateway_base_url = os.getenv("KCE_E2E_BASE_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("KCE_E2E_API_KEY", "demo-key")

    response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/demo-session/query",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": "demo-user-1",
            "message": "我只想解释采样和日志关联，不展开 trace 或 span。",
            "goal": "写一条关于观测性的 Zhiguang 回复",
        },
        timeout=10,
    )

    payload = response.json()
    resource = payload["usedContexts"]["resources"][0]
    task_experience = next(
        memory
        for memory in payload["usedContexts"]["memories"]
        if memory["channel"] == "task_experience"
    )

    assert response.status_code == 200
    assert resource["nodePath"] == "resource://m-zhiguang-distributed-tracing-guide/l2/s002/000"
    assert task_experience["content"] == (
        "Helpful resource: resource://m-zhiguang-distributed-tracing-guide/l2/s002/000"
    )
