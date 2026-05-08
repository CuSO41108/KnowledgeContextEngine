from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models import IdentityBinding as IdentityBindingModel
from app.models import Memory as MemoryModel
from app.models import Resource as ResourceModel
from app.models import ResourceNode as ResourceNodeModel
from app.models import RetrievalTrace as RetrievalTraceModel
from app.models import RetrievalTraceNode as RetrievalTraceNodeModel
from app.models import Session as SessionModel
from app.models import SessionTurn as SessionTurnModel
from app.models import User as UserModel
from app.services.memory import extract_memory_candidates, summarize_session
from app.services.query import build_node_id
from app.services.query import build_trace_node_snapshot
from app.services.resource_nodes import ResourceNode
from app.services.resource_nodes import build_resource_nodes


_LEVEL_ORDER = {"l0": 0, "l1": 1, "l2": 2}


def _parse_uuid(value: str) -> UUID:
    return UUID(value)


def parse_node_id(node_id: str) -> tuple[str, str]:
    resource_slug, separator, stable_key = node_id.partition(":")
    if not separator or not resource_slug or not stable_key:
        raise ValueError(f"Invalid node id: {node_id}")
    return resource_slug, stable_key


def _sort_resource_rows(rows: list[ResourceNodeModel]) -> list[ResourceNodeModel]:
    return sorted(
        rows,
        key=lambda row: (
            _LEVEL_ORDER.get(row.level, 99),
            row.node_path,
            row.ordinal,
            row.stable_key,
        ),
    )


def _row_to_service_node(resource_slug: str, row: ResourceNodeModel) -> ResourceNode:
    ancestry = list(row.ancestry_json)
    parent_stable_key = ancestry[-1]["stable_key"] if ancestry else None
    parent_node_path = ancestry[-1]["node_path"] if ancestry else None
    return ResourceNode(
        resource_slug=resource_slug,
        level=row.level,
        stable_key=row.stable_key,
        node_path=row.node_path,
        parent_stable_key=parent_stable_key,
        parent_node_path=parent_node_path,
        title=row.title,
        content=row.content,
        ordinal=row.ordinal,
        section_slug=row.section_slug,
        ancestry=ancestry,
    )


def _serialize_tree_node(resource_slug: str, row: ResourceNodeModel, *, include_content: bool) -> dict[str, object]:
    parent_node_id = None
    ancestry = list(row.ancestry_json)
    if ancestry:
        parent_node_id = build_node_id(resource_slug=resource_slug, stable_key=ancestry[-1]["stable_key"])

    payload: dict[str, object] = {
        "nodeId": build_node_id(resource_slug=resource_slug, stable_key=row.stable_key),
        "nodePath": row.node_path,
        "level": row.level,
        "title": row.title,
        "parentNodeId": parent_node_id,
    }
    if include_content:
        payload["content"] = row.content
    return payload


def _serialize_trace_node(row: RetrievalTraceNodeModel) -> dict[str, object]:
    return {
        "nodeId": row.public_node_id,
        "nodePath": row.node_path,
        "level": row.level,
        "ancestry": list(row.ancestry_json),
        "snapshotContent": row.snapshot_content,
    }


def _build_snapshot_payload(resource_slug: str, row: ResourceNodeModel) -> dict[str, object]:
    snapshot = build_trace_node_snapshot(node=_row_to_service_node(resource_slug, row))
    return {
        "nodeId": snapshot.node_id,
        "nodePath": snapshot.node_path,
        "level": snapshot.level,
        "ancestry": snapshot.ancestry,
        "snapshotContent": snapshot.snapshot_content,
    }


def ensure_user_identity(
    db_session: DbSession,
    *,
    user_id: str,
    provider: str,
    external_user_id: str,
) -> UserModel:
    user_uuid = _parse_uuid(user_id)
    user = db_session.get(UserModel, user_uuid)
    if user is None:
        user = UserModel(id=user_uuid, display_name=external_user_id)
        db_session.add(user)
        db_session.flush()

    binding = db_session.scalar(
        select(IdentityBindingModel).where(
            IdentityBindingModel.provider == provider,
            IdentityBindingModel.external_user_id == external_user_id,
        )
    )
    if binding is None:
        db_session.add(
            IdentityBindingModel(
                user_id=user.id,
                provider=provider,
                external_user_id=external_user_id,
            )
        )
        db_session.flush()

    return user


def ensure_session(
    db_session: DbSession,
    *,
    session_key: str,
    user_id: str,
    provider: str,
    external_user_id: str,
    goal: str,
) -> tuple[SessionModel, bool]:
    user = ensure_user_identity(
        db_session,
        user_id=user_id,
        provider=provider,
        external_user_id=external_user_id,
    )
    session = db_session.scalar(select(SessionModel).where(SessionModel.session_key == session_key))
    created = False

    if session is None:
        session = SessionModel(
            user_id=user.id,
            session_key=session_key,
            provider=provider,
            mode="demo",
            goal=goal or None,
            summary="",
        )
        db_session.add(session)
        db_session.flush()
        created = True
    elif session.user_id != user.id:
        raise ValueError(f"Session {session_key} belongs to a different user.")

    if goal:
        session.goal = goal
        db_session.flush()

    return session, created


def list_user_memory_payload(
    db_session: DbSession,
    *,
    user_id: str,
    limit: int = 10,
) -> dict[str, object]:
    user_uuid = _parse_uuid(user_id)
    memory_rows = db_session.scalars(
        select(MemoryModel)
        .where(MemoryModel.user_id == user_uuid)
        .order_by(MemoryModel.salience.desc(), MemoryModel.id)
        .limit(limit)
    ).all()

    return {
        "userId": user_id,
        "memories": [
            {
                "channel": row.memory_channel.value,
                "type": row.memory_type.value,
                "content": row.content,
                "salience": row.salience,
            }
            for row in memory_rows
        ],
    }


def list_current_resource_nodes(
    db_session: DbSession,
    *,
    resource_slug: str,
) -> list[ResourceNode]:
    resource = db_session.scalar(select(ResourceModel).where(ResourceModel.slug == resource_slug))
    if resource is None:
        return []

    rows = db_session.scalars(
        select(ResourceNodeModel).where(
            ResourceNodeModel.resource_id == resource.id,
            ResourceNodeModel.is_current.is_(True),
        )
    ).all()
    return [_row_to_service_node(resource.slug, row) for row in _sort_resource_rows(rows)]


def upsert_resource_from_markdown(
    db_session: DbSession,
    *,
    provider: str,
    resource_slug: str,
    markdown: str,
    source_uri: str,
    previous_path_map: dict[str, str] | None = None,
) -> list[ResourceNode]:
    resource = db_session.scalar(select(ResourceModel).where(ResourceModel.slug == resource_slug))
    previous_nodes = list_current_resource_nodes(db_session, resource_slug=resource_slug)
    current_rows_by_stable_key: dict[str, ResourceNodeModel] = {}

    if resource is not None:
        current_rows = db_session.scalars(
            select(ResourceNodeModel).where(
                ResourceNodeModel.resource_id == resource.id,
                ResourceNodeModel.is_current.is_(True),
            )
        ).all()
        current_rows_by_stable_key = {row.stable_key: row for row in current_rows}

    new_nodes = build_resource_nodes(
        resource_slug=resource_slug,
        markdown=markdown,
        previous_path_map=previous_path_map,
        previous_nodes=previous_nodes,
    )
    document_title = new_nodes[0].title if new_nodes else resource_slug

    if resource is None:
        resource = ResourceModel(
            slug=resource_slug,
            provider=provider,
            title=document_title,
            source_uri=source_uri,
        )
        db_session.add(resource)
        db_session.flush()
    else:
        resource.provider = provider
        resource.title = document_title
        resource.source_uri = source_uri

    for row in current_rows_by_stable_key.values():
        row.is_current = False

    current_node_rows: dict[str, ResourceNodeModel] = {}
    for node in new_nodes:
        row = current_rows_by_stable_key.get(node.stable_key)
        if row is None:
            row = ResourceNodeModel(
                resource_id=resource.id,
                parent_node_id=None,
                level=node.level,
                stable_key=node.stable_key,
                node_path=node.node_path,
                title=node.title,
                content=node.content,
                ordinal=node.ordinal,
                section_slug=node.section_slug,
                ancestry_json=list(node.ancestry),
                is_current=True,
            )
            db_session.add(row)
        else:
            row.level = node.level
            row.node_path = node.node_path
            row.title = node.title
            row.content = node.content
            row.ordinal = node.ordinal
            row.section_slug = node.section_slug
            row.ancestry_json = list(node.ancestry)
            row.is_current = True
        current_node_rows[node.stable_key] = row

    db_session.flush()

    for node in new_nodes:
        row = current_node_rows[node.stable_key]
        if node.parent_stable_key is None:
            row.parent_node_id = None
            continue
        row.parent_node_id = current_node_rows[node.parent_stable_key].id

    db_session.flush()
    return new_nodes


def get_resource_tree_payload(
    db_session: DbSession,
    *,
    resource_slug: str,
    include_content: bool = False,
) -> dict[str, object] | None:
    resource = db_session.scalar(select(ResourceModel).where(ResourceModel.slug == resource_slug))
    if resource is None:
        return None

    rows = db_session.scalars(
        select(ResourceNodeModel).where(
            ResourceNodeModel.resource_id == resource.id,
            ResourceNodeModel.is_current.is_(True),
        )
    ).all()
    ordered_rows = _sort_resource_rows(rows)
    return {
        "resourceId": resource.slug,
        "title": resource.title,
        "nodes": [
            _serialize_tree_node(resource.slug, row, include_content=include_content)
            for row in ordered_rows
        ],
    }


def list_provider_resource_trees_payload(
    db_session: DbSession,
    *,
    provider: str,
) -> dict[str, object]:
    resource_rows = db_session.scalars(
        select(ResourceModel).where(ResourceModel.provider == provider).order_by(ResourceModel.slug)
    ).all()
    return {
        "provider": provider,
        "resources": [
            get_resource_tree_payload(
                db_session,
                resource_slug=resource.slug,
                include_content=True,
            )
            for resource in resource_rows
        ],
    }


def get_current_resource_node_payload(
    db_session: DbSession,
    *,
    node_id: str,
) -> dict[str, object] | None:
    resource_slug, stable_key = parse_node_id(node_id)
    resource = db_session.scalar(select(ResourceModel).where(ResourceModel.slug == resource_slug))
    if resource is None:
        return None

    row = db_session.scalar(
        select(ResourceNodeModel).where(
            ResourceNodeModel.resource_id == resource.id,
            ResourceNodeModel.stable_key == stable_key,
            ResourceNodeModel.is_current.is_(True),
        )
    )
    if row is None:
        return None
    return _build_snapshot_payload(resource_slug, row)


def persist_trace_payload(
    db_session: DbSession,
    *,
    trace_id: str,
    session_key: str,
    user_id: str,
    question: str,
    answer: str,
    used_contexts: dict[str, object],
    compression_summary: dict[str, int],
    snapshots: list[dict[str, object]],
) -> None:
    session = db_session.scalar(select(SessionModel).where(SessionModel.session_key == session_key))
    if session is None:
        raise ValueError(f"Session {session_key} does not exist.")

    trace_uuid = _parse_uuid(trace_id)
    existing_trace = db_session.get(RetrievalTraceModel, trace_uuid)
    if existing_trace is not None:
        return

    trace = RetrievalTraceModel(
        id=trace_uuid,
        session_id=session.id,
        user_id=_parse_uuid(user_id),
        query_text=question,
        answer_text=answer,
        session_summary=str(used_contexts["sessionSummary"]),
        used_memories_json=list(used_contexts["memories"]),
        used_resources_json=list(used_contexts["resources"]),
        drilldown_json={"resources": list(used_contexts["resources"])},
        compression_before=int(compression_summary["beforeContextChars"]),
        compression_after=int(compression_summary["afterContextChars"]),
    )
    db_session.add(trace)
    db_session.flush()

    for snapshot in snapshots:
        public_node_id = str(snapshot["nodeId"])
        resource_slug, stable_key = parse_node_id(public_node_id)
        resource = db_session.scalar(select(ResourceModel).where(ResourceModel.slug == resource_slug))
        if resource is None:
            raise ValueError(f"Resource {resource_slug} does not exist for trace persistence.")

        node_row = db_session.scalar(
            select(ResourceNodeModel).where(
                ResourceNodeModel.resource_id == resource.id,
                ResourceNodeModel.stable_key == stable_key,
            )
        )
        if node_row is None:
            raise ValueError(f"Node {public_node_id} does not exist for trace persistence.")

        db_session.add(
            RetrievalTraceNodeModel(
                trace_id=trace.id,
                node_id=node_row.id,
                public_node_id=public_node_id,
                node_path=str(snapshot["nodePath"]),
                level=str(snapshot["level"]),
                snapshot_content=str(snapshot["snapshotContent"]),
                ancestry_json=list(snapshot["ancestry"]),
            )
        )

    db_session.flush()


def get_trace_payload(
    db_session: DbSession,
    *,
    trace_id: str,
) -> dict[str, object] | None:
    trace_uuid = _parse_uuid(trace_id)
    trace = db_session.get(RetrievalTraceModel, trace_uuid)
    if trace is None:
        return None

    snapshot_rows = db_session.scalars(
        select(RetrievalTraceNodeModel).where(RetrievalTraceNodeModel.trace_id == trace.id)
    ).all()
    return {
        "traceId": str(trace.id),
        "question": trace.query_text,
        "answer": trace.answer_text,
        "usedContexts": {
            "sessionSummary": trace.session_summary,
            "memories": list(trace.used_memories_json),
            "resources": list(trace.used_resources_json),
        },
        "compressionSummary": {
            "beforeContextChars": trace.compression_before,
            "afterContextChars": trace.compression_after,
        },
        "nodeSnapshots": [_serialize_trace_node(row) for row in snapshot_rows],
    }


def get_trace_node_snapshot_payload(
    db_session: DbSession,
    *,
    trace_id: str,
    node_id: str,
) -> dict[str, object] | None:
    trace_uuid = _parse_uuid(trace_id)
    row = db_session.scalar(
        select(RetrievalTraceNodeModel).where(
            RetrievalTraceNodeModel.trace_id == trace_uuid,
            RetrievalTraceNodeModel.public_node_id == node_id,
        )
    )
    if row is None:
        return None
    return _serialize_trace_node(row)


def commit_session_turn(
    db_session: DbSession,
    *,
    session_key: str,
    user_id: str,
    goal: str,
    user_message: str,
    assistant_answer: str,
    trace_id: str,
) -> dict[str, object]:
    session = db_session.scalar(select(SessionModel).where(SessionModel.session_key == session_key))
    if session is None:
        raise ValueError(f"Session {session_key} does not exist.")
    if session.user_id != _parse_uuid(user_id):
        raise ValueError(f"Session {session_key} belongs to a different user.")

    trace = db_session.get(RetrievalTraceModel, _parse_uuid(trace_id))
    if trace is None:
        raise ValueError(f"Trace {trace_id} does not exist.")

    db_session.add(
        SessionTurnModel(
            session_id=session.id,
            trace_id=trace.id,
            user_message=user_message,
            assistant_answer=assistant_answer,
        )
    )
    db_session.flush()

    selected_resource_paths = [
        str(resource["nodePath"])
        for resource in list(trace.used_resources_json)
        if isinstance(resource, dict) and "nodePath" in resource
    ]
    candidates = extract_memory_candidates(
        session_goal=goal or session.goal or "",
        turns=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_answer},
        ],
        selected_resource_paths=selected_resource_paths,
    )

    committed_memory_count = 0
    for candidate in candidates:
        existing_memory = db_session.scalar(
            select(MemoryModel).where(
                MemoryModel.user_id == session.user_id,
                MemoryModel.memory_channel == candidate.channel,
                MemoryModel.memory_type == candidate.memory_type,
                MemoryModel.content == candidate.content,
            )
        )
        if existing_memory is None:
            db_session.add(
                MemoryModel(
                    user_id=session.user_id,
                    memory_channel=candidate.channel,
                    memory_type=candidate.memory_type,
                    salience=candidate.salience,
                    content=candidate.content,
                )
            )
            committed_memory_count += 1
            continue

        existing_memory.salience = max(existing_memory.salience, candidate.salience)

    turn_rows = db_session.scalars(
        select(SessionTurnModel).where(SessionTurnModel.session_id == session.id).order_by(SessionTurnModel.id)
    ).all()
    summarized_turns: list[dict[str, str]] = []
    for row in turn_rows:
        summarized_turns.append({"role": "user", "content": row.user_message})
        if row.assistant_answer:
            summarized_turns.append({"role": "assistant", "content": row.assistant_answer})

    session.goal = goal or session.goal
    session.summary = summarize_session(
        session_goal=session.goal or "",
        turns=summarized_turns,
    )
    db_session.flush()

    return {
        "status": "ok",
        "sessionId": session.session_key,
        "summary": session.summary,
        "committedMemoryCount": committed_memory_count,
    }
