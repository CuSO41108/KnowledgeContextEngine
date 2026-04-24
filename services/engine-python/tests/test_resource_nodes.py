from app.services.resource_nodes import build_resource_nodes


def test_build_resource_nodes_preserves_l2_path_by_stable_key() -> None:
    markdown = "# Java Cache\n## Redis\nCache aside keeps DB authoritative.\nCache invalidation follows writes."

    nodes = build_resource_nodes(
        resource_slug="zhiguang-java-cache-playbook",
        markdown=markdown,
        previous_path_map={
            "l1:redis": "resource://zhiguang-java-cache-playbook/l1/redis",
            "l2:redis:000": "resource://zhiguang-java-cache-playbook/l2/redis/000",
        },
    )

    assert any(node.stable_key == "l1:redis" and node.node_path.endswith("/l1/redis") for node in nodes)
    assert any(node.stable_key == "l2:redis:000" and node.node_path.endswith("/l2/redis/000") for node in nodes)
