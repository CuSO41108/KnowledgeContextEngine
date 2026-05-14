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


def test_context_query_route_generic_summary_skips_zhiguang_metadata_overview() -> None:
    client = TestClient(app)
    index_response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-summary-post",
            "markdown": (
                "# b站视频总结\n\n"
                "Provider: zhiguang\n"
                "Post ID: 312421331314544640\n"
                "Content URL: https://example.com/content.md\n"
                "Content SHA256: abc123\n\n"
                "## Summary\n\n"
                "揭秘穷人思维，打破局限，改变认知才能改变命运。\n\n"
                "## Content\n\n"
                "常见的穷人思维"
            ),
        },
    )

    assert index_response.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "这篇知文主要讲什么？",
            "resource_id": "zhiguang-summary-post",
            "session_summary": "围绕当前知光知文生成回答",
            "memory_items": [],
        },
    )

    assert query_response.status_code == 200
    payload = query_response.json()
    resource_paths = [
        resource["nodePath"]
        for resource in payload["usedContexts"]["resources"]
    ]

    assert "揭秘穷人思维" in payload["answer"]
    assert "常见的穷人思维" in payload["answer"]
    assert "Content URL" not in payload["answer"]
    assert resource_paths == [
        "resource://zhiguang-summary-post/l2/s001/000",
        "resource://zhiguang-summary-post/l2/s002/000",
    ]


def test_context_query_route_generic_summary_covers_later_long_article_sections() -> None:
    client = TestClient(app)
    index_response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-long-rag-post",
            "markdown": (
                "# RAG 工程化笔记\n\n"
                "这篇文章讨论从能通到好用的知识问答系统。\n\n"
                "## 工程分层\n\n"
                "系统分为内容存储层、按需同步层、节点构建层、查询生成层和观测层。\n\n"
                "## 排障方法\n\n"
                "如果答案很短但带引用，先检查原文是否太薄；如果答案像模板，检查 engine-python 的 LLM 环境变量。\n\n"
                "## 检索优化方向\n\n"
                "下一步应加入 resource scope、hybrid retrieval 和 evidence trace，让回答能覆盖多个相关章节。"
            ),
        },
    )

    assert index_response.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "这篇技术博客主要讲了什么？请总结工程分层、排障方法和检索优化方向。",
            "resource_id": "zhiguang-long-rag-post",
            "session_summary": "围绕当前知光知文生成回答",
            "memory_items": [],
        },
    )

    assert query_response.status_code == 200
    payload = query_response.json()
    resource_paths = [
        resource["nodePath"]
        for resource in payload["usedContexts"]["resources"]
    ]

    assert any("/l1/s001" in path for path in resource_paths)
    assert any("/l1/s002" in path for path in resource_paths)
    assert any("/l1/s003" in path for path in resource_paths)
    assert "内容存储层" in payload["answer"]
    assert "LLM 环境变量" in payload["answer"]
    assert "resource scope" in payload["answer"]


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


def test_context_query_route_prefers_queue_delivery_subtopic_when_question_excludes_overview() -> None:
    client = TestClient(app)
    index_response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-queue-doc",
            "markdown": (
                "# Zhiguang Queue Guide\n"
                "## 消息队列 / Message Queue\n"
                "A message queue decouples producers and consumers so burst traffic can be buffered instead of failing synchronous calls. 在中文语境里，消息队列常用来削峰填谷、异步化和解耦。\n\n"
                "## 至少一次投递与幂等 / At-least-once Delivery and Idempotency\n"
                "At-least-once delivery means consumers may receive duplicate messages, so handlers should be idempotent and retry-safe. Dead-letter queues help isolate poison messages instead of blocking the whole pipeline."
            ),
        },
    )

    assert index_response.status_code == 200

    query_response = client.post(
        "/internal/context/query",
        json={
            "question": "我只想解释重复消费、幂等和死信队列，不展开削峰填谷。",
            "resource_id": "zhiguang-queue-doc",
            "session_summary": "写一条关于消息队列的 Zhiguang 回复 Key context: 我只想解释重复消费、幂等和死信队列，不展开削峰填谷。",
            "memory_items": [],
        },
    )

    assert query_response.status_code == 200
    payload = query_response.json()

    assert "At-least-once delivery" in payload["answer"]
    assert payload["usedContexts"]["resources"][0]["nodePath"] == (
        "resource://zhiguang-queue-doc/l2/s001/000"
    )
