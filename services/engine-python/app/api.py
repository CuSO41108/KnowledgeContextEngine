from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

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


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "mode": settings.app_mode,
    }


@router.post("/internal/resources/index", response_model=ResourceIndexResponse)
def index_resource(payload: ResourceIndexRequest) -> ResourceIndexResponse:
    nodes = build_resource_nodes(
        resource_slug=payload.resource_slug,
        markdown=payload.markdown,
        previous_path_map=payload.previous_path_map,
    )
    _resource_index_store[payload.resource_slug] = nodes
    return ResourceIndexResponse(
        resource_slug=payload.resource_slug,
        imported_count=len(nodes),
        nodes=[ResourceNodeResponse.model_validate(node.to_dict()) for node in nodes],
    )
