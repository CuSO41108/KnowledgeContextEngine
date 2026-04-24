from fastapi.testclient import TestClient

from app.main import app


def test_index_resource_returns_required_contract_fields() -> None:
    client = TestClient(app)

    response = client.post(
        "/internal/resources/index",
        json={
            "resource_slug": "zhiguang-java-cache-playbook",
            "markdown": "# Java Cache\n## Redis\nCache aside keeps DB authoritative.",
            "previous_path_map": {
                "l1:s000": "resource://zhiguang-java-cache-playbook/l1/s000",
                "l2:s000:000": "resource://zhiguang-java-cache-playbook/l2/s000/000",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["resource_slug"] == "zhiguang-java-cache-playbook"
    assert payload["imported_count"] == 3
    assert len(payload["nodes"]) == 3
    assert payload["nodes"][0].keys() >= {
        "resource_slug",
        "level",
        "stable_key",
        "node_path",
        "parent_stable_key",
        "parent_node_path",
        "title",
        "content",
        "ordinal",
        "section_slug",
        "ancestry",
    }
    assert payload["nodes"][1]["stable_key"] == "l1:s000"
    assert payload["nodes"][1]["node_path"] == "resource://zhiguang-java-cache-playbook/l1/s000"
    assert payload["nodes"][2]["stable_key"] == "l2:s000:000"
    assert payload["nodes"][2]["node_path"] == "resource://zhiguang-java-cache-playbook/l2/s000/000"
