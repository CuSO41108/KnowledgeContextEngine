# KnowledgeContextEngine V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, Context Engine-first MVP in `D:\code\KnowledgeContextEngine` that supports layered resources, dual-channel memory, stable `node_path`, re-queryable drill-down retrieval trace, a thin Java gateway, and a runnable Zhiguang-shaped demo chat.

**Architecture:** The Python engine owns persistence, resource ingestion, memory extraction, retrieval, fusion, trace persistence, and answer generation. The Java gateway owns public APIs, API-key auth, internal user resolution, and proxying to the engine. The Next.js demo chat is a thin Vercel AI SDK shell that renders answers and live trace metadata without owning core context logic.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, pgvector, pytest, pytest-cov, Java 21, Spring Boot 3, JUnit 5, TypeScript, Next.js, Vercel AI SDK, Vitest, PostgreSQL, Redis, Docker Compose

---

## File Structure

### Root

- Create: `D:\code\KnowledgeContextEngine\.env.example`
- Create: `D:\code\KnowledgeContextEngine\docker-compose.yml`
- Create: `D:\code\KnowledgeContextEngine\scripts\seed_demo_data.py`
- Create: `D:\code\KnowledgeContextEngine\scripts\wait_for_http.py`

### Shared Contracts

- Create: `D:\code\KnowledgeContextEngine\packages\contracts\openapi\gateway.yaml`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\json\query-response.schema.json`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\json\trace-response.schema.json`

### Python Engine

- Create: `D:\code\KnowledgeContextEngine\services\engine-python\pyproject.toml`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\main.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\settings.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\db.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\models.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\resource_nodes.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\memory.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\query.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\conftest.py`
- Keep and extend: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_health.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_schema_contract.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_resource_nodes.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_memory_channels.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_query_trace.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_trace_snapshots.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_demo_story_e2e.py`

### Java Gateway

- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\pom.xml`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\resources\application.yml`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\GatewayApplication.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\config\ApiKeyFilter.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\identity\IdentityService.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\client\EngineClient.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\SessionController.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\ResourceController.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\TraceController.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\ApiKeyFilterTest.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\SessionControllerTest.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\ResourceControllerTest.java`

### Demo Chat

- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\package.json`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\.env.local.example`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\next.config.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\tsconfig.json`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\vitest.config.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\app\page.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\app\api\chat\route.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\components\chat-shell.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\components\trace-panel.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\lib\gateway-client.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\src\lib\gateway-client.test.ts`

### Task 1: Bootstrap the Python Engine Runtime

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\pyproject.toml`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\main.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\settings.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\conftest.py`
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_health.py`

- [ ] **Step 1: Write the failing health test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_engine_metadata() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "engine-python",
        "mode": "standalone",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Write the minimal runtime**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "engine-python"
    app_mode: str = "standalone"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pip install -e services/engine-python[dev]`
Expected: package and dev dependencies install successfully

Run: `python -m pytest services/engine-python/tests/test_health.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python
git commit -m "feat: bootstrap python engine runtime"
```

### Task 2: Add Env-Driven Settings and Schema Foundations

**Files:**
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\app\settings.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\db.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\models.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_schema_contract.py`

- [ ] **Step 1: Write the failing schema contract test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_schema_contract.py -v`
Expected: FAIL with missing settings fields or missing model symbols

- [ ] **Step 3: Implement settings, db wiring, and base schema**

```python
class Settings(BaseSettings):
    app_name: str = "engine-python"
    app_mode: str = "standalone"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/kce"
    redis_url: str = "redis://localhost:6379/0"
```

```python
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_schema_contract.py -v`
Expected: PASS with `3 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app services/engine-python/tests/test_schema_contract.py
git commit -m "feat: add engine settings and schema foundations"
```

### Task 3: Implement Stable Resource Nodes and Import Pipeline

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\resource_nodes.py`
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_resource_nodes.py`

- [ ] **Step 1: Write the failing stable-path test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_resource_nodes.py -v`
Expected: FAIL with `ImportError` or missing `stable_key`

- [ ] **Step 3: Implement the builder and import route**

```python
stable_key = f"l2:{section_slug}:{index:03d}"
node_path = previous_path_map.get(
    stable_key,
    f"resource://{resource_slug}/l2/{section_slug}/{index:03d}",
)
```

The builder must:

- generate `L0`, `L1`, and `L2` nodes
- assign `stable_key` to every node
- derive `L2` identity from section lineage plus ordinal, not raw chunk text
- return enough metadata for later tree browsing and trace persistence

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_resource_nodes.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app/api.py services/engine-python/app/services/resource_nodes.py services/engine-python/tests/test_resource_nodes.py
git commit -m "feat: add stable layered resource nodes"
```

### Task 4: Implement Session Summaries and Dual-Channel Memory Services

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\memory.py`
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_memory_channels.py`

- [ ] **Step 1: Write the failing memory test**

```python
from app.models import MemoryChannel, MemoryType
from app.services.memory import extract_memory_candidates, summarize_session


def test_extract_memory_candidates_splits_user_and_task_memory() -> None:
    items = extract_memory_candidates(
        goal="write a Zhiguang reply about Redis cache-aside",
        user_message="I prefer concise Java explanations when replying on Zhiguang.",
        assistant_answer="Reuse the Redis section and the prior accepted answer pattern.",
        selected_node_paths=[
            "resource://zhiguang-java-cache-playbook/l1/redis",
            "resource://zhiguang-java-cache-playbook/l2/redis/000",
        ],
    )

    assert any(item.channel == MemoryChannel.USER and item.memory_type == MemoryType.EXPLANATION_PREFERENCE for item in items)
    assert any(item.channel == MemoryChannel.TASK_EXPERIENCE and item.memory_type == MemoryType.SUCCESSFUL_RESOURCE for item in items)


def test_summarize_session_keeps_goal_relevant_turns() -> None:
    summary = summarize_session(
        goal="write a Zhiguang reply about Redis cache-aside",
        turns=[
            "User is drafting a short Zhiguang answer about Redis cache-aside.",
            "Assistant recommends the Redis section and prior accepted answer trace.",
            "User jokes about coffee.",
        ],
    )

    assert "redis cache-aside" in summary.lower()
    assert "coffee" not in summary.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_memory_channels.py -v`
Expected: FAIL with missing service functions

- [ ] **Step 3: Implement memory extraction and session summarization**

```python
MemoryCandidate(
    channel=MemoryChannel.TASK_EXPERIENCE,
    memory_type=MemoryType.SUCCESSFUL_RESOURCE,
    salience=70,
    content=f"Helpful resource: {node_path}",
)
```

The service must:

- emit both `user` and `task_experience` channels
- preserve `memory_type`
- keep goal-relevant summary text
- expose internal endpoints for `/internal/memory/extract` and `/internal/session/summarize`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_memory_channels.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app/services/memory.py services/engine-python/app/api.py services/engine-python/tests/test_memory_channels.py
git commit -m "feat: add dual-channel memory services"
```

### Task 5: Implement Fused Query Pipeline and Re-queryable Trace Snapshots

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\query.py`
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_query_trace.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_trace_snapshots.py`

- [ ] **Step 1: Write the failing trace tests**

```python
from app.services.query import build_query_result, build_trace_node_snapshot


def test_build_query_result_returns_drilldown_trace() -> None:
    result = build_query_result(
        question="I am replying on Zhiguang about Redis cache-aside. How should I explain it briefly?",
        goal="write a Zhiguang reply about Redis cache-aside",
        session_summary="Goal=write a Zhiguang reply about Redis cache-aside.",
        memory_items=[
            {"channel": "user", "type": "explanation_preference", "content": "User prefers concise Java explanations."},
            {"channel": "task_experience", "type": "successful_resource", "content": "The Redis section worked in a prior accepted answer."},
        ],
        resource_candidates=[
            {"node_id": "node-l0", "level": "L0", "node_path": "resource://zhiguang-java-cache-playbook/l0/root", "content": "Java cache playbook"},
            {"node_id": "node-l1", "level": "L1", "node_path": "resource://zhiguang-java-cache-playbook/l1/redis", "content": "Redis"},
            {"node_id": "node-l2", "level": "L2", "node_path": "resource://zhiguang-java-cache-playbook/l2/redis/000", "content": "Cache-aside keeps the database authoritative."},
        ],
    )

    assert "Zhiguang" in result["answer"]
    assert result["usedContexts"]["resources"][0]["drilldownTrail"][-1] == "resource://zhiguang-java-cache-playbook/l2/redis/000"


def test_build_trace_node_snapshot_keeps_requeryable_identity() -> None:
    snapshot = build_trace_node_snapshot(
        trace_id="trace-demo-001",
        selected_candidate={
            "node_id": "node-l2",
            "level": "L2",
            "node_path": "resource://zhiguang-java-cache-playbook/l2/redis/000",
            "content": "Cache-aside keeps the database authoritative.",
        },
        drilldown=[
            "resource://zhiguang-java-cache-playbook/l0/root",
            "resource://zhiguang-java-cache-playbook/l1/redis",
            "resource://zhiguang-java-cache-playbook/l2/redis/000",
        ],
    )

    assert snapshot["nodeId"] == "node-l2"
    assert snapshot["ancestry"][1] == "resource://zhiguang-java-cache-playbook/l1/redis"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_query_trace.py services/engine-python/tests/test_trace_snapshots.py -v`
Expected: FAIL with missing query or trace helpers

- [ ] **Step 3: Implement query composition, trace persistence shape, and internal read routes**

```python
{
    "nodeId": selected["node_id"],
    "traceNodeId": trace_node_id,
    "nodePath": selected["node_path"],
    "drilldownTrail": drilldown,
}
```

This task must also expose internal routes for:

- `POST /internal/context/query`
- `GET /internal/resources/{resourceId}/tree`
- `GET /internal/resources/nodes/{nodeId}`
- `GET /internal/traces/{traceId}`
- `GET /internal/traces/{traceId}/nodes/{nodeId}`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_query_trace.py services/engine-python/tests/test_trace_snapshots.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app/api.py services/engine-python/app/services/query.py services/engine-python/tests/test_query_trace.py services/engine-python/tests/test_trace_snapshots.py
git commit -m "feat: add query pipeline and trace snapshots"
```

### Task 6: Bootstrap the Java Gateway and API-Key Auth

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\pom.xml`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\resources\application.yml`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\GatewayApplication.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\config\ApiKeyFilter.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\ApiKeyFilterTest.java`

- [ ] **Step 1: Write the failing auth test**

```java
@SpringBootTest
@AutoConfigureMockMvc
class ApiKeyFilterTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void rejectsRequestsWithoutApiKey() throws Exception {
        mockMvc.perform(get("/api/v1/health"))
                .andExpect(status().isUnauthorized());
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `mvn -f services/gateway-java/pom.xml -Dtest=ApiKeyFilterTest test`
Expected: FAIL with missing `pom.xml` or missing Spring Boot app

- [ ] **Step 3: Implement real gateway bootstrap**

```xml
<plugin>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-maven-plugin</artifactId>
</plugin>
```

```yaml
kce:
  auth:
    api-key: demo-key
  engine:
    base-url: http://localhost:8000
```

The gateway bootstrap must be Docker-friendly and overrideable through environment variables such as `KCE_AUTH_API_KEY` and `KCE_ENGINE_BASE_URL`.

- [ ] **Step 4: Run test to verify it passes**

Run: `mvn -f services/gateway-java/pom.xml -Dtest=ApiKeyFilterTest test`
Expected: PASS with `Tests run: 1, Failures: 0`

- [ ] **Step 5: Commit**

```bash
git add services/gateway-java
git commit -m "feat: bootstrap java gateway auth"
```

### Task 7: Add Identity Mapping, Engine Proxying, and Public Contracts

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\identity\IdentityService.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\client\EngineClient.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\SessionController.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\ResourceController.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\TraceController.java`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\openapi\gateway.yaml`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\json\query-response.schema.json`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\json\trace-response.schema.json`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\SessionControllerTest.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\ResourceControllerTest.java`

- [ ] **Step 1: Write the failing public API tests**

```java
mockMvc.perform(post("/api/v1/sessions/demo-session/query")
        .header("X-API-Key", "demo-key")
        .contentType(MediaType.APPLICATION_JSON)
        .content("""
            {
              "provider": "demo_local",
              "externalUserId": "demo-user-1",
              "message": "I am replying on Zhiguang. Explain Redis cache-aside simply.",
              "goal": "write a Zhiguang reply about Redis cache-aside"
            }
            """))
    .andExpect(status().isOk())
    .andExpect(jsonPath("$.answer").exists())
    .andExpect(jsonPath("$.traceId").exists())
    .andExpect(jsonPath("$.usedContexts.resources[0].traceNodeId").exists())
    .andExpect(jsonPath("$.usedContexts.memories[1].channel").value("task_experience"));
```

- [ ] **Step 2: Run test to verify it fails**

Run: `mvn -f services/gateway-java/pom.xml -Dtest=SessionControllerTest,ResourceControllerTest test`
Expected: FAIL with missing controllers or proxy client

- [ ] **Step 3: Implement real proxy client and contracts**

```java
UUID userId = identityService.resolveInternalUserId(provider, externalUserId);
Map<String, Object> payload = engineClient.query(sessionId, userId, message, goal);
```

```json
{
  "required": ["answer", "traceId", "usedContexts", "compressionSummary"],
  "properties": {
    "usedContexts": {
      "required": ["resources", "memories", "sessionSummary"]
    }
  }
}
```

Requirements:

- `EngineClient` must use HTTP to call the engine, not return hard-coded payloads
- `POST /api/v1/resources/import` must accept a JSON body such as `{ "provider": "demo_local", "resourceDir": "data/demo-resources" }`
- `GET /api/v1/traces/{traceId}` must exist in both controller and OpenAPI contract
- response schemas must explicitly model `traceNodeId`, `nodePath`, `drilldownTrail`, `channel`, and `type`

- [ ] **Step 4: Run test to verify it passes**

Run: `mvn -f services/gateway-java/pom.xml -Dtest=SessionControllerTest,ResourceControllerTest test`
Expected: PASS with `Failures: 0`

- [ ] **Step 5: Commit**

```bash
git add services/gateway-java packages/contracts
git commit -m "feat: add gateway proxy APIs and contracts"
```

### Task 8: Build the Demo Chat and Dynamic Trace Panel

**Files:**
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\package.json`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\.env.local.example`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\next.config.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\tsconfig.json`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\vitest.config.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\app\page.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\app\api\chat\route.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\components\chat-shell.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\components\trace-panel.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\lib\gateway-client.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\src\lib\gateway-client.test.ts`

- [ ] **Step 1: Write the failing client test**

```ts
import { describe, expect, it } from "vitest";
import { buildGatewayUrl, normalizeQueryResponse } from "../../lib/gateway-client";

describe("gateway-client", () => {
  it("normalizes trace metadata from the gateway envelope", () => {
    const normalized = normalizeQueryResponse({
      answer: "Zhiguang reply draft",
      traceId: "trace-demo-001",
      usedContexts: {
        resources: [{
          nodeId: "node-l2",
          traceNodeId: "trace-node-l2",
          nodePath: "resource://zhiguang-java-cache-playbook/l2/redis/000",
          drilldownTrail: [],
        }],
        memories: [
          { channel: "user", type: "explanation_preference" },
          { channel: "task_experience", type: "successful_resource" },
        ],
        sessionSummary: "Goal=reply on Zhiguang",
      },
      compressionSummary: { before: 12, after: 8 },
    });

    expect(normalized.resources[0].traceNodeId).toBe("trace-node-l2");
    expect(normalized.memories[1].channel).toBe("task_experience");
  });

  it("builds the gateway base url from env", () => {
    expect(buildGatewayUrl("http://gateway-java:8080")).toBe("http://gateway-java:8080");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix apps/demo-chat test -- src/lib/gateway-client.test.ts`
Expected: FAIL with missing package or missing module

- [ ] **Step 3: Implement the thin AI SDK demo**

```ts
const gatewayBaseUrl =
  process.env.GATEWAY_BASE_URL ??
  process.env.NEXT_PUBLIC_GATEWAY_BASE_URL ??
  "http://localhost:8080";
```

```tsx
const { messages, ...chat } = useChat({
  api: "/api/chat",
  onFinish({ message }) {
    const trace = message.annotations?.at(-1);
    if (trace) setLastTrace(normalizeTraceAnnotation(trace));
  },
});
```

Requirements:

- `app/api/chat/route.ts` must call the gateway through env-driven base URLs, not hard-coded service names only
- `TracePanel` must render live trace data returned by the route, not static fixture data in `page.tsx`
- the UI should remain thin and agent-compatible, not absorb retrieval or memory logic

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix apps/demo-chat install`
Expected: dependencies install successfully

Run: `npm --prefix apps/demo-chat test -- src/lib/gateway-client.test.ts`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/demo-chat
git commit -m "feat: add dynamic demo chat trace ui"
```

### Task 9: Add Docker Compose, Demo Seed, and End-to-End Verification

**Files:**
- Create: `D:\code\KnowledgeContextEngine\.env.example`
- Create: `D:\code\KnowledgeContextEngine\docker-compose.yml`
- Create: `D:\code\KnowledgeContextEngine\scripts\seed_demo_data.py`
- Create: `D:\code\KnowledgeContextEngine\scripts\wait_for_http.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\.env.local.example`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_demo_story_e2e.py`

- [ ] **Step 1: Write the failing end-to-end story test**

```python
import httpx


def test_demo_story_returns_personalized_traceable_answer() -> None:
    response = httpx.post(
        "http://localhost:8080/api/v1/sessions/demo-session/query",
        headers={"X-API-Key": "demo-key"},
        json={
            "provider": "demo_local",
            "externalUserId": "demo-user-1",
            "message": "I am replying on Zhiguang. How should I explain Redis cache-aside briefly?",
            "goal": "write a Zhiguang reply about Redis cache-aside",
        },
        timeout=10,
    )

    payload = response.json()

    assert response.status_code == 200
    assert "Zhiguang" in payload["answer"]
    assert payload["usedContexts"]["resources"][0]["drilldownTrail"][1].endswith("/l1/redis")
    assert payload["usedContexts"]["memories"][1]["channel"] == "task_experience"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_demo_story_e2e.py -v`
Expected: FAIL with `ConnectError` because services are not running yet

- [ ] **Step 3: Implement compose, Dockerfiles, and seed flow**

```env
POSTGRES_DB=kce
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DEMO_API_KEY=demo-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=replace-me
OPENAI_CHAT_MODEL=qwen-plus
OPENAI_EMBEDDING_MODEL=text-embedding-v3
```

```yaml
demo-bootstrap:
  build: ./services/engine-python
  env_file: .env
  depends_on:
    gateway-java:
      condition: service_started
  command: ["python", "/workspace/scripts/seed_demo_data.py"]
```

Requirements:

- runtime containers must read `.env`, while `.env.example` remains the committed template
- no service code may hard-code localhost DSNs or internal base URLs
- `seed_demo_data.py` must seed:
  - demo resource files for the current Zhiguang-shaped article and related note
  - demo identity binding for `demo-user-1`
  - at least one `user` memory row
  - at least one `task_experience` memory row
  - at least one prior trace snapshot fixture
- `demo-chat` must wait for `demo-bootstrap` to finish successfully

- [ ] **Step 4: Run end-to-end verification**

Run: `Copy-Item .env.example .env`
Expected: local runtime env file created

Run: `docker compose up -d --build`
Expected: `postgres`, `redis`, `engine-python`, `gateway-java`, and `demo-chat` start successfully; `demo-bootstrap` exits with success

Run: `python -m pytest services/engine-python/tests/test_demo_story_e2e.py -v`
Expected: PASS with `1 passed`

Run: `python -m pytest services/engine-python/tests -v --cov=app.services --cov-fail-under=90`
Expected: PASS with core business service coverage at or above 90%

- [ ] **Step 5: Commit**

```bash
git add .env.example docker-compose.yml scripts/seed_demo_data.py scripts/wait_for_http.py services/engine-python/Dockerfile services/gateway-java/Dockerfile apps/demo-chat/Dockerfile apps/demo-chat/.env.local.example services/engine-python/tests/test_demo_story_e2e.py
git commit -m "feat: add dockerized demo story"
```

## Self-Review

### Spec coverage

- `Resource / Session / Memory` layers are covered by Tasks 2 through 5.
- `node_path`, `stable_key`, resource tree, and drill-down trace are covered by Tasks 3, 5, 7, and 9.
- dual-channel memory is covered by Task 4.
- Java gateway and real proxy boundaries are covered by Tasks 6 and 7.
- the dynamic Zhiguang-shaped demo chat is covered by Task 8.
- Docker Compose, bootstrap seed flow, integration testing, and coverage gate are covered by Task 9.

### Placeholder scan

- No `TODO`, `TBD`, or "implement later" placeholders remain.
- Each task includes explicit files, verification commands, and commit messages.
- The plan no longer relies on hard-coded gateway or engine stub responses.

### Type consistency

- `MemoryChannel.TASK_EXPERIENCE` and `memory_type` enum values remain consistent across schema, services, and response payloads.
- `node_path`, `stable_key`, `traceNodeId`, `drilldownTrail`, and `compressionSummary` stay consistent across engine, gateway, and demo-chat tasks.
- Public gateway contracts and internal engine routes now align for resource-tree, node, trace, and trace-node lookups.
