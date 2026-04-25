from app.services.resource_nodes import build_resource_nodes


def test_build_resource_nodes_preserves_paths_by_structural_stable_key() -> None:
    markdown = "# Java Cache\n## Redis\nCache aside keeps DB authoritative.\nCache invalidation follows writes."

    nodes = build_resource_nodes(
        resource_slug="zhiguang-java-cache-playbook",
        markdown=markdown,
        previous_path_map={
            "l1:s000": "resource://zhiguang-java-cache-playbook/l1/s000",
            "l2:s000:000": "resource://zhiguang-java-cache-playbook/l2/s000/000",
        },
    )

    assert any(node.stable_key == "l1:s000" and node.node_path.endswith("/l1/s000") for node in nodes)
    assert any(node.stable_key == "l2:s000:000" and node.node_path.endswith("/l2/s000/000") for node in nodes)


def test_build_resource_nodes_keeps_duplicate_titles_uniquely_addressable() -> None:
    markdown = (
        "# Java Cache\n"
        "## Redis\n"
        "Primary cache guidance.\n\n"
        "## Redis\n"
        "Secondary cache guidance."
    )

    nodes = build_resource_nodes(resource_slug="zhiguang-java-cache-playbook", markdown=markdown)

    l1_nodes = [node for node in nodes if node.level == "l1"]
    l2_nodes = [node for node in nodes if node.level == "l2"]

    assert [node.stable_key for node in l1_nodes] == ["l1:s000", "l1:s001"]
    assert [node.node_path for node in l1_nodes] == [
        "resource://zhiguang-java-cache-playbook/l1/s000",
        "resource://zhiguang-java-cache-playbook/l1/s001",
    ]
    assert [node.stable_key for node in l2_nodes] == ["l2:s000:000", "l2:s001:000"]
    assert [node.node_path for node in l2_nodes] == [
        "resource://zhiguang-java-cache-playbook/l2/s000/000",
        "resource://zhiguang-java-cache-playbook/l2/s001/000",
    ]


def test_build_resource_nodes_preserves_lineage_when_heading_is_renamed() -> None:
    original_markdown = "# Java Cache\n## Redis\nCache aside keeps DB authoritative."
    renamed_markdown = "# Java Cache\n## Caching Patterns\nCache aside keeps DB authoritative."

    original_nodes = build_resource_nodes(
        resource_slug="zhiguang-java-cache-playbook",
        markdown=original_markdown,
    )
    renamed_nodes = build_resource_nodes(
        resource_slug="zhiguang-java-cache-playbook",
        markdown=renamed_markdown,
    )

    assert [node.stable_key for node in original_nodes if node.level == "l1"] == ["l1:s000"]
    assert [node.stable_key for node in renamed_nodes if node.level == "l1"] == ["l1:s000"]
    assert [node.stable_key for node in original_nodes if node.level == "l2"] == ["l2:s000:000"]
    assert [node.stable_key for node in renamed_nodes if node.level == "l2"] == ["l2:s000:000"]
    assert [node.section_slug for node in original_nodes if node.level == "l1"] == ["redis"]
    assert [node.section_slug for node in renamed_nodes if node.level == "l1"] == ["caching-patterns"]


def test_build_resource_nodes_uses_coarse_summary_for_l0_content() -> None:
    markdown = "# Java Cache\n## Redis\nCache aside keeps DB authoritative.\nCache invalidation follows writes."

    nodes = build_resource_nodes(resource_slug="zhiguang-java-cache-playbook", markdown=markdown)

    l0_node = next(node for node in nodes if node.level == "l0")

    assert l0_node.content == "Java Cache"
    assert l0_node.content != markdown


def test_build_resource_nodes_preserves_existing_sections_when_new_section_is_inserted_before() -> None:
    old_markdown = "# Doc\n## Redis\nfirst\n\n## Memcached\nsecond"
    new_markdown = "# Doc\n## Overview\nintro\n\n## Redis\nfirst\n\n## Memcached\nsecond"

    old_nodes = build_resource_nodes(resource_slug="cache-doc", markdown=old_markdown)
    new_nodes = build_resource_nodes(
        resource_slug="cache-doc",
        markdown=new_markdown,
        previous_nodes=old_nodes,
    )

    old_redis = next(node for node in old_nodes if node.level == "l1" and node.content == "first")
    old_memcached = next(node for node in old_nodes if node.level == "l1" and node.content == "second")
    new_redis = next(node for node in new_nodes if node.level == "l1" and node.content == "first")
    new_memcached = next(node for node in new_nodes if node.level == "l1" and node.content == "second")

    assert new_redis.stable_key == old_redis.stable_key
    assert new_redis.node_path == old_redis.node_path
    assert new_memcached.stable_key == old_memcached.stable_key
    assert new_memcached.node_path == old_memcached.node_path


def test_build_resource_nodes_preserves_existing_paragraph_when_new_paragraph_is_inserted_before() -> None:
    old_markdown = "# Doc\n## Redis\nfirst"
    new_markdown = "# Doc\n## Redis\nintro\n\nfirst"

    old_nodes = build_resource_nodes(resource_slug="cache-doc", markdown=old_markdown)
    new_nodes = build_resource_nodes(
        resource_slug="cache-doc",
        markdown=new_markdown,
        previous_nodes=old_nodes,
    )

    old_paragraph = next(node for node in old_nodes if node.level == "l2" and node.content == "first")
    new_paragraph = next(node for node in new_nodes if node.level == "l2" and node.content == "first")

    assert new_paragraph.stable_key == old_paragraph.stable_key
    assert new_paragraph.node_path == old_paragraph.node_path


def test_build_resource_nodes_preserves_identity_across_same_structure_content_refresh() -> None:
    old_markdown = "# Doc\n## Redis\nOld snapshot content."
    new_markdown = "# Doc\n## Redis\nNew current content after reindex."

    old_nodes = build_resource_nodes(resource_slug="trace-history-doc", markdown=old_markdown)
    new_nodes = build_resource_nodes(
        resource_slug="trace-history-doc",
        markdown=new_markdown,
        previous_nodes=old_nodes,
    )

    old_section = next(node for node in old_nodes if node.level == "l1")
    old_paragraph = next(node for node in old_nodes if node.level == "l2")
    new_section = next(node for node in new_nodes if node.level == "l1")
    new_paragraph = next(node for node in new_nodes if node.level == "l2")

    assert new_section.stable_key == old_section.stable_key
    assert new_section.node_path == old_section.node_path
    assert new_paragraph.stable_key == old_paragraph.stable_key
    assert new_paragraph.node_path == old_paragraph.node_path
