from __future__ import annotations

from dataclasses import dataclass
from math import log
from uuid import uuid4
from re import findall, sub

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
_GENERIC_SUMMARY_TERMS = (
    "主要讲什么",
    "讲什么",
    "主要内容",
    "总结",
    "概括",
    "大意",
    "main idea",
    "summarize",
    "summary",
    "what is this",
    "what is it about",
)
_SUBSTANTIVE_SECTION_SLUGS = {"summary", "content"}
_METADATA_SECTION_SLUGS = {"overview", "metadata"}
_MAX_SELECTED_QUERY_NODES = 10
_MAX_SELECTED_QUERY_CONTENT_CHARS = 4200
_MAX_SELECTED_NODES_PER_SECTION_FIRST_PASS = 2
_MIN_SELECTED_QUERY_SCORE_WITH_EXCLUSIONS = 5.0
_NODE_LEVEL_WEIGHTS = {
    "l0": 0.35,
    "l1": 0.9,
    "l2": 1.25,
}
_EXCLUSION_PREFIX_PATTERN = r"(?:不展开|不讲|不讨论|不解释|不要展开|不要讲|不要讨论|不要解释)"
_CLAUSE_BOUNDARY_CHARS = r"。；;!?！？，,"


@dataclass(frozen=True)
class ScoredQueryNode:
    score: float
    ordinal_sort: int
    node: ResourceNode
    matched_terms: tuple[str, ...]
    score_breakdown: dict[str, float]
    selection_reason: str


@dataclass(frozen=True)
class QueryNodeSelection:
    selected_nodes: list[ResourceNode]
    retrieval_evidence_by_path: dict[str, dict[str, object]]


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
    retrievalScore: float = 0.0
    matchedTerms: list[str] = Field(default_factory=list)
    selectionReason: str = ""
    resourceScope: str = ""
    scoreBreakdown: dict[str, float] = Field(default_factory=dict)


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


def _pick_generic_summary_candidate_nodes(nodes: list[ResourceNode]) -> list[ResourceNode]:
    l1_substantive_nodes = [
        node
        for node in nodes
        if node.level == "l1" and _is_substantive_query_node(node)
    ]
    if len(l1_substantive_nodes) > 2:
        return l1_substantive_nodes
    return _pick_query_nodes(nodes)


def _is_generic_summary_question(value: str) -> bool:
    normalized = value.strip().lower()
    return any(term in normalized for term in _GENERIC_SUMMARY_TERMS)


def _is_metadata_overview_node(node: ResourceNode) -> bool:
    content = node.content.lower()
    return node.section_slug in _METADATA_SECTION_SLUGS and (
        "provider:" in content
        or "post id:" in content
        or "content url:" in content
        or "content sha256:" in content
    )


def _pick_substantive_default_nodes(candidate_nodes: list[ResourceNode]) -> list[ResourceNode]:
    substantive_nodes = [
        node
        for node in candidate_nodes
        if node.section_slug in _SUBSTANTIVE_SECTION_SLUGS and node.content.strip()
    ]
    if substantive_nodes:
        return substantive_nodes[:2]

    non_metadata_nodes = [
        node
        for node in candidate_nodes
        if not _is_metadata_overview_node(node) and node.content.strip()
    ]
    if non_metadata_nodes:
        return non_metadata_nodes[:1]

    return candidate_nodes[:1]


def _is_substantive_query_node(node: ResourceNode) -> bool:
    return bool(node.content.strip()) and not _is_metadata_overview_node(node)


def _section_stable_key(node: ResourceNode) -> str:
    for ancestor in reversed(node.ancestry):
        if ancestor.get("level") == "l1":
            return ancestor.get("stable_key", node.stable_key)
    return node.stable_key


def _add_selected_query_node(
    selected_nodes: list[ResourceNode],
    seen_paths: set[str],
    section_counts: dict[str, int],
    node: ResourceNode,
    *,
    content_chars: int,
    enforce_section_limit: bool = False,
) -> int:
    if node.node_path in seen_paths or not node.content.strip():
        return content_chars
    if len(selected_nodes) >= _MAX_SELECTED_QUERY_NODES:
        return content_chars

    section_key = _section_stable_key(node)
    if enforce_section_limit and section_counts.get(section_key, 0) >= _MAX_SELECTED_NODES_PER_SECTION_FIRST_PASS:
        return content_chars

    next_content_chars = content_chars + len(node.content)
    if selected_nodes and next_content_chars > _MAX_SELECTED_QUERY_CONTENT_CHARS:
        return content_chars

    selected_nodes.append(node)
    seen_paths.add(node.node_path)
    section_counts[section_key] = section_counts.get(section_key, 0) + 1
    return next_content_chars


def _select_ranked_query_nodes(
    ranked_nodes: list[ScoredQueryNode],
    *,
    seed_nodes: list[ResourceNode] | None = None,
    minimum_score: float = 0.0,
) -> list[ResourceNode]:
    selected_nodes: list[ResourceNode] = []
    seen_paths: set[str] = set()
    section_counts: dict[str, int] = {}
    content_chars = 0

    for node in seed_nodes or []:
        content_chars = _add_selected_query_node(
            selected_nodes,
            seen_paths,
            section_counts,
            node,
            content_chars=content_chars,
        )

    for ranked_node in ranked_nodes:
        if ranked_node.score <= 0 or ranked_node.score < minimum_score:
            continue
        content_chars = _add_selected_query_node(
            selected_nodes,
            seen_paths,
            section_counts,
            ranked_node.node,
            content_chars=content_chars,
            enforce_section_limit=True,
        )

    for ranked_node in ranked_nodes:
        if ranked_node.score <= 0 or ranked_node.score < minimum_score:
            continue
        content_chars = _add_selected_query_node(
            selected_nodes,
            seen_paths,
            section_counts,
            ranked_node.node,
            content_chars=content_chars,
        )

    return selected_nodes


def _build_retrieval_evidence_by_path(
    *,
    selected_nodes: list[ResourceNode],
    ranked_nodes: list[ScoredQueryNode],
    resource_scope: str,
    default_reason: str,
) -> dict[str, dict[str, object]]:
    ranked_by_path = {ranked_node.node.node_path: ranked_node for ranked_node in ranked_nodes}
    evidence_by_path: dict[str, dict[str, object]] = {}

    for node in selected_nodes:
        ranked_node = ranked_by_path.get(node.node_path)
        if ranked_node is None:
            evidence_by_path[node.node_path] = {
                "retrievalScore": 0.0,
                "matchedTerms": [],
                "selectionReason": default_reason,
                "resourceScope": resource_scope,
                "scoreBreakdown": {},
            }
            continue

        reason = ranked_node.selection_reason if ranked_node.score > 0 else default_reason
        evidence_by_path[node.node_path] = {
            "retrievalScore": ranked_node.score,
            "matchedTerms": list(ranked_node.matched_terms),
            "selectionReason": reason,
            "resourceScope": resource_scope,
            "scoreBreakdown": ranked_node.score_breakdown,
        }

    return evidence_by_path


def _extend_with_broad_substantive_nodes(
    selected_nodes: list[ResourceNode],
    candidate_nodes: list[ResourceNode],
) -> list[ResourceNode]:
    seen_paths = {node.node_path for node in selected_nodes}
    section_counts: dict[str, int] = {}
    content_chars = 0
    for node in selected_nodes:
        section_key = _section_stable_key(node)
        section_counts[section_key] = section_counts.get(section_key, 0) + 1
        content_chars += len(node.content)

    for node in candidate_nodes:
        if not _is_substantive_query_node(node):
            continue
        content_chars = _add_selected_query_node(
            selected_nodes,
            seen_paths,
            section_counts,
            node,
            content_chars=content_chars,
            enforce_section_limit=True,
        )
        if len(selected_nodes) >= _MAX_SELECTED_QUERY_NODES:
            break

    return selected_nodes


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
    excluded_segments = findall(rf"{_EXCLUSION_PREFIX_PATTERN}([^{_CLAUSE_BOUNDARY_CHARS}]+)", value)
    excluded_segments.extend(findall(r"不要把(.+?)(?:当作|作为|当)", value))
    if not excluded_segments:
        return []
    return _build_query_terms(*excluded_segments)


def _remove_excluded_query_segments(value: str) -> str:
    without_exclusion_clauses = sub(rf"{_EXCLUSION_PREFIX_PATTERN}[^{_CLAUSE_BOUNDARY_CHARS}]+", " ", value)
    return sub(r"不要把.+?(?:当作|作为|当)[^。；;!?！？]+", " ", without_exclusion_clauses)


def _extract_focus_query_terms(value: str) -> list[str]:
    focus_segments = findall(
        rf"(?:只想|想要|想|只)(?:解释|讲|聊|覆盖)([^{_CLAUSE_BOUNDARY_CHARS}]+?)(?:[{_CLAUSE_BOUNDARY_CHARS}]|{_EXCLUSION_PREFIX_PATTERN}|$)",
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


def _count_term_occurrences(haystack: str, term: str) -> int:
    normalized_term = term.lower()
    if not normalized_term:
        return 0
    return haystack.count(normalized_term)


def _node_haystacks(node: ResourceNode) -> tuple[str, str]:
    return node.title.lower(), f"{node.content}\n{node.node_path}".lower()


def _node_length(node: ResourceNode) -> int:
    token_count = len(_build_query_terms(node.title, node.content))
    return max(token_count, len(node.content) // 4, 1)


def _document_frequencies(candidate_nodes: list[ResourceNode], terms: list[str]) -> dict[str, int]:
    frequencies: dict[str, int] = {}
    unique_terms = list(dict.fromkeys(terms))
    for term in unique_terms:
        frequencies[term] = sum(
            1
            for node in candidate_nodes
            if _count_term_occurrences(_node_haystacks(node)[0], term)
            or _count_term_occurrences(_node_haystacks(node)[1], term)
        )
    return frequencies


def _bm25_term_score(
    *,
    term_count: int,
    doc_length: int,
    avg_doc_length: float,
    document_frequency: int,
    total_documents: int,
) -> float:
    if term_count <= 0 or document_frequency <= 0 or total_documents <= 0:
        return 0.0
    k1 = 1.2
    b = 0.75
    idf = log(1 + (total_documents - document_frequency + 0.5) / (document_frequency + 0.5))
    denominator = term_count + k1 * (1 - b + b * (doc_length / max(avg_doc_length, 1.0)))
    return idf * ((term_count * (k1 + 1)) / denominator)


def _bm25_group_score(
    node: ResourceNode,
    *,
    terms: list[str],
    title_weight: float,
    content_weight: float,
    document_frequencies: dict[str, int],
    total_documents: int,
    avg_doc_length: float,
) -> tuple[float, list[str]]:
    if not terms:
        return 0.0, []

    title_haystack, content_haystack = _node_haystacks(node)
    doc_length = _node_length(node)
    score = 0.0
    matched_terms: list[str] = []
    seen_matches: set[str] = set()

    for term in terms:
        title_count = _count_term_occurrences(title_haystack, term)
        content_count = _count_term_occurrences(content_haystack, term)
        if title_count <= 0 and content_count <= 0:
            continue
        if term not in seen_matches:
            seen_matches.add(term)
            matched_terms.append(term)
        document_frequency = document_frequencies.get(term, 0)
        score += title_weight * _bm25_term_score(
            term_count=title_count,
            doc_length=doc_length,
            avg_doc_length=avg_doc_length,
            document_frequency=document_frequency,
            total_documents=total_documents,
        )
        score += content_weight * _bm25_term_score(
            term_count=content_count,
            doc_length=doc_length,
            avg_doc_length=avg_doc_length,
            document_frequency=document_frequency,
            total_documents=total_documents,
        )

    return score, matched_terms


def _node_term_score(node: ResourceNode, terms: list[str]) -> int:
    if not terms:
        return 0
    title_haystack = node.title.lower()
    content_haystack = f"{node.content}\n{node.node_path}".lower()
    return _score_terms_against_node(
        title_haystack=title_haystack,
        content_haystack=content_haystack,
        query_terms=terms,
        title_weight=1,
        content_weight=1,
    )


def _node_matches_terms(node: ResourceNode, terms: list[str], *, minimum_score: int = 1) -> bool:
    return _node_term_score(node, terms) >= minimum_score


def _filter_excluded_candidate_nodes(
    candidate_nodes: list[ResourceNode],
    *,
    allow_terms: list[str],
    excluded_terms: list[str],
) -> list[ResourceNode]:
    if not excluded_terms:
        return candidate_nodes

    filtered_nodes = [
        node
        for node in candidate_nodes
        if not (
            _node_matches_terms(node, excluded_terms)
            and not _node_matches_terms(node, allow_terms, minimum_score=5)
        )
    ]
    return filtered_nodes or candidate_nodes


def _score_query_node(
    node: ResourceNode,
    *,
    focus_terms: list[str],
    question_terms: list[str],
    summary_terms: list[str],
    excluded_terms: list[str],
    document_frequencies: dict[str, int],
    total_documents: int,
    avg_doc_length: float,
) -> ScoredQueryNode:
    focus_score, focus_matches = _bm25_group_score(
        node,
        terms=focus_terms,
        title_weight=4.2,
        content_weight=2.8,
        document_frequencies=document_frequencies,
        total_documents=total_documents,
        avg_doc_length=avg_doc_length,
    )
    question_score, question_matches = _bm25_group_score(
        node,
        terms=question_terms,
        title_weight=2.8,
        content_weight=1.9,
        document_frequencies=document_frequencies,
        total_documents=total_documents,
        avg_doc_length=avg_doc_length,
    )
    summary_score, summary_matches = _bm25_group_score(
        node,
        terms=summary_terms,
        title_weight=1.1,
        content_weight=0.7,
        document_frequencies=document_frequencies,
        total_documents=total_documents,
        avg_doc_length=avg_doc_length,
    )
    excluded_score, excluded_matches = _bm25_group_score(
        node,
        terms=excluded_terms,
        title_weight=3.5,
        content_weight=2.2,
        document_frequencies=document_frequencies,
        total_documents=total_documents,
        avg_doc_length=avg_doc_length,
    )

    level_weight = _NODE_LEVEL_WEIGHTS.get(node.level, 1.0)
    positive_score = focus_score + question_score + summary_score
    final_score = max((positive_score - excluded_score) * level_weight, 0.0)
    matched_terms = tuple(dict.fromkeys(focus_matches + question_matches + summary_matches))
    dominant_source = "focus" if focus_score > 0 else "question" if question_score > 0 else "session" if summary_score > 0 else "none"
    if final_score <= 0:
        reason = "not selected: no positive evidence after exclusion filtering"
    else:
        reason = (
            f"bm25-like {dominant_source} match in current-resource scope; "
            f"level={node.level}; matched={', '.join(matched_terms[:6]) or 'none'}"
        )

    return ScoredQueryNode(
        score=round(final_score, 4),
        ordinal_sort=-node.ordinal,
        node=node,
        matched_terms=matched_terms,
        score_breakdown={
            "focus": round(focus_score, 4),
            "question": round(question_score, 4),
            "session": round(summary_score, 4),
            "excluded": round(excluded_score, 4),
            "levelWeight": level_weight,
            "final": round(final_score, 4),
        },
        selection_reason=reason,
    )


def _rank_query_nodes(
    candidate_nodes: list[ResourceNode],
    *,
    focus_terms: list[str],
    question_terms: list[str],
    summary_terms: list[str],
    excluded_terms: list[str],
) -> list[ScoredQueryNode]:
    all_terms = focus_terms + question_terms + summary_terms + excluded_terms
    document_frequencies = _document_frequencies(candidate_nodes, all_terms)
    total_documents = len(candidate_nodes)
    avg_doc_length = (
        sum(_node_length(node) for node in candidate_nodes) / total_documents
        if total_documents
        else 1.0
    )
    ranked_nodes = [
        _score_query_node(
                node,
                focus_terms=focus_terms,
                question_terms=question_terms,
                summary_terms=summary_terms,
                excluded_terms=excluded_terms,
                document_frequencies=document_frequencies,
                total_documents=total_documents,
                avg_doc_length=avg_doc_length,
        )
        for node in candidate_nodes
    ]
    return sorted(ranked_nodes, key=lambda item: (item.score, item.ordinal_sort), reverse=True)


def _pick_query_nodes_for_prompt(
    nodes: list[ResourceNode],
    *,
    resource_id: str,
    question: str,
    session_summary: str,
) -> QueryNodeSelection:
    resource_scope = f"current_resource:{resource_id}"
    is_generic_summary_question = _is_generic_summary_question(question)
    candidate_nodes = _pick_generic_summary_candidate_nodes(nodes) if is_generic_summary_question else _pick_query_nodes(nodes)
    if not candidate_nodes:
        return QueryNodeSelection(selected_nodes=[], retrieval_evidence_by_path={})

    focus_terms = _expand_query_terms(_extract_focus_query_terms(question))
    question_terms = _expand_query_terms(_build_query_terms(_remove_excluded_query_segments(question)))
    summary_terms = _expand_query_terms(
        _build_query_terms(_remove_excluded_query_segments(_extract_summary_focus(session_summary)))
    )
    excluded_terms = _expand_query_terms(_build_excluded_query_terms(question))
    candidate_nodes = _filter_excluded_candidate_nodes(
        candidate_nodes,
        allow_terms=focus_terms or question_terms,
        excluded_terms=excluded_terms,
    )

    if is_generic_summary_question:
        default_nodes = _pick_substantive_default_nodes(candidate_nodes)
        ranked_nodes = _rank_query_nodes(
            candidate_nodes,
            focus_terms=focus_terms,
            question_terms=question_terms,
            summary_terms=summary_terms,
            excluded_terms=excluded_terms,
        )
        selected_nodes = _select_ranked_query_nodes(
            ranked_nodes,
            seed_nodes=default_nodes,
            minimum_score=_MIN_SELECTED_QUERY_SCORE_WITH_EXCLUSIONS if excluded_terms else 0.0,
        )
        selected_nodes = _extend_with_broad_substantive_nodes(selected_nodes, candidate_nodes)
        return QueryNodeSelection(
            selected_nodes=selected_nodes,
            retrieval_evidence_by_path=_build_retrieval_evidence_by_path(
                selected_nodes=selected_nodes,
                ranked_nodes=ranked_nodes,
                resource_scope=resource_scope,
                default_reason="selected as substantive section for generic summary in current-resource scope",
            ),
        )

    if not focus_terms and not question_terms and not summary_terms:
        selected_nodes = _pick_substantive_default_nodes(candidate_nodes)
        return QueryNodeSelection(
            selected_nodes=selected_nodes,
            retrieval_evidence_by_path=_build_retrieval_evidence_by_path(
                selected_nodes=selected_nodes,
                ranked_nodes=[],
                resource_scope=resource_scope,
                default_reason="selected as default substantive node because no query terms were available",
            ),
        )

    ranked_nodes = _rank_query_nodes(
        candidate_nodes,
        focus_terms=focus_terms,
        question_terms=question_terms,
        summary_terms=summary_terms,
        excluded_terms=excluded_terms,
    )
    selected_nodes = _select_ranked_query_nodes(
        ranked_nodes,
        minimum_score=_MIN_SELECTED_QUERY_SCORE_WITH_EXCLUSIONS if excluded_terms else 0.0,
    )
    if not selected_nodes:
        return QueryNodeSelection(selected_nodes=[], retrieval_evidence_by_path={})
    return QueryNodeSelection(
        selected_nodes=selected_nodes,
        retrieval_evidence_by_path=_build_retrieval_evidence_by_path(
            selected_nodes=selected_nodes,
            ranked_nodes=ranked_nodes,
            resource_scope=resource_scope,
            default_reason="selected by current-resource fallback",
        ),
    )


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
    query_selection = _pick_query_nodes_for_prompt(
        resource_nodes,
        resource_id=payload.resource_id,
        question=payload.question,
        session_summary=payload.session_summary,
    )
    query_result = build_query_result(
        question=payload.question,
        session_summary=payload.session_summary,
        memory_items=payload.memory_items,
        selected_nodes=query_selection.selected_nodes,
        trace_id=trace_id,
        retrieval_evidence_by_path=query_selection.retrieval_evidence_by_path,
    )
    snapshots = [build_trace_node_snapshot(node=node) for node in query_selection.selected_nodes]
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
