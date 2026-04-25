from fastapi.testclient import TestClient

from app.main import app
from app.services.query import build_query_result
from app.services.resource_nodes import build_resource_nodes


def test_build_query_result_returns_traceable_used_context_resources() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-cache-doc",
        markdown="# Redis Cache\n## Cache Aside\nRedis cache-aside keeps DB authoritative.",
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    result = build_query_result(
        question="How should I reply on Zhiguang about Redis cache-aside?",
        session_summary="Draft a concise Java reply to Zhiguang.",
        memory_items=[
            "User prefers concise Java explanations.",
            "Helpful resource: resource://zhiguang-cache-doc/l2/s000/000",
        ],
        selected_nodes=[l2_node],
        trace_id="trace-001",
    )

    assert result.answer.startswith("Zhiguang reply:")
    assert "Redis cache-aside" in result.answer
    assert "database" in result.answer.lower()
    assert result.used_contexts["sessionSummary"] == "Draft a concise Java reply to Zhiguang."
    assert result.used_contexts["memories"][0]["channel"] == "user"
    assert result.used_contexts["memories"][0]["type"] == "explanation_preference"
    assert result.used_contexts["resources"][0]["nodeId"] == "zhiguang-cache-doc:l2:s000:000"
    assert result.used_contexts["resources"][0]["traceNodeId"] == "trace-001:zhiguang-cache-doc:l2:s000:000"
    assert result.used_contexts["resources"][0]["nodePath"] == l2_node.node_path
    assert result.used_contexts["resources"][0]["drilldownTrail"] == [
        "resource://zhiguang-cache-doc/l0/root",
        "resource://zhiguang-cache-doc/l1/s000",
        "resource://zhiguang-cache-doc/l2/s000/000",
    ]
    assert result.compression_summary["beforeContextChars"] > result.compression_summary["afterContextChars"]


def test_build_query_result_returns_human_readable_answer() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-cache-doc",
        markdown="# Redis Cache\n## Cache Aside\nRedis cache-aside keeps DB authoritative.",
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    result = build_query_result(
        question="How should I reply on Zhiguang about Redis cache-aside?",
        session_summary="Draft a concise Java reply to Zhiguang.",
        memory_items=[
            "User prefers concise Java explanations.",
            "Helpful resource: resource://zhiguang-cache-doc/l2/s000/000",
        ],
        selected_nodes=[l2_node],
        trace_id="trace-002",
    )

    assert result.answer.startswith("Zhiguang reply:")
    assert "Question:" not in result.answer
    assert "Session summary:" not in result.answer
    assert "Memories:" not in result.answer
    assert "Redis cache-aside" in result.answer
    assert "database" in result.answer.lower()


def test_context_query_route_returns_traceable_resources() -> None:
    client = TestClient(app)
    index_response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-query-doc",
            "markdown": "# Redis Cache\n## Cache Aside\nRedis cache-aside keeps DB authoritative.",
        },
    )

    assert index_response.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "How should I reply on Zhiguang about Redis cache-aside?",
            "resource_id": "zhiguang-query-doc",
            "session_summary": "Draft a concise Java reply to Zhiguang.",
            "memory_items": [
                "User prefers concise Java explanations.",
                "Helpful resource: resource://zhiguang-query-doc/l2/s000/000",
            ],
        },
    )

    assert query_response.status_code == 200
    payload = query_response.json()

    assert payload["traceId"]
    assert "Zhiguang" in payload["answer"]
    assert payload["usedContexts"]["sessionSummary"] == "Draft a concise Java reply to Zhiguang."
    assert payload["usedContexts"]["memories"][0]["channel"] == "user"
    assert payload["usedContexts"]["memories"][0]["type"] == "explanation_preference"
    assert payload["usedContexts"]["resources"][0]["nodeId"] == "zhiguang-query-doc:l2:s000:000"
    assert payload["usedContexts"]["resources"][0]["traceNodeId"].startswith(payload["traceId"])
    assert payload["usedContexts"]["resources"][0]["nodePath"] == "resource://zhiguang-query-doc/l2/s000/000"
    assert payload["usedContexts"]["resources"][0]["drilldownTrail"] == [
        "resource://zhiguang-query-doc/l0/root",
        "resource://zhiguang-query-doc/l1/s000",
        "resource://zhiguang-query-doc/l2/s000/000",
    ]
    assert payload["compressionSummary"]["beforeContextChars"] > payload["compressionSummary"]["afterContextChars"]
