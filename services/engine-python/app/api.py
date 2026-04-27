from __future__ import annotations

from uuid import uuid4
from re import findall

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models import MemoryChannel, MemoryType
from app.models import Session as SessionModel
from app.models import SessionTurn as SessionTurnModel
from app.db import get_db_session
from app.services.memory import extract_memory_candidates, summarize_session
from app.services.persistence import commit_session_turn
from app.services.persistence import ensure_session
from app.services.persistence import get_current_resource_node_payload
from app.services.persistence import get_resource_tree_payload
from app.services.persistence import get_trace_node_snapshot_payload
from app.services.persistence import get_trace_payload
from app.services.persistence import list_current_resource_nodes
from app.services.persistence import list_provider_resource_trees_payload
from app.services.persistence import list_user_memory_payload
from app.services.persistence import persist_trace_payload
from app.services.persistence import upsert_resource_from_markdown
from app.services.query import build_node_id, build_query_result, build_trace_node_snapshot
from app.services.resource_nodes import ResourceNode
from app.settings import settings

router = APIRouter()
_trace_store: dict[str, dict[str, object]] = {}
_QUERY_TERM_ALIASES: dict[str, list[str]] = {
    "采样": ["sampling"],
    "日志关联": ["log correlation"],
    "调用链": ["call chain"],
    "幂等": ["idempotent", "idempotency"],
    "死信队列": ["dead-letter", "dead-letter queues"],
    "重复消费": ["duplicate", "duplicate messages"],
    "增量刷新": ["incremental refresh"],
    "排序信号": ["ranking"],
    "倒排索引": ["inverted index"],
}


class ResourceIndexRequest(BaseModel):
    provider: str = "demo_local"
    resource_slug: str
    markdown: str
    source_uri: str = ""
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
    session_key: str | None = None
    user_id: str | None = None


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


class ResourceTreeWithContentNodeResponse(ResourceTreeNodeResponse):
    content: str


class ResourceTreeResponse(BaseModel):
    resourceId: str
    nodes: list[ResourceTreeNodeResponse]


class ProviderResourceTreeResponse(BaseModel):
    resourceId: str
    title: str
    nodes: list[ResourceTreeWithContentNodeResponse]


class ProviderResourceTreesResponse(BaseModel):
    provider: str
    resources: list[ProviderResourceTreeResponse]


class TraceNodeSnapshotResponse(BaseModel):
    nodeId: str
    nodePath: str
    level: str
    ancestry: list[dict[str, str]]
    snapshotContent: str


class SessionEnsureRequest(BaseModel):
    session_key: str
    user_id: str
    provider: str
    external_user_id: str
    goal: str = ""


class SessionStateResponse(BaseModel):
    sessionId: str
    goal: str
    summary: str
    created: bool
    turnCount: int


class SessionCommitRequest(BaseModel):
    user_id: str
    goal: str = ""
    user_message: str
    assistant_answer: str
    trace_id: str


class SessionCommitResponse(BaseModel):
    status: str
    sessionId: str
    summary: str
    committedMemoryCount: int


class RecalledMemoryResponse(QueryMemoryUsageResponse):
    salience: int


class UserMemoryResponse(BaseModel):
    userId: str
    memories: list[RecalledMemoryResponse]


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
def index_resource(
    payload: ResourceIndexRequest,
    db_session: DbSession = Depends(get_db_session),
) -> ResourceIndexResponse:
    nodes = upsert_resource_from_markdown(
        db_session,
        provider=payload.provider,
        resource_slug=payload.resource_slug,
        markdown=payload.markdown,
        source_uri=payload.source_uri or f"resource://{payload.provider}/{payload.resource_slug}",
        previous_path_map=payload.previous_path_map,
    )
    db_session.commit()
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


def _expand_query_terms(query_terms: list[str]) -> list[str]:
    expanded_terms = list(query_terms)
    seen = set(query_terms)

    for term in query_terms:
        for alias in _QUERY_TERM_ALIASES.get(term, []):
            if alias not in seen:
                seen.add(alias)
                expanded_terms.append(alias)

    return expanded_terms


def _build_excluded_query_terms(value: str) -> list[str]:
    excluded_segments = findall(r"(?:不展开|不讲|不讨论|不解释)([^。；;!?！？]+)", value)
    if not excluded_segments:
        return []
    return _build_query_terms(*excluded_segments)


def _remove_excluded_query_segments(value: str) -> str:
    return value.replace("不展开", "\n").replace("不讲", "\n").replace("不讨论", "\n").replace("不解释", "\n")


def _extract_focus_query_terms(value: str) -> list[str]:
    focus_segments = findall(
        r"(?:只想|想要|想)(?:解释|讲|聊|覆盖)([^。；;!?！？]+?)(?:，|,|不展开|不讲|不讨论|不解释|$)",
        value,
    )
    if not focus_segments:
        return []
    return _build_query_terms(*focus_segments)


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
    focus_terms: list[str],
    question_terms: list[str],
    summary_terms: list[str],
    excluded_terms: list[str],
) -> int:
    title_haystack = node.title.lower()
    content_haystack = f"{node.content}\n{node.node_path}".lower()

    score = _score_terms_against_node(
        title_haystack=title_haystack,
        content_haystack=content_haystack,
        query_terms=focus_terms,
        title_weight=13,
        content_weight=9,
    )
    score += _score_terms_against_node(
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

    focus_terms = _expand_query_terms(_extract_focus_query_terms(question))
    question_terms = _expand_query_terms(_build_query_terms(_remove_excluded_query_segments(question)))
    summary_terms = _expand_query_terms(_build_query_terms(_extract_summary_focus(session_summary)))
    excluded_terms = _expand_query_terms(_build_excluded_query_terms(question))
    if not focus_terms and not question_terms and not summary_terms:
        return [candidate_nodes[0]]

    best_node = max(
        candidate_nodes,
        key=lambda node: (
            _score_query_node(
                node,
                focus_terms=focus_terms,
                question_terms=question_terms,
                summary_terms=summary_terms,
                excluded_terms=excluded_terms,
            ),
            -node.ordinal,
        ),
    )
    return [best_node]


def _build_session_state_response(
    db_session: DbSession,
    *,
    session: SessionModel,
    created: bool,
) -> SessionStateResponse:
    turn_count = db_session.query(SessionTurnModel).filter(SessionTurnModel.session_id == session.id).count()
    return SessionStateResponse(
        sessionId=session.session_key,
        goal=session.goal or "",
        summary=session.summary or "",
        created=created,
        turnCount=turn_count,
    )


@router.post("/internal/sessions", response_model=SessionStateResponse)
def ensure_session_route(
    payload: SessionEnsureRequest,
    db_session: DbSession = Depends(get_db_session),
) -> SessionStateResponse:
    try:
        session, created = ensure_session(
            db_session,
            session_key=payload.session_key,
            user_id=payload.user_id,
            provider=payload.provider,
            external_user_id=payload.external_user_id,
            goal=payload.goal,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    db_session.commit()
    return _build_session_state_response(db_session, session=session, created=created)


@router.post("/internal/sessions/{sessionKey}/commit", response_model=SessionCommitResponse)
def commit_session_route(
    sessionKey: str,
    payload: SessionCommitRequest,
    db_session: DbSession = Depends(get_db_session),
) -> SessionCommitResponse:
    try:
        commit_payload = commit_session_turn(
            db_session,
            session_key=sessionKey,
            user_id=payload.user_id,
            goal=payload.goal,
            user_message=payload.user_message,
            assistant_answer=payload.assistant_answer,
            trace_id=payload.trace_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    db_session.commit()
    return SessionCommitResponse.model_validate(commit_payload)


@router.get("/internal/users/{userId}/memories", response_model=UserMemoryResponse)
def get_user_memories(
    userId: str,
    limit: int = 10,
    db_session: DbSession = Depends(get_db_session),
) -> UserMemoryResponse:
    return UserMemoryResponse.model_validate(
        list_user_memory_payload(db_session, user_id=userId, limit=limit)
    )


@router.post("/internal/context/query", response_model=ContextQueryResponse)
def context_query(
    payload: ContextQueryRequest,
    db_session: DbSession = Depends(get_db_session),
) -> ContextQueryResponse:
    resource_nodes = list_current_resource_nodes(db_session, resource_slug=payload.resource_id)
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
    serialized_snapshots = [
        {
            "nodeId": snapshot.node_id,
            "nodePath": snapshot.node_path,
            "level": snapshot.level,
            "ancestry": snapshot.ancestry,
            "snapshotContent": snapshot.snapshot_content,
        }
        for snapshot in snapshots
    ]
    trace_payload = TraceResponse(
        traceId=trace_id,
        question=payload.question,
        answer=query_result.answer,
        usedContexts=used_contexts,
        compressionSummary=compression_summary,
        nodeSnapshots=[
            TraceNodeSnapshotResponse.model_validate(snapshot_payload)
            for snapshot_payload in serialized_snapshots
        ],
    )

    if payload.session_key and payload.user_id:
        try:
            persist_trace_payload(
                db_session,
                trace_id=trace_id,
                session_key=payload.session_key,
                user_id=payload.user_id,
                question=payload.question,
                answer=query_result.answer,
                used_contexts=used_contexts.model_dump(),
                compression_summary=compression_summary.model_dump(),
                snapshots=serialized_snapshots,
            )
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        db_session.commit()
    else:
        _trace_store[trace_id] = trace_payload.model_dump()

    return ContextQueryResponse(
        traceId=trace_id,
        answer=query_result.answer,
        usedContexts=used_contexts,
        compressionSummary=compression_summary,
    )


@router.get("/internal/resources/{resourceId}/tree", response_model=ResourceTreeResponse)
def get_resource_tree(
    resourceId: str,
    db_session: DbSession = Depends(get_db_session),
) -> ResourceTreeResponse:
    tree_payload = get_resource_tree_payload(db_session, resource_slug=resourceId, include_content=False)
    if tree_payload is None:
        raise HTTPException(status_code=404, detail="resource not indexed")
    return ResourceTreeResponse.model_validate(tree_payload)


@router.get("/internal/resources/providers/{provider}/trees", response_model=ProviderResourceTreesResponse)
def get_provider_resource_trees(
    provider: str,
    db_session: DbSession = Depends(get_db_session),
) -> ProviderResourceTreesResponse:
    return ProviderResourceTreesResponse.model_validate(
        list_provider_resource_trees_payload(db_session, provider=provider)
    )


@router.get("/internal/resources/nodes/{nodeId}", response_model=TraceNodeSnapshotResponse)
def get_resource_node(
    nodeId: str,
    db_session: DbSession = Depends(get_db_session),
) -> TraceNodeSnapshotResponse:
    snapshot_payload = get_current_resource_node_payload(db_session, node_id=nodeId)
    if snapshot_payload is None:
        raise HTTPException(status_code=404, detail="node not found")
    return TraceNodeSnapshotResponse.model_validate(snapshot_payload)


@router.get("/internal/traces/{traceId}", response_model=TraceResponse)
def get_trace(
    traceId: str,
    db_session: DbSession = Depends(get_db_session),
) -> TraceResponse:
    trace_payload = get_trace_payload(db_session, trace_id=traceId)
    if trace_payload is not None:
        return TraceResponse.model_validate(trace_payload)

    memory_trace_payload = _trace_store.get(traceId)
    if memory_trace_payload is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return TraceResponse.model_validate(memory_trace_payload)


@router.get("/internal/traces/{traceId}/nodes/{nodeId}", response_model=TraceNodeSnapshotResponse)
def get_trace_node_snapshot(
    traceId: str,
    nodeId: str,
    db_session: DbSession = Depends(get_db_session),
) -> TraceNodeSnapshotResponse:
    snapshot_payload = get_trace_node_snapshot_payload(
        db_session,
        trace_id=traceId,
        node_id=nodeId,
    )
    if snapshot_payload is not None:
        return TraceNodeSnapshotResponse.model_validate(snapshot_payload)

    memory_trace_payload = _trace_store.get(traceId)
    if memory_trace_payload is None:
        raise HTTPException(status_code=404, detail="trace node not found")
    for snapshot in memory_trace_payload["nodeSnapshots"]:
        if snapshot["nodeId"] == nodeId:
            return TraceNodeSnapshotResponse.model_validate(snapshot)
    raise HTTPException(status_code=404, detail="trace node not found")
