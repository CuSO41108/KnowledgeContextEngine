from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, String, Uuid

from app.models import Base, MemoryChannel, MemoryType
from app.settings import settings


def test_settings_expose_env_driven_database_url() -> None:
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_metadata_contains_required_tables_and_columns() -> None:
    expected_columns = {
        "users": {"id", "display_name"},
        "identity_bindings": {
            "id",
            "user_id",
            "provider",
            "external_user_id",
            "external_tenant_id",
        },
        "resources": {"id", "provider", "title", "source_uri"},
        "resource_nodes": {
            "id",
            "resource_id",
            "parent_node_id",
            "level",
            "stable_key",
            "node_path",
            "content",
        },
        "sessions": {"id", "user_id", "mode", "goal", "summary"},
        "session_turns": {"id", "session_id", "user_message", "assistant_answer"},
        "memories": {"id", "user_id", "memory_channel", "memory_type", "salience", "content"},
        "retrieval_traces": {
            "id",
            "session_id",
            "user_id",
            "query_text",
            "drilldown_json",
            "compression_before",
            "compression_after",
        },
        "retrieval_trace_nodes": {
            "id",
            "trace_id",
            "node_id",
            "node_path",
            "level",
            "snapshot_content",
            "ancestry_json",
        },
    }

    assert expected_columns.keys() <= Base.metadata.tables.keys()

    for table_name, columns in expected_columns.items():
        table = Base.metadata.tables[table_name]
        assert columns <= set(table.columns.keys())


def test_schema_uses_uuid_identifiers_for_primary_and_foreign_keys() -> None:
    expected_uuid_columns = {
        "users": {"id"},
        "identity_bindings": {"id", "user_id"},
        "resources": {"id"},
        "resource_nodes": {"id", "resource_id", "parent_node_id"},
        "sessions": {"id", "user_id"},
        "session_turns": {"id", "session_id"},
        "memories": {"id", "user_id"},
        "retrieval_traces": {"id", "session_id", "user_id"},
        "retrieval_trace_nodes": {"id", "trace_id", "node_id"},
    }

    for table_name, column_names in expected_uuid_columns.items():
        table = Base.metadata.tables[table_name]
        for column_name in column_names:
            assert isinstance(table.c[column_name].type, Uuid)


def test_schema_contains_expected_foreign_keys() -> None:
    expected_foreign_keys = {
        "identity_bindings": {"user_id": "users.id"},
        "resource_nodes": {"resource_id": "resources.id", "parent_node_id": "resource_nodes.id"},
        "sessions": {"user_id": "users.id"},
        "session_turns": {"session_id": "sessions.id"},
        "memories": {"user_id": "users.id"},
        "retrieval_traces": {"session_id": "sessions.id", "user_id": "users.id"},
        "retrieval_trace_nodes": {"trace_id": "retrieval_traces.id", "node_id": "resource_nodes.id"},
    }

    for table_name, columns in expected_foreign_keys.items():
        table = Base.metadata.tables[table_name]
        for column_name, target in columns.items():
            foreign_keys = {fk.target_fullname for fk in table.c[column_name].foreign_keys}
            assert target in foreign_keys


def test_optional_and_future_facing_fields_match_spec() -> None:
    identity_bindings = Base.metadata.tables["identity_bindings"]
    sessions = Base.metadata.tables["sessions"]
    memories = Base.metadata.tables["memories"]
    resource_nodes = Base.metadata.tables["resource_nodes"]
    retrieval_trace_nodes = Base.metadata.tables["retrieval_trace_nodes"]

    assert identity_bindings.c.external_tenant_id.nullable is True
    assert sessions.c.goal.nullable is True
    assert isinstance(memories.c.salience.type, Integer)
    assert isinstance(resource_nodes.c.level.type, String)
    assert isinstance(retrieval_trace_nodes.c.level.type, String)


def test_memory_enums_are_constrained() -> None:
    assert MemoryChannel.TASK_EXPERIENCE.value == "task_experience"
    assert MemoryType.SUCCESSFUL_RESOURCE.value == "successful_resource"
    memories = Base.metadata.tables["memories"]
    memory_channel_type = memories.c.memory_channel.type
    memory_type_type = memories.c.memory_type.type

    assert isinstance(memory_channel_type, SqlEnum)
    assert isinstance(memory_type_type, SqlEnum)
    assert list(memory_channel_type.enums) == [channel.value for channel in MemoryChannel]
    assert list(memory_type_type.enums) == [memory_type.value for memory_type in MemoryType]
