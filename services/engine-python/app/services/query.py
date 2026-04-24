from __future__ import annotations

from dataclasses import dataclass

from app.services.resource_nodes import ResourceNode


def build_node_id(*, resource_slug: str, stable_key: str) -> str:
    return f"{resource_slug}:{stable_key}"


def build_trace_node_id(*, trace_id: str, node_id: str) -> str:
    return f"{trace_id}:{node_id}"


def _build_drilldown_trail(node: ResourceNode) -> list[dict[str, str]]:
    return [ancestor["node_path"] for ancestor in node.ancestry] + [node.node_path]


@dataclass(frozen=True)
class QueryResult:
    answer: str
    used_contexts: dict[str, object]
    compression_summary: dict[str, int]


@dataclass(frozen=True)
class TraceNodeSnapshot:
    node_id: str
    node_path: str
    level: str
    ancestry: list[dict[str, str]]
    snapshot_content: str


def build_trace_node_snapshot(*, node: ResourceNode) -> TraceNodeSnapshot:
    return TraceNodeSnapshot(
        node_id=build_node_id(resource_slug=node.resource_slug, stable_key=node.stable_key),
        node_path=node.node_path,
        level=node.level,
        ancestry=[
            {
                "node_id": build_node_id(resource_slug=node.resource_slug, stable_key=ancestor["stable_key"]),
                "node_path": ancestor["node_path"],
                "level": ancestor["level"],
            }
            for ancestor in node.ancestry
        ],
        snapshot_content=node.content,
    )


def _infer_memory_context(memory_item: str) -> dict[str, str]:
    lowered = memory_item.lower()
    if lowered.startswith("user goal:"):
        return {"channel": "user", "type": "user_goal", "content": memory_item}
    if "prefers" in lowered or "concise" in lowered or "java" in lowered:
        return {"channel": "user", "type": "explanation_preference", "content": memory_item}
    if lowered.startswith("helpful resource:"):
        return {"channel": "task_experience", "type": "successful_resource", "content": memory_item}
    return {"channel": "user", "type": "topic_preference", "content": memory_item}


def build_query_result(
    *,
    question: str,
    session_summary: str,
    memory_items: list[str],
    selected_nodes: list[ResourceNode],
    trace_id: str,
) -> QueryResult:
    resource_contexts: list[dict[str, object]] = []
    resource_snippets: list[str] = []

    for node in selected_nodes:
        node_id = build_node_id(resource_slug=node.resource_slug, stable_key=node.stable_key)
        resource_contexts.append(
            {
                "nodeId": node_id,
                "traceNodeId": build_trace_node_id(trace_id=trace_id, node_id=node_id),
                "nodePath": node.node_path,
                "drilldownTrail": _build_drilldown_trail(node),
            }
        )
        resource_snippets.append(node.content)

    memory_summary = " ".join(memory_items).strip()
    resource_summary = " ".join(resource_snippets).strip()
    answer = (
        f"Question: {question} "
        f"Session summary: {session_summary} "
        f"Memories: {memory_summary} "
        f"Selected resource context: {resource_summary}"
    ).strip()

    before_context_chars = len(question) + len(session_summary) + sum(len(item) for item in memory_items) + sum(
        len(node.content) for node in selected_nodes
    )
    after_context_chars = len(session_summary) + len(resource_summary)

    return QueryResult(
        answer=answer,
        used_contexts={
            "sessionSummary": session_summary,
            "memories": [_infer_memory_context(memory_item) for memory_item in memory_items],
            "resources": resource_contexts,
        },
        compression_summary={
            "beforeContextChars": before_context_chars,
            "afterContextChars": after_context_chars,
        },
    )
