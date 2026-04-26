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
            "Helpful resource: resource://zhiguang-cache-doc/l2/other/999",
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
    assert result.used_contexts["memories"][1]["content"] == "Helpful resource: resource://zhiguang-cache-doc/l2/s000/000"
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


def test_build_query_result_preserves_existing_sentence_punctuation() -> None:
    nodes = build_resource_nodes(
        resource_slug="zhiguang-tracing-doc",
        markdown=(
            "# Zhiguang Tracing Guide\n"
            "## 分布式追踪 / Distributed Tracing\n"
            "Distributed tracing links trace and span IDs across services。"
        ),
    )
    l2_node = next(node for node in nodes if node.level == "l2")

    result = build_query_result(
        question="我想写一条关于分布式追踪的 Zhiguang 回复。",
        session_summary="写一条关于分布式追踪的 Zhiguang 回复",
        memory_items=[],
        selected_nodes=[l2_node],
        trace_id="trace-003",
    )

    assert "。." not in result.answer
    assert result.answer.endswith("services。")


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
    assert payload["usedContexts"]["memories"][1]["content"] == "Helpful resource: resource://zhiguang-query-doc/l2/s000/000"
    assert payload["usedContexts"]["resources"][0]["nodeId"] == "zhiguang-query-doc:l2:s000:000"
    assert payload["usedContexts"]["resources"][0]["traceNodeId"].startswith(payload["traceId"])
    assert payload["usedContexts"]["resources"][0]["nodePath"] == "resource://zhiguang-query-doc/l2/s000/000"
    assert payload["usedContexts"]["resources"][0]["drilldownTrail"] == [
        "resource://zhiguang-query-doc/l0/root",
        "resource://zhiguang-query-doc/l1/s000",
        "resource://zhiguang-query-doc/l2/s000/000",
    ]
    assert payload["compressionSummary"]["beforeContextChars"] > payload["compressionSummary"]["afterContextChars"]


def test_context_query_route_picks_the_most_relevant_resource_node() -> None:
    client = TestClient(app)
    index_response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-multi-topic-doc",
            "markdown": (
                "# Zhiguang Multi Topic Guide\n"
                "## Redis Cache Aside\n"
                "Redis cache-aside keeps the database authoritative.\n\n"
                "## 分布式追踪 / Distributed Tracing\n"
                "Distributed tracing links trace and span IDs across services so engineers can inspect the call chain."
            ),
        },
    )

    assert index_response.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "我想在 Zhiguang 上解释分布式追踪，顺便提到 trace、span 和调用链。",
            "resource_id": "zhiguang-multi-topic-doc",
            "session_summary": "写一条关于分布式追踪的 Zhiguang 回复",
            "memory_items": [],
        },
    )

    assert query_response.status_code == 200
    payload = query_response.json()

    assert "Distributed tracing" in payload["answer"]
    assert payload["usedContexts"]["resources"][0]["nodePath"] == (
        "resource://zhiguang-multi-topic-doc/l2/s001/000"
    )


def test_context_query_route_prefers_specific_subtopic_when_question_excludes_broader_section() -> None:
    client = TestClient(app)
    index_response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-search-doc",
            "markdown": (
                "# Zhiguang Search Guide\n"
                "## 搜索索引 / Search Indexing\n"
                "Search indexing usually starts from an inverted index so queries can map terms to matching documents quickly.\n\n"
                "## 排序与刷新 / Ranking and Refresh\n"
                "Ranking combines term matching, recency, and quality signals, while incremental refresh keeps new content searchable."
            ),
        },
    )

    assert index_response.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "我只想解释排序信号和增量刷新，不展开倒排索引。",
            "resource_id": "zhiguang-search-doc",
            "session_summary": "写一条关于搜索索引的 Zhiguang 回复 Key context: 我只想解释排序信号和增量刷新，不展开倒排索引。",
            "memory_items": [],
        },
    )

    assert query_response.status_code == 200
    payload = query_response.json()

    assert "Ranking combines term matching" in payload["answer"]
    assert payload["usedContexts"]["resources"][0]["nodePath"] == (
        "resource://zhiguang-search-doc/l2/s001/000"
    )
