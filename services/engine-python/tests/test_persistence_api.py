from fastapi.testclient import TestClient

from app.main import app


USER_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"
SESSION_KEY = "demo-history"
PROVIDER = "demo_local"
EXTERNAL_USER_ID = "demo-user-1"
GOAL = "write a Zhiguang reply about Redis cache-aside"


def test_provider_resource_tree_and_node_routes_return_persisted_resource_surface() -> None:
    client = TestClient(app)

    index_response = client.post(
        "/internal/resources/index",
        json={
            "provider": PROVIDER,
            "resource_slug": "persisted-zhiguang-cache",
            "markdown": (
                "# Zhiguang Cache Guide\n"
                "## Redis Cache Aside\n"
                "Redis cache-aside keeps the database authoritative."
            ),
            "source_uri": "file:///demo/persisted-zhiguang-cache.md",
        },
    )

    assert index_response.status_code == 200

    provider_trees_response = client.get(f"/internal/resources/providers/{PROVIDER}/trees")
    assert provider_trees_response.status_code == 200
    provider_payload = provider_trees_response.json()

    assert provider_payload["provider"] == PROVIDER
    assert provider_payload["resources"][0]["resourceId"] == "persisted-zhiguang-cache"
    assert any(
        node["title"] == "Redis Cache Aside"
        for node in provider_payload["resources"][0]["nodes"]
    )
    assert any(
        node["content"] == "Redis cache-aside keeps the database authoritative."
        for node in provider_payload["resources"][0]["nodes"]
    )

    resource_tree_response = client.get("/internal/resources/persisted-zhiguang-cache/tree")
    assert resource_tree_response.status_code == 200
    resource_tree_payload = resource_tree_response.json()

    assert resource_tree_payload["resourceId"] == "persisted-zhiguang-cache"
    assert resource_tree_payload["nodes"][2]["nodePath"] == (
        "resource://persisted-zhiguang-cache/l2/s000/000"
    )
    assert "content" not in resource_tree_payload["nodes"][2]

    node_response = client.get("/internal/resources/nodes/persisted-zhiguang-cache:l2:s000:000")
    assert node_response.status_code == 200
    node_payload = node_response.json()

    assert node_payload["nodeId"] == "persisted-zhiguang-cache:l2:s000:000"
    assert "database authoritative" in node_payload["snapshotContent"]


def test_commit_route_persists_session_summary_memories_and_trace_snapshots() -> None:
    client = TestClient(app)

    index_response = client.post(
        "/internal/resources/index",
        json={
            "provider": PROVIDER,
            "resource_slug": "persisted-query-doc",
            "markdown": (
                "# Redis Cache\n"
                "## Cache Aside\n"
                "Redis cache-aside keeps DB authoritative."
            ),
        },
    )
    assert index_response.status_code == 200

    session_response = client.post(
        "/internal/sessions",
        json={
            "session_key": SESSION_KEY,
            "user_id": USER_ID,
            "provider": PROVIDER,
            "external_user_id": EXTERNAL_USER_ID,
            "goal": GOAL,
        },
    )
    assert session_response.status_code == 200
    assert session_response.json()["created"] is True

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?",
            "resource_id": "persisted-query-doc",
            "session_summary": GOAL,
            "memory_items": [],
            "session_key": SESSION_KEY,
            "user_id": USER_ID,
        },
    )
    assert query_response.status_code == 200
    query_payload = query_response.json()

    commit_response = client.post(
        f"/internal/sessions/{SESSION_KEY}/commit",
        json={
            "user_id": USER_ID,
            "goal": GOAL,
            "user_message": "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?",
            "assistant_answer": query_payload["answer"],
            "trace_id": query_payload["traceId"],
        },
    )
    assert commit_response.status_code == 200
    commit_payload = commit_response.json()

    assert commit_payload["status"] == "ok"
    assert commit_payload["sessionId"] == SESSION_KEY
    assert commit_payload["committedMemoryCount"] >= 3
    assert "Zhiguang" in commit_payload["summary"]

    persisted_session_response = client.post(
        "/internal/sessions",
        json={
            "session_key": SESSION_KEY,
            "user_id": USER_ID,
            "provider": PROVIDER,
            "external_user_id": EXTERNAL_USER_ID,
            "goal": GOAL,
        },
    )
    assert persisted_session_response.status_code == 200
    persisted_session_payload = persisted_session_response.json()

    assert persisted_session_payload["created"] is False
    assert persisted_session_payload["turnCount"] == 1
    assert persisted_session_payload["summary"] == commit_payload["summary"]

    trace_response = client.get(f"/internal/traces/{query_payload['traceId']}")
    assert trace_response.status_code == 200
    trace_payload = trace_response.json()

    assert trace_payload["traceId"] == query_payload["traceId"]
    assert trace_payload["nodeSnapshots"][0]["nodeId"] == "persisted-query-doc:l2:s000:000"
    assert "DB authoritative" in trace_payload["nodeSnapshots"][0]["snapshotContent"]

    trace_node_response = client.get(
        f"/internal/traces/{query_payload['traceId']}/nodes/persisted-query-doc:l2:s000:000"
    )
    assert trace_node_response.status_code == 200
    assert trace_node_response.json()["nodePath"] == "resource://persisted-query-doc/l2/s000/000"

    memories_response = client.get(f"/internal/users/{USER_ID}/memories")
    assert memories_response.status_code == 200
    memories_payload = memories_response.json()

    assert any(
        memory["channel"] == "user"
        and memory["type"] == "explanation_preference"
        and "concise" in memory["content"].lower()
        for memory in memories_payload["memories"]
    )
    assert any(
        memory["channel"] == "task_experience"
        and memory["content"] == "Helpful resource: resource://persisted-query-doc/l2/s000/000"
        for memory in memories_payload["memories"]
    )
