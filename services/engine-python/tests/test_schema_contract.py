from app.models import Base, MemoryChannel, MemoryType
from app.settings import settings


def test_settings_expose_env_driven_database_url() -> None:
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_metadata_contains_required_tables() -> None:
    assert {
        "users",
        "identity_bindings",
        "resources",
        "resource_nodes",
        "sessions",
        "session_turns",
        "memories",
        "retrieval_traces",
        "retrieval_trace_nodes",
    }.issubset(Base.metadata.tables)


def test_memory_enums_are_constrained() -> None:
    assert MemoryChannel.TASK_EXPERIENCE.value == "task_experience"
    assert MemoryType.SUCCESSFUL_RESOURCE.value == "successful_resource"
