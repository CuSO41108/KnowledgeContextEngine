from __future__ import annotations

import os
from uuid import uuid4

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


def test_demo_story_routes_queue_subtopic_to_delivery_section() -> None:
    gateway_base_url = os.getenv("KCE_E2E_BASE_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("KCE_E2E_API_KEY", "demo-key")

    response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/demo-session/query",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": "demo-user-1",
            "message": "我只想解释重复消费、幂等和死信队列，不展开削峰填谷。",
            "goal": "写一条关于消息队列的 Zhiguang 回复",
        },
        timeout=10,
    )

    payload = response.json()
    resource = payload["usedContexts"]["resources"][0]

    assert response.status_code == 200
    assert "At-least-once delivery" in payload["answer"]
    assert resource["nodePath"] == "resource://n-zhiguang-message-queue-delivery-guide/l2/s002/000"


def test_demo_story_routes_search_subtopic_to_ranking_section() -> None:
    gateway_base_url = os.getenv("KCE_E2E_BASE_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("KCE_E2E_API_KEY", "demo-key")

    response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/demo-session/query",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": "demo-user-1",
            "message": "我只想解释排序信号和增量刷新，不展开倒排索引。",
            "goal": "写一条关于搜索索引的 Zhiguang 回复",
        },
        timeout=10,
    )

    payload = response.json()
    resource = payload["usedContexts"]["resources"][0]

    assert response.status_code == 200
    assert "Ranking combines term matching" in payload["answer"]
    assert resource["nodePath"] == "resource://o-zhiguang-search-indexing-guide/l2/s002/000"


def test_public_session_flow_persists_turn_memory_and_trace_surfaces() -> None:
    gateway_base_url = os.getenv("KCE_E2E_BASE_URL", "http://localhost:8080").rstrip("/")
    api_key = os.getenv("KCE_E2E_API_KEY", "demo-key")
    session_suffix = uuid4().hex[:8]
    session_id = f"public-e2e-{session_suffix}"
    external_user_id = f"public-e2e-user-{session_suffix}"
    goal = "write a Zhiguang reply about Redis cache-aside"
    message = "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?"

    create_response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": external_user_id,
            "sessionId": session_id,
            "goal": goal,
        },
        timeout=10,
    )

    create_payload = create_response.json()

    assert create_response.status_code == 200
    assert create_payload["sessionId"] == session_id
    assert create_payload["created"] is True
    assert create_payload["turnCount"] == 0

    tree_response = httpx.get(
        f"{gateway_base_url}/api/v1/resources/z-zhiguang-redis-cache-playbook/tree",
        headers={"X-API-Key": api_key},
        timeout=10,
    )
    tree_payload = tree_response.json()

    assert tree_response.status_code == 200
    assert tree_payload["resourceId"] == "z-zhiguang-redis-cache-playbook"
    assert any(
        node["nodePath"] == "resource://z-zhiguang-redis-cache-playbook/l2/s001/000"
        for node in tree_payload["nodes"]
    )

    query_response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/{session_id}/query",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": external_user_id,
            "message": message,
            "goal": goal,
        },
        timeout=10,
    )
    query_payload = query_response.json()
    resource = query_payload["usedContexts"]["resources"][0]

    assert query_response.status_code == 200
    assert resource["nodePath"] == "resource://z-zhiguang-redis-cache-playbook/l2/s001/000"
    assert resource["traceNodeId"]

    commit_response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/{session_id}/commit",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": external_user_id,
            "userMessage": message,
            "assistantAnswer": query_payload["answer"],
            "traceId": query_payload["traceId"],
            "goal": goal,
        },
        timeout=10,
    )
    commit_payload = commit_response.json()

    assert commit_response.status_code == 200
    assert commit_payload["status"] == "ok"
    assert commit_payload["sessionId"] == session_id
    assert commit_payload["committedMemoryCount"] >= 3

    trace_response = httpx.get(
        f"{gateway_base_url}/api/v1/traces/{query_payload['traceId']}",
        headers={"X-API-Key": api_key},
        timeout=10,
    )
    trace_payload = trace_response.json()

    assert trace_response.status_code == 200
    assert trace_payload["traceId"] == query_payload["traceId"]
    assert trace_payload["nodeSnapshots"][0]["nodeId"] == resource["nodeId"]

    trace_node_response = httpx.get(
        f"{gateway_base_url}/api/v1/traces/{query_payload['traceId']}/nodes/{resource['nodeId']}",
        headers={"X-API-Key": api_key},
        timeout=10,
    )
    trace_node_payload = trace_node_response.json()

    assert trace_node_response.status_code == 200
    assert trace_node_payload["nodePath"] == resource["nodePath"]

    resource_node_response = httpx.get(
        f"{gateway_base_url}/api/v1/resources/nodes/{resource['nodeId']}",
        headers={"X-API-Key": api_key},
        timeout=10,
    )
    resource_node_payload = resource_node_response.json()

    assert resource_node_response.status_code == 200
    assert resource_node_payload["nodePath"] == resource["nodePath"]

    ensure_again_response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": external_user_id,
            "sessionId": session_id,
            "goal": goal,
        },
        timeout=10,
    )
    ensure_again_payload = ensure_again_response.json()

    assert ensure_again_response.status_code == 200
    assert ensure_again_payload["created"] is False
    assert ensure_again_payload["turnCount"] == 1
    assert ensure_again_payload["summary"]

    follow_up_response = httpx.post(
        f"{gateway_base_url}/api/v1/sessions/{session_id}/query",
        headers={"X-API-Key": api_key},
        json={
            "provider": "demo_local",
            "externalUserId": external_user_id,
            "message": "Make it even shorter for Zhiguang.",
            "goal": goal,
        },
        timeout=10,
    )
    follow_up_payload = follow_up_response.json()

    assert follow_up_response.status_code == 200
    assert any(
        memory["channel"] == "task_experience"
        for memory in follow_up_payload["usedContexts"]["memories"]
    )
