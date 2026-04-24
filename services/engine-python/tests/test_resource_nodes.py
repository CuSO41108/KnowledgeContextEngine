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
