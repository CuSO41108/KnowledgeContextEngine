from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = ROOT / "services" / "engine-python"
DEFAULT_CASES_PATH = ROOT / "eval" / "kce_v1_harness_cases.json"
DEFAULT_DB_PATH = ROOT / ".eval-runtime" / "kce-v1-harness.db"


def _load_cases(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _contains_all(values: list[str], expected_fragments: list[str]) -> list[str]:
    missing: list[str] = []
    for fragment in expected_fragments:
        if not any(fragment in value for value in values):
            missing.append(fragment)
    return missing


def _failures_for_response_text(text: str, case: dict[str, Any], *, field: str) -> list[str]:
    failures: list[str] = []
    for fragment in case.get(f"expected_{field}_contains", []):
        if fragment not in text:
            failures.append(f"{field} missing expected fragment: {fragment}")
    for fragment in case.get(f"forbidden_{field}_contains", []):
        if fragment in text:
            failures.append(f"{field} contains forbidden fragment: {fragment}")
    return failures


def _request_json(client: Any, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    response = getattr(client, method)(path, **kwargs)
    if response.status_code >= 400:
        raise AssertionError(f"{method.upper()} {path} returned {response.status_code}: {response.text}")
    return response.json()


def _evaluate_retrieval_case(client: Any, case: dict[str, Any]) -> dict[str, Any]:
    slug = case["resource_slug"]
    _request_json(
        client,
        "post",
        "/internal/resources/index",
        json={
            "provider": case.get("provider", "eval_local"),
            "resource_slug": slug,
            "markdown": case["markdown"],
            "source_uri": case.get("source_uri", f"eval://{slug}"),
        },
    )

    payload = _request_json(
        client,
        "post",
        "/internal/context/query",
        json={
            "question": case["question"],
            "resource_id": slug,
            "session_summary": case.get("session_summary", ""),
            "memory_items": case.get("memory_items", []),
        },
    )

    resources = payload["usedContexts"]["resources"]
    resource_paths = [resource["nodePath"] for resource in resources]
    failures: list[str] = []
    should_refuse = bool(case.get("shouldRefuse", False))

    if should_refuse and resources:
        failures.append(f"expected refusal with no selected resources, got {resource_paths}")
    if not should_refuse and not resources:
        failures.append("expected at least one selected evidence resource")

    failures.extend(
        f"resource path missing expected fragment: {fragment}"
        for fragment in _contains_all(resource_paths, case.get("expected_node_path_contains", []))
    )
    for fragment in case.get("forbidden_node_path_contains", []):
        if any(fragment in path for path in resource_paths):
            failures.append(f"resource path contains forbidden fragment: {fragment}")

    expected_first_path = case.get("expected_first_node_path")
    if expected_first_path and (not resource_paths or resource_paths[0] != expected_first_path):
        actual = resource_paths[0] if resource_paths else "<none>"
        failures.append(f"first resource path expected {expected_first_path}, got {actual}")

    expected_evidence_node = case.get("expectedEvidenceNode", "")
    if expected_evidence_node and expected_evidence_node not in resource_paths:
        failures.append(f"expected evidence node missing: {expected_evidence_node}")

    failures.extend(_failures_for_response_text(payload["answer"], case, field="answer"))

    trace_ok = False
    evidence_trace_ok = not resources
    if resources:
        first_resource = resources[0]
        evidence_trace_ok = (
            isinstance(first_resource.get("retrievalScore"), (int, float))
            and isinstance(first_resource.get("matchedTerms"), list)
            and isinstance(first_resource.get("selectionReason"), str)
            and bool(first_resource.get("selectionReason"))
            and isinstance(first_resource.get("resourceScope"), str)
            and first_resource.get("resourceScope", "").startswith("current_resource:")
            and isinstance(first_resource.get("scoreBreakdown"), dict)
        )
        if not evidence_trace_ok:
            failures.append("first selected resource is missing retrieval evidence trace fields")

    if case.get("expect_trace_requeryable") and resources:
        trace = _request_json(client, "get", f"/internal/traces/{payload['traceId']}")
        first_resource = resources[0]
        trace_node = _request_json(
            client,
            "get",
            f"/internal/traces/{payload['traceId']}/nodes/{first_resource['nodeId']}",
        )
        trace_ok = (
            trace["traceId"] == payload["traceId"]
            and trace_node["nodePath"] == first_resource["nodePath"]
            and bool(trace_node["snapshotContent"])
        )
        if not trace_ok:
            failures.append("trace is not re-queryable for the first selected resource node")

    return {
        "id": case["id"],
        "postId": case.get("postId", ""),
        "question": case["question"],
        "expectedEvidenceNode": case.get("expectedEvidenceNode", ""),
        "shouldRefuse": should_refuse,
        "actualAnswer": payload["answer"],
        "qualityNotes": case.get("qualityNotes", ""),
        "axis": case.get("axis", []),
        "passed": not failures,
        "failures": failures,
        "traceRequeryable": trace_ok,
        "evidenceTracePresent": evidence_trace_ok,
        "selectedNodePaths": resource_paths,
        "answerPreview": payload["answer"][:240],
    }


def _evaluate_memory_case(client: Any, case: dict[str, Any]) -> dict[str, Any]:
    payload = _request_json(
        client,
        "post",
        "/internal/memory/extract",
        json={
            "session_goal": case["session_goal"],
            "turns": case["turns"],
            "selected_resource_paths": case.get("selected_resource_paths", []),
        },
    )
    candidates = payload["candidates"]
    channels = [candidate["channel"] for candidate in candidates]
    types = [candidate["memory_type"] for candidate in candidates]
    contents = [candidate["content"] for candidate in candidates]
    failures: list[str] = []

    failures.extend(
        f"memory channel missing: {channel}"
        for channel in case.get("expected_channels", [])
        if channel not in channels
    )
    failures.extend(
        f"memory type missing: {memory_type}"
        for memory_type in case.get("expected_types", [])
        if memory_type not in types
    )
    failures.extend(
        f"memory content missing expected fragment: {fragment}"
        for fragment in _contains_all(contents, case.get("expected_content_contains", []))
    )

    return {
        "id": case["id"],
        "axis": case.get("axis", []),
        "passed": not failures,
        "failures": failures,
        "candidateCount": payload["candidate_count"],
        "channels": channels,
        "types": types,
    }


def _evaluate_session_case(client: Any, case: dict[str, Any]) -> dict[str, Any]:
    payload = _request_json(
        client,
        "post",
        "/internal/session/summarize",
        json={
            "session_goal": case["session_goal"],
            "turns": case["turns"],
        },
    )
    summary = payload["summary"]
    failures: list[str] = []

    for fragment in case.get("expected_summary_contains", []):
        if fragment not in summary:
            failures.append(f"summary missing expected fragment: {fragment}")
    for fragment in case.get("forbidden_summary_contains", []):
        if fragment in summary:
            failures.append(f"summary contains forbidden fragment: {fragment}")

    return {
        "id": case["id"],
        "axis": case.get("axis", []),
        "passed": not failures,
        "failures": failures,
        "summary": summary,
    }


def _build_client() -> Any:
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    os.environ["KCE_RUNTIME_DATABASE_URL"] = f"sqlite+pysqlite:///{DEFAULT_DB_PATH.as_posix()}"
    os.environ["ANSWER_LLM_ENABLED"] = "false"
    os.environ["KCE_INTERNAL_TOKEN"] = ""
    service_root = str(SERVICE_ROOT)
    if service_root not in sys.path:
        sys.path.insert(0, service_root)

    from fastapi.testclient import TestClient

    from app import models  # noqa: F401
    from app.db import Base, engine
    from app.main import app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


def run(cases_path: Path) -> dict[str, Any]:
    cases = _load_cases(cases_path)
    results: list[dict[str, Any]] = []

    with _build_client() as client:
        for case in cases.get("retrieval_cases", []):
            results.append(_evaluate_retrieval_case(client, case))
        for case in cases.get("memory_cases", []):
            results.append(_evaluate_memory_case(client, case))
        for case in cases.get("session_cases", []):
            results.append(_evaluate_session_case(client, case))

    failed = [result for result in results if not result["passed"]]
    return {
        "version": cases.get("version"),
        "ok": not failed,
        "summary": {
            "total": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the KCE v1 retrieval/memory/trace harness.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Path to the harness case JSON file.",
    )
    args = parser.parse_args()

    report = run(args.cases)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
