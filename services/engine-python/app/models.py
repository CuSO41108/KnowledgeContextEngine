from __future__ import annotations

from enum import Enum
from typing import Any

from app.db import Base

try:
    from sqlalchemy import Boolean, Enum as SqlEnum, ForeignKey, Integer, String, Table
    from sqlalchemy.orm import Mapped, mapped_column

    SQLALCHEMY_AVAILABLE = True
except ModuleNotFoundError:
    SQLALCHEMY_AVAILABLE = False


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


if SQLALCHEMY_AVAILABLE:
    class User(Base):
        __tablename__ = "users"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


    class IdentityBinding(Base):
        __tablename__ = "identity_bindings"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
        provider: Mapped[str] = mapped_column(String(100), nullable=False)
        subject: Mapped[str] = mapped_column(String(255), nullable=False)


    class Resource(Base):
        __tablename__ = "resources"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        uri: Mapped[str] = mapped_column(String(500), nullable=False)


    class ResourceNode(Base):
        __tablename__ = "resource_nodes"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), nullable=False)
        node_key: Mapped[str] = mapped_column(String(255), nullable=False)


    class Session(Base):
        __tablename__ = "sessions"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


    class SessionTurn(Base):
        __tablename__ = "session_turns"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
        turn_index: Mapped[int] = mapped_column(Integer, nullable=False)


    class Memory(Base):
        __tablename__ = "memories"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
        channel: Mapped[MemoryChannel] = mapped_column(SqlEnum(MemoryChannel), nullable=False)
        memory_type: Mapped[MemoryType] = mapped_column(SqlEnum(MemoryType), nullable=False)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


    class RetrievalTrace(Base):
        __tablename__ = "retrieval_traces"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        session_turn_id: Mapped[int] = mapped_column(
            ForeignKey("session_turns.id"),
            nullable=False,
        )


    class RetrievalTraceNode(Base):
        __tablename__ = "retrieval_trace_nodes"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        retrieval_trace_id: Mapped[int] = mapped_column(
            ForeignKey("retrieval_traces.id"),
            nullable=False,
        )
        resource_node_id: Mapped[int] = mapped_column(
            ForeignKey("resource_nodes.id"),
            nullable=False,
        )
else:
    def _register_table(name: str) -> None:
        Base.metadata.tables.setdefault(name, {"name": name})


    for _table_name in (
        "users",
        "identity_bindings",
        "resources",
        "resource_nodes",
        "sessions",
        "session_turns",
        "memories",
        "retrieval_traces",
        "retrieval_trace_nodes",
    ):
        _register_table(_table_name)
