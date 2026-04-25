from fastapi.testclient import TestClient

from app.main import app
from app.services.query import build_trace_node_snapshot
from app.services.resource_nodes import build_resource_nodes


def test_build_trace_node_snapshot_returns_requeryable_fields() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-trace-doc",
        markdown="# Redis Cache\n## Cache Aside\nRedis cache-aside keeps DB authoritative.",
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    snapshot = build_trace_node_snapshot(node=l2_node)

    assert snapshot.node_id == "zhiguang-trace-doc:l2:s000:000"
    assert snapshot.node_path == l2_node.node_path
    assert snapshot.level == "l2"
    assert snapshot.ancestry[-1]["node_path"] == "resource://zhiguang-trace-doc/l1/s000"
    assert snapshot.snapshot_content == "Redis cache-aside keeps DB authoritative."


def test_trace_routes_return_tree_current_node_and_historical_snapshot() -> None:
    client = TestClient(app)

    index_response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-trace-route-doc",
            "markdown": "# Redis Cache\n## Cache Aside\nRedis cache-aside keeps DB authoritative.",
        },
    )
    assert index_response.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "How should I reply on Zhiguang about Redis cache-aside?",
            "resource_id": "zhiguang-trace-route-doc",
            "session_summary": "Draft a concise Java reply to Zhiguang.",
            "memory_items": ["User prefers concise Java explanations."],
        },
    )
    assert query_response.status_code == 200
    query_payload = query_response.json()
    trace_id = query_payload["traceId"]
    node_id = query_payload["usedContexts"]["resources"][0]["nodeId"]

    tree_response = client.get("/internal/resources/zhiguang-trace-route-doc/tree")
    current_node_response = client.get(f"/internal/resources/nodes/{node_id}")
    trace_response = client.get(f"/internal/traces/{trace_id}")
    trace_node_response = client.get(f"/internal/traces/{trace_id}/nodes/{node_id}")

    assert tree_response.status_code == 200
    assert current_node_response.status_code == 200
    assert trace_response.status_code == 200
    assert trace_node_response.status_code == 200

    assert any(node["nodePath"] == "resource://zhiguang-trace-route-doc/l2/s000/000" for node in tree_response.json()["nodes"])
    assert current_node_response.json()["nodeId"] == node_id
    assert current_node_response.json()["snapshotContent"] == "Redis cache-aside keeps DB authoritative."
    assert trace_response.json()["traceId"] == trace_id
    assert trace_response.json()["usedContexts"]["sessionSummary"] == "Draft a concise Java reply to Zhiguang."
    assert trace_response.json()["usedContexts"]["memories"][0]["channel"] == "user"
    assert trace_response.json()["usedContexts"]["resources"][0]["traceNodeId"].startswith(trace_id)
    assert trace_response.json()["compressionSummary"]["beforeContextChars"] > trace_response.json()["compressionSummary"]["afterContextChars"]
    assert trace_node_response.json()["nodeId"] == node_id
    assert trace_node_response.json()["snapshotContent"] == "Redis cache-aside keeps DB authoritative."


def test_reindex_keeps_current_node_identity_while_trace_snapshot_stays_historical() -> None:
    client = TestClient(app)

    first_index = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "trace-history-doc",
            "markdown": "# Doc\n## Redis\nOld snapshot content.",
        },
    )
    assert first_index.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "How should I reply on Zhiguang about Redis cache-aside?",
            "resource_id": "trace-history-doc",
            "session_summary": "Draft a concise Java reply to Zhiguang.",
            "memory_items": ["User prefers concise Java explanations."],
        },
    )
    assert query_response.status_code == 200
    query_payload = query_response.json()
    trace_id = query_payload["traceId"]
    node_id = query_payload["usedContexts"]["resources"][0]["nodeId"]

    second_index = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "trace-history-doc",
            "markdown": "# Doc\n## Redis\nNew current content after reindex.",
        },
    )
    assert second_index.status_code == 200

    historical_trace_node = client.get(f"/internal/traces/{trace_id}/nodes/{node_id}")
    current_resource_node = client.get(f"/internal/resources/nodes/{node_id}")

    assert historical_trace_node.status_code == 200
    assert current_resource_node.status_code == 200
    assert historical_trace_node.json()["snapshotContent"] == "Old snapshot content."
    assert current_resource_node.json()["nodeId"] == node_id
    assert current_resource_node.json()["snapshotContent"] == "New current content after reindex."
