from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models import MemoryChannel, MemoryType
from app.services.memory import extract_memory_candidates, summarize_session
from app.services.resource_nodes import ResourceNode, build_resource_nodes
from app.settings import settings

router = APIRouter()
_resource_index_store: dict[str, list[ResourceNode]] = {}


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
