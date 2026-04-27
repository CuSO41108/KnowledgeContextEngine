from __future__ import annotations

from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import Boolean
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


def _constrained_enum(enum_cls: type[Enum], enum_name: str) -> SqlEnum:
    return SqlEnum(
        enum_cls,
        name=enum_name,
        native_enum=False,
        values_callable=_enum_values,
        validate_strings=True,
    )


class MemoryChannel(str, Enum):
    USER = "user"
    TASK_EXPERIENCE = "task_experience"


class MemoryType(str, Enum):
    USER_GOAL = "user_goal"
    TOPIC_PREFERENCE = "topic_preference"
    EXPLANATION_PREFERENCE = "explanation_preference"
    FOLLOWUP_PATTERN = "followup_pattern"
    SUCCESSFUL_RESOURCE = "successful_resource"
    RETRIEVAL_PATTERN = "retrieval_pattern"
    REUSABLE_FRAGMENT = "reusable_fragment"
    PRIOR_RESOLUTION = "prior_resolution"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)


class IdentityBinding(Base):
    __tablename__ = "identity_bindings"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    external_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_uri: Mapped[str] = mapped_column(String(1000), nullable=False)


class ResourceNode(Base):
    __tablename__ = "resource_nodes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    resource_id: Mapped[UUID] = mapped_column(ForeignKey("resources.id"), nullable=False)
    parent_node_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("resource_nodes.id"),
        nullable=True,
    )
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    stable_key: Mapped[str] = mapped_column(String(255), nullable=False)
    node_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    section_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    ancestry_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class SessionTurn(Base):
    __tablename__ = "session_turns"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    trace_id: Mapped[UUID | None] = mapped_column(ForeignKey("retrieval_traces.id"), nullable=True)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    assistant_answer: Mapped[str | None] = mapped_column(Text, nullable=True)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    memory_channel: Mapped[MemoryChannel] = mapped_column(
        _constrained_enum(MemoryChannel, "memory_channel"),
        nullable=False,
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        _constrained_enum(MemoryType, "memory_type"),
        nullable=False,
    )
    salience: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class RetrievalTrace(Base):
    __tablename__ = "retrieval_traces"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    session_summary: Mapped[str] = mapped_column(Text, nullable=False)
    used_memories_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    used_resources_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    drilldown_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    compression_before: Mapped[int] = mapped_column(Integer, nullable=False)
    compression_after: Mapped[int] = mapped_column(Integer, nullable=False)


class RetrievalTraceNode(Base):
    __tablename__ = "retrieval_trace_nodes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    trace_id: Mapped[UUID] = mapped_column(ForeignKey("retrieval_traces.id"), nullable=False)
    node_id: Mapped[UUID] = mapped_column(ForeignKey("resource_nodes.id"), nullable=False)
    public_node_id: Mapped[str] = mapped_column(String(1000), nullable=False)
    node_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    snapshot_content: Mapped[str] = mapped_column(Text, nullable=False)
    ancestry_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
