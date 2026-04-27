from __future__ import annotations

import os
import sys
from pprint import pprint

import httpx

from wait_for_http import wait_for_http


QUESTION = "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?"
FOLLOW_UP_QUESTION = "Make it even shorter for Zhiguang."
GOAL = "write a Zhiguang reply about Redis cache-aside"
SESSION_ID = "demo-history"


def required_env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def main() -> int:
    gateway_base_url = required_env("GATEWAY_BASE_URL", "http://gateway-java:8080").rstrip("/")
    engine_base_url = required_env("ENGINE_BASE_URL", "http://engine-python:8000").rstrip("/")
    api_key = required_env("DEMO_API_KEY", "demo-key")
    provider = required_env("DEMO_PROVIDER", "demo_local")
    external_user_id = required_env("DEMO_EXTERNAL_USER_ID", "demo-user-1")
    resource_dir = required_env("DEMO_RESOURCE_DIR", "/workspace/data/demo-resources")

    wait_for_http(f"{engine_base_url}/health", timeout=90.0, interval=2.0)
    wait_for_http(f"{gateway_base_url}/api/v1/health", timeout=90.0, interval=2.0)

    headers = {"X-API-Key": api_key}

    with httpx.Client(timeout=20.0) as client:
        import_response = client.post(
            f"{gateway_base_url}/api/v1/resources/import",
            headers=headers,
            json={
                "provider": provider,
                "resourceDir": resource_dir,
            },
        )
        import_response.raise_for_status()
        imported_payload = import_response.json()

        if imported_payload.get("importedCount", 0) < 5:
            raise RuntimeError(f"Expected at least 5 imported demo resources, got {imported_payload!r}")

        session_response = client.post(
            f"{gateway_base_url}/api/v1/sessions",
            headers=headers,
            json={
                "provider": provider,
                "externalUserId": external_user_id,
                "sessionId": SESSION_ID,
                "goal": GOAL,
            },
        )
        session_response.raise_for_status()

        query_response = client.post(
            f"{gateway_base_url}/api/v1/sessions/{SESSION_ID}/query",
            headers=headers,
            json={
                "provider": provider,
                "externalUserId": external_user_id,
                "message": QUESTION,
                "goal": GOAL,
            },
        )
        query_response.raise_for_status()
        query_payload = query_response.json()

        memories = query_payload["usedContexts"]["memories"]
        if not any(memory["channel"] == "user" for memory in memories):
            raise RuntimeError(f"Expected at least one user memory, got {memories!r}")

        trace_id = query_payload["traceId"]
        commit_response = client.post(
            f"{gateway_base_url}/api/v1/sessions/{SESSION_ID}/commit",
            headers=headers,
            json={
                "provider": provider,
                "externalUserId": external_user_id,
                "userMessage": QUESTION,
                "assistantAnswer": query_payload["answer"],
                "traceId": trace_id,
                "goal": GOAL,
            },
        )
        commit_response.raise_for_status()
        commit_payload = commit_response.json()

        persisted_session_response = client.post(
            f"{gateway_base_url}/api/v1/sessions",
            headers=headers,
            json={
                "provider": provider,
                "externalUserId": external_user_id,
                "sessionId": SESSION_ID,
                "goal": GOAL,
            },
        )
        persisted_session_response.raise_for_status()
        persisted_session_payload = persisted_session_response.json()

        if persisted_session_payload.get("turnCount", 0) < 1:
            raise RuntimeError(
                f"Expected persisted session turn count >= 1, got {persisted_session_payload!r}"
            )
        if not str(persisted_session_payload.get("summary", "")).strip():
            raise RuntimeError(f"Expected persisted session summary, got {persisted_session_payload!r}")

        follow_up_response = client.post(
            f"{gateway_base_url}/api/v1/sessions/{SESSION_ID}/query",
            headers=headers,
            json={
                "provider": provider,
                "externalUserId": external_user_id,
                "message": FOLLOW_UP_QUESTION,
                "goal": GOAL,
            },
        )
        follow_up_response.raise_for_status()
        follow_up_payload = follow_up_response.json()

        follow_up_memories = follow_up_payload["usedContexts"]["memories"]
        if not any(memory["channel"] == "task_experience" for memory in follow_up_memories):
            raise RuntimeError(
                "Expected persisted task experience memory during follow-up query, "
                f"got {follow_up_memories!r}"
            )

        trace_response = client.get(
            f"{gateway_base_url}/api/v1/traces/{trace_id}",
            headers=headers,
        )
        trace_response.raise_for_status()
        trace_payload = trace_response.json()

    print("Seeded demo data successfully.")
    pprint(
        {
            "importedCount": imported_payload["importedCount"],
            "resourceIds": imported_payload["resourceIds"],
            "committedMemoryCount": commit_payload["committedMemoryCount"],
            "persistedTurnCount": persisted_session_payload["turnCount"],
            "seedTraceId": trace_payload["traceId"],
            "followUpTraceId": follow_up_payload["traceId"],
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # pragma: no cover - bootstrap reporting path
        print(f"Seed demo data failed: {error}", file=sys.stderr)
        raise
