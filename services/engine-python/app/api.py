from __future__ import annotations

from uuid import uuid4
from re import findall

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.models import MemoryChannel, MemoryType
from app.services.memory import extract_memory_candidates, summarize_session
from app.services.query import build_node_id, build_query_result, build_trace_node_snapshot
from app.services.resource_nodes import ResourceNode, build_resource_nodes
from app.settings import settings

router = APIRouter()
_resource_index_store: dict[str, list[ResourceNode]] = {}
_trace_store: dict[str, dict[str, object]] = {}


class ResourceIndexRequest(BaseModel):
    resource_slug: str
    markdown: str
    previous_path_map: dict[str, str] = Field(default_factory=dict)


class ResourceIndexResponse(BaseModel):
    resource_slug: str
    imported_count: int
    nodes: list["ResourceNodeResponse"]


class ResourceNodeResponse(BaseModel):
    resource_slug: str
    level: str
    stable_key: str
    node_path: str
    parent_stable_key: str | None
    parent_node_path: str | None
    title: str
    content: str
    ordinal: int
    section_slug: str
    ancestry: list[dict[str, str]]


class SessionTurnPayload(BaseModel):
    role: str
    content: str


class MemoryExtractRequest(BaseModel):
    session_goal: str
    turns: list[SessionTurnPayload]
    selected_resource_paths: list[str] = Field(default_factory=list)


class MemoryCandidateResponse(BaseModel):
    channel: MemoryChannel
    memory_type: MemoryType
    salience: int
    content: str


class MemoryExtractResponse(BaseModel):
    candidate_count: int
    candidates: list[MemoryCandidateResponse]


class SessionSummaryRequest(BaseModel):
    session_goal: str
    turns: list[SessionTurnPayload]


class SessionSummaryResponse(BaseModel):
    summary: str


class ContextQueryRequest(BaseModel):
    question: str
    resource_id: str
    session_summary: str
    memory_items: list[str] = Field(default_factory=list)


class QueryResourceUsageResponse(BaseModel):
    nodeId: str
    traceNodeId: str
    nodePath: str
    drilldownTrail: list[str]


class QueryMemoryUsageResponse(BaseModel):
    channel: str
    type: str
    content: str


class UsedContextsResponse(BaseModel):
    sessionSummary: str
    memories: list[QueryMemoryUsageResponse]
    resources: list[QueryResourceUsageResponse]


class CompressionSummaryResponse(BaseModel):
    beforeContextChars: int
    afterContextChars: int


class ContextQueryResponse(BaseModel):
    traceId: str
    answer: str
    usedContexts: UsedContextsResponse
    compressionSummary: CompressionSummaryResponse


class ResourceTreeNodeResponse(BaseModel):
    nodeId: str
    nodePath: str
    level: str
    title: str
    parentNodeId: str | None


class ResourceTreeResponse(BaseModel):
    resourceId: str
    nodes: list[ResourceTreeNodeResponse]


class TraceNodeSnapshotResponse(BaseModel):
    nodeId: str
    nodePath: str
    level: str
    ancestry: list[dict[str, str]]
    snapshotContent: str


class TraceResponse(BaseModel):
    traceId: str
    question: str
    answer: str
    usedContexts: UsedContextsResponse
    compressionSummary: CompressionSummaryResponse
    nodeSnapshots: list[TraceNodeSnapshotResponse]


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "mode": settings.app_mode,
    }


@router.post("/internal/resources/index", response_model=ResourceIndexResponse)
def index_resource(payload: ResourceIndexRequest) -> ResourceIndexResponse:
    previous_nodes = _resource_index_store.get(payload.resource_slug, [])
    nodes = build_resource_nodes(
        resource_slug=payload.resource_slug,
        markdown=payload.markdown,
        previous_path_map=payload.previous_path_map,
        previous_nodes=previous_nodes,
    )
    _resource_index_store[payload.resource_slug] = nodes
    return ResourceIndexResponse(
        resource_slug=payload.resource_slug,
        imported_count=len(nodes),
        nodes=[ResourceNodeResponse.model_validate(node.to_dict()) for node in nodes],
    )


@router.post("/internal/memory/extract", response_model=MemoryExtractResponse)
def extract_memory(payload: MemoryExtractRequest) -> MemoryExtractResponse:
    candidates = extract_memory_candidates(
        session_goal=payload.session_goal,
        turns=[turn.model_dump() for turn in payload.turns],
        selected_resource_paths=payload.selected_resource_paths,
    )
    return MemoryExtractResponse(
        candidate_count=len(candidates),
        candidates=[
            MemoryCandidateResponse(
                channel=candidate.channel,
                memory_type=candidate.memory_type,
                salience=candidate.salience,
                content=candidate.content,
            )
            for candidate in candidates
        ],
    )


@router.post("/internal/session/summarize", response_model=SessionSummaryResponse)
def summarize_session_route(payload: SessionSummaryRequest) -> SessionSummaryResponse:
    summary = summarize_session(
        session_goal=payload.session_goal,
        turns=[turn.model_dump() for turn in payload.turns],
    )
    return SessionSummaryResponse(summary=summary)


def _find_current_resource_node(node_id: str) -> ResourceNode | None:
    for nodes in _resource_index_store.values():
        for node in nodes:
            if build_node_id(resource_slug=node.resource_slug, stable_key=node.stable_key) == node_id:
                return node
    return None


def _pick_query_nodes(nodes: list[ResourceNode]) -> list[ResourceNode]:
    l2_nodes = [node for node in nodes if node.level == "l2"]
    l1_nodes = [node for node in nodes if node.level == "l1"]
    return l2_nodes or l1_nodes[:1]


def _build_query_terms(*values: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    for value in values:
        lowered = value.lower()
        for latin_term in findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", lowered):
            if len(latin_term) <= 1 or latin_term in {"about", "reply", "write", "zhiguang"}:
                continue
            if latin_term not in seen:
                seen.add(latin_term)
                terms.append(latin_term)

        for cjk_sequence in findall(r"[\u4e00-\u9fff]{2,}", value):
            if len(cjk_sequence) <= 4:
                if cjk_sequence not in seen:
                    seen.add(cjk_sequence)
                    terms.append(cjk_sequence)
                continue

            for size in range(4, 1, -1):
                for index in range(len(cjk_sequence) - size + 1):
                    term = cjk_sequence[index : index + size]
                    if term not in seen:
                        seen.add(term)
                        terms.append(term)

    return terms


def _build_excluded_query_terms(value: str) -> list[str]:
    excluded_segments = findall(r"(?:不展开|不讲|不讨论|不解释)([^。；;!?！？]+)", value)
    if not excluded_segments:
        return []
    return _build_query_terms(*excluded_segments)


def _extract_summary_focus(session_summary: str) -> str:
    if "Key context:" not in session_summary:
        return session_summary
    return session_summary.split("Key context:", maxsplit=1)[1].strip()


def _score_terms_against_node(
    *,
    title_haystack: str,
    content_haystack: str,
    query_terms: list[str],
    title_weight: int,
    content_weight: int,
) -> int:
    score = 0
    for term in query_terms:
        normalized_term = term.lower()
        if normalized_term in title_haystack:
            score += title_weight + min(len(term), 10)
        elif normalized_term in content_haystack:
            score += content_weight + min(len(term), 10)
    return score


def _score_query_node(
    node: ResourceNode,
    *,
    question_terms: list[str],
    summary_terms: list[str],
    excluded_terms: list[str],
) -> int:
    title_haystack = node.title.lower()
    content_haystack = f"{node.content}\n{node.node_path}".lower()

    score = _score_terms_against_node(
        title_haystack=title_haystack,
        content_haystack=content_haystack,
        query_terms=question_terms,
        title_weight=9,
        content_weight=6,
    )
    score += _score_terms_against_node(
        title_haystack=title_haystack,
        content_haystack=content_haystack,
        query_terms=summary_terms,
        title_weight=4,
        content_weight=2,
    )
    score -= _score_terms_against_node(
        title_haystack=title_haystack,
        content_haystack=content_haystack,
        query_terms=excluded_terms,
        title_weight=11,
        content_weight=7,
    )
    return score


def _pick_query_nodes_for_prompt(
    nodes: list[ResourceNode],
    *,
    question: str,
    session_summary: str,
) -> list[ResourceNode]:
    candidate_nodes = _pick_query_nodes(nodes)
    if not candidate_nodes:
        return []

    question_terms = _build_query_terms(question)
    summary_terms = _build_query_terms(_extract_summary_focus(session_summary))
    excluded_terms = _build_excluded_query_terms(question)
    if not question_terms and not summary_terms:
        return [candidate_nodes[0]]

    best_node = max(
        candidate_nodes,
        key=lambda node: (
            _score_query_node(
                node,
                question_terms=question_terms,
                summary_terms=summary_terms,
                excluded_terms=excluded_terms,
            ),
            -node.ordinal,
        ),
    )
    return [best_node]


@router.post("/internal/context/query", response_model=ContextQueryResponse)
def context_query(payload: ContextQueryRequest) -> ContextQueryResponse:
    resource_nodes = _resource_index_store.get(payload.resource_id)
    if not resource_nodes:
        raise HTTPException(status_code=404, detail="resource not indexed")

    trace_id = str(uuid4())
    selected_nodes = _pick_query_nodes_for_prompt(
        resource_nodes,
        question=payload.question,
        session_summary=payload.session_summary,
    )
    query_result = build_query_result(
        question=payload.question,
        session_summary=payload.session_summary,
        memory_items=payload.memory_items,
        selected_nodes=selected_nodes,
        trace_id=trace_id,
    )
    snapshots = [build_trace_node_snapshot(node=node) for node in selected_nodes]
    used_contexts = UsedContextsResponse(
        sessionSummary=query_result.used_contexts["sessionSummary"],
        memories=[
            QueryMemoryUsageResponse.model_validate(memory_item)
            for memory_item in query_result.used_contexts["memories"]
        ],
        resources=[
            QueryResourceUsageResponse.model_validate(resource)
            for resource in query_result.used_contexts["resources"]
        ],
    )
    compression_summary = CompressionSummaryResponse.model_validate(query_result.compression_summary)
    trace_payload = TraceResponse(
        traceId=trace_id,
        question=payload.question,
        answer=query_result.answer,
        usedContexts=used_contexts,
        compressionSummary=compression_summary,
        nodeSnapshots=[
            TraceNodeSnapshotResponse(
                nodeId=snapshot.node_id,
                nodePath=snapshot.node_path,
                level=snapshot.level,
                ancestry=snapshot.ancestry,
                snapshotContent=snapshot.snapshot_content,
            )
            for snapshot in snapshots
        ],
    )
    _trace_store[trace_id] = trace_payload.model_dump()
    return ContextQueryResponse(
        traceId=trace_id,
        answer=query_result.answer,
        usedContexts=used_contexts,
        compressionSummary=compression_summary,
    )


@router.get("/internal/resources/{resourceId}/tree", response_model=ResourceTreeResponse)
def get_resource_tree(resourceId: str) -> ResourceTreeResponse:
    resource_nodes = _resource_index_store.get(resourceId)
    if not resource_nodes:
        raise HTTPException(status_code=404, detail="resource not indexed")

    return ResourceTreeResponse(
        resourceId=resourceId,
        nodes=[
            ResourceTreeNodeResponse(
                nodeId=build_node_id(resource_slug=node.resource_slug, stable_key=node.stable_key),
                nodePath=node.node_path,
                level=node.level,
                title=node.title,
                parentNodeId=(
                    build_node_id(resource_slug=node.resource_slug, stable_key=node.parent_stable_key)
                    if node.parent_stable_key is not None
                    else None
                ),
            )
            for node in resource_nodes
        ],
    )


@router.get("/internal/resources/nodes/{nodeId}", response_model=TraceNodeSnapshotResponse)
def get_resource_node(nodeId: str) -> TraceNodeSnapshotResponse:
    node = _find_current_resource_node(nodeId)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")

    snapshot = build_trace_node_snapshot(node=node)
    return TraceNodeSnapshotResponse(
        nodeId=snapshot.node_id,
        nodePath=snapshot.node_path,
        level=snapshot.level,
        ancestry=snapshot.ancestry,
        snapshotContent=snapshot.snapshot_content,
    )


@router.get("/internal/traces/{traceId}", response_model=TraceResponse)
def get_trace(traceId: str) -> TraceResponse:
    trace_payload = _trace_store.get(traceId)
    if trace_payload is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return TraceResponse.model_validate(trace_payload)


@router.get("/internal/traces/{traceId}/nodes/{nodeId}", response_model=TraceNodeSnapshotResponse)
def get_trace_node_snapshot(traceId: str, nodeId: str) -> TraceNodeSnapshotResponse:
    trace_payload = _trace_store.get(traceId)
    if trace_payload is None:
        raise HTTPException(status_code=404, detail="trace not found")

    for snapshot in trace_payload["nodeSnapshots"]:
        if snapshot["nodeId"] == nodeId:
            return TraceNodeSnapshotResponse.model_validate(snapshot)
    raise HTTPException(status_code=404, detail="trace node not found")
