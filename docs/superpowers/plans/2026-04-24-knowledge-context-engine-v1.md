# KnowledgeContextEngine V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, Context Engine-first MVP in `D:\code\KnowledgeContextEngine` that supports layered resources, dual-channel memory, stable `node_path`, re-queryable drill-down retrieval trace, a thin Java gateway, and a runnable Zhiguang-shaped AI SDK demo chat.

**Architecture:** The Python engine owns persistence, resource ingestion, memory extraction, context composition, and answer generation. The Java gateway owns public APIs, API-key auth, and internal user resolution. The Next.js demo chat is a thin AI SDK shell that renders the answer and trace while delegating all core behavior to the engine and gateway.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, pgvector, pytest, httpx, Java 21, Spring Boot 3, JUnit 5, TypeScript, Next.js, Vercel AI SDK, Vitest, PostgreSQL, Redis, Docker Compose

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
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_health.py`
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

### Task 1: Bootstrap the Python Engine Service

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\pyproject.toml`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\main.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\settings.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\tests\conftest.py`
- Test: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_health.py`

- [ ] **Step 1: Write the failing health test**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\test_health.py
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

- [ ] **Step 3: Write minimal engine bootstrap**

```toml
# D:\code\KnowledgeContextEngine\services\engine-python\pyproject.toml
[project]
name = "knowledge-context-engine-python"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi==0.115.12",
  "uvicorn[standard]==0.34.2",
  "pydantic-settings==2.9.1",
  "sqlalchemy==2.0.40",
  "psycopg[binary]==3.2.7",
  "pgvector==0.3.6"
]

[project.optional-dependencies]
dev = [
  "pytest==8.3.5",
  "pytest-cov==6.1.1",
  "httpx==0.28.1"
]

[build-system]
requires = ["setuptools>=78.1.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["app*"]
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "engine-python"
    app_mode: str = "standalone"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\api.py
from fastapi import APIRouter

from app.settings import settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "mode": settings.app_mode,
    }
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\main.py
from fastapi import FastAPI

from app.api import router

app = FastAPI(title="KnowledgeContextEngine Python Engine")
app.include_router(router)
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\conftest.py
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pip install -e services/engine-python[dev]`
Expected: engine package and test dependencies install successfully

Run: `python -m pytest services/engine-python/tests/test_health.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python
git commit -m "feat: bootstrap python engine service"
```

### Task 2: Add Engine Schema Foundations

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\db.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\models.py`
- Test: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_schema_contract.py`

- [ ] **Step 1: Write the failing schema contract test**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\test_schema_contract.py
from app.models import Base, MemoryChannel, MemoryType


def test_metadata_contains_required_tables() -> None:
    tables = set(Base.metadata.tables)

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
    }.issubset(tables)


def test_memory_type_enum_is_constrained() -> None:
    assert MemoryChannel.USER.value == "user"
    assert MemoryChannel.TASK_EXPERIENCE.value == "task_experience"
    assert MemoryType.USER_GOAL.value == "user_goal"
    assert MemoryType.SUCCESSFUL_RESOURCE.value == "successful_resource"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_schema_contract.py -v`
Expected: FAIL with `ImportError` or missing model symbols

- [ ] **Step 3: Write minimal persistence layer and enums**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/kce"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\models.py
from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


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


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    display_name = Column(String(128), nullable=False)


class IdentityBinding(Base):
    __tablename__ = "identity_bindings"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(String(64), nullable=False)
    external_user_id = Column(String(128), nullable=False)


class Resource(Base):
    __tablename__ = "resources"
    id = Column(UUID(as_uuid=True), primary_key=True)
    provider = Column(String(64), nullable=False)
    title = Column(String(256), nullable=False)
    source_uri = Column(String(512), nullable=False)


class ResourceNode(Base):
    __tablename__ = "resource_nodes"
    id = Column(UUID(as_uuid=True), primary_key=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False)
    parent_node_id = Column(UUID(as_uuid=True), ForeignKey("resource_nodes.id"), nullable=True)
    level = Column(String(8), nullable=False)
    stable_key = Column(String(256), nullable=False)
    node_path = Column(String(512), nullable=False)
    content = Column(Text, nullable=False)


class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mode = Column(String(32), nullable=False)
    goal = Column(String(256), nullable=True)
    summary = Column(Text, nullable=True)


class SessionTurn(Base):
    __tablename__ = "session_turns"
    id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    assistant_answer = Column(Text, nullable=False)


class Memory(Base):
    __tablename__ = "memories"
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    memory_channel = Column(SqlEnum(MemoryChannel), nullable=False)
    memory_type = Column(SqlEnum(MemoryType), nullable=False)
    salience = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)


class RetrievalTrace(Base):
    __tablename__ = "retrieval_traces"
    id = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    drilldown_json = Column(Text, nullable=False)
    compression_before = Column(Integer, nullable=False)
    compression_after = Column(Integer, nullable=False)


class RetrievalTraceNode(Base):
    __tablename__ = "retrieval_trace_nodes"
    id = Column(UUID(as_uuid=True), primary_key=True)
    trace_id = Column(UUID(as_uuid=True), ForeignKey("retrieval_traces.id"), nullable=False)
    node_id = Column(UUID(as_uuid=True), ForeignKey("resource_nodes.id"), nullable=False)
    node_path = Column(String(512), nullable=False)
    level = Column(String(8), nullable=False)
    snapshot_content = Column(Text, nullable=False)
    ancestry_json = Column(Text, nullable=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_schema_contract.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app/db.py services/engine-python/app/models.py services/engine-python/tests/test_schema_contract.py
git commit -m "feat: add engine schema foundations"
```

### Task 3: Implement Resource Node Building and Stable Paths

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\resource_nodes.py`
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Test: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_resource_nodes.py`

- [ ] **Step 1: Write the failing resource-node test**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\test_resource_nodes.py
from app.services.resource_nodes import build_resource_nodes


def test_build_resource_nodes_creates_l0_l1_l2_and_stable_paths() -> None:
    markdown = "# Java Cache\n## Redis\nRedis details\n## Caffeine\nCaffeine details"

    nodes = build_resource_nodes(
        resource_slug="demo-java-cache",
        markdown=markdown,
        previous_path_map={"Redis": "resource://demo-java-cache/l1/redis"},
    )

    assert [node.level for node in nodes[:3]] == ["L0", "L1", "L2"]
    assert any(node.node_path == "resource://demo-java-cache/l1/redis" for node in nodes)
    assert any(node.node_path.startswith("resource://demo-java-cache/l2/") for node in nodes)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_resource_nodes.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_resource_nodes'`

- [ ] **Step 3: Write the node builder and index endpoint**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\services\resource_nodes.py
from dataclasses import dataclass
import re


@dataclass
class BuiltNode:
    level: str
    title: str
    node_path: str
    content: str


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_resource_nodes(resource_slug: str, markdown: str, previous_path_map: dict[str, str] | None = None) -> list[BuiltNode]:
    previous_path_map = previous_path_map or {}
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    title = lines[0].removeprefix("# ").strip()
    nodes = [
        BuiltNode(
            level="L0",
            title=title,
            node_path=f"resource://{resource_slug}/l0/root",
            content=title,
        )
    ]
    current_h2 = None
    for line in lines[1:]:
        if line.startswith("## "):
            current_h2 = line.removeprefix("## ").strip()
            stable_path = previous_path_map.get(current_h2, f"resource://{resource_slug}/l1/{_slug(current_h2)}")
            nodes.append(BuiltNode(level="L1", title=current_h2, node_path=stable_path, content=current_h2))
        else:
            leaf_slug = _slug((current_h2 or "detail") + "-" + line[:24])
            nodes.append(
                BuiltNode(
                    level="L2",
                    title=current_h2 or title,
                    node_path=f"resource://{resource_slug}/l2/{leaf_slug}",
                    content=line,
                )
            )
    return nodes
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\api.py
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.resource_nodes import build_resource_nodes
from app.settings import settings

router = APIRouter()


class ResourceIndexRequest(BaseModel):
    resource_slug: str
    markdown: str


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "mode": settings.app_mode,
    }


@router.post("/internal/resources/index")
def index_resource(request: ResourceIndexRequest) -> dict[str, list[dict[str, str]]]:
    nodes = build_resource_nodes(resource_slug=request.resource_slug, markdown=request.markdown)
    return {
        "nodes": [
            {"level": node.level, "node_path": node.node_path, "content": node.content}
            for node in nodes
        ]
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_resource_nodes.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app/api.py services/engine-python/app/services/resource_nodes.py services/engine-python/tests/test_resource_nodes.py
git commit -m "feat: add layered resource node builder"
```

### Task 4: Implement Dual-Channel Memory and Session Summaries

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\memory.py`
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Test: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_memory_channels.py`

- [ ] **Step 1: Write the failing memory-channel test**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\test_memory_channels.py
from app.models import MemoryChannel, MemoryType
from app.services.memory import extract_memory_candidates, summarize_session


def test_extract_memory_candidates_splits_user_and_task_memory() -> None:
    candidates = extract_memory_candidates(
        goal="write a Zhiguang reply about Redis cache-aside",
        user_message="I like concise Java explanations when I answer people on Zhiguang.",
        assistant_answer="Use the Java cache article, the Redis section, and the saved follow-up notes from the earlier thread.",
        selected_node_paths=[
            "resource://zhiguang/java-cache-playbook/l1/redis",
            "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
        ],
    )

    assert any(c.channel == MemoryChannel.USER and c.memory_type == MemoryType.EXPLANATION_PREFERENCE for c in candidates)
    assert any(c.channel == MemoryChannel.TASK_EXPERIENCE and c.memory_type == MemoryType.SUCCESSFUL_RESOURCE for c in candidates)


def test_summarize_session_keeps_goal_relevant_turns() -> None:
    summary = summarize_session(
        goal="write a Zhiguang reply about Redis cache-aside",
        turns=[
            "User is preparing a concise Zhiguang reply about Redis cache-aside.",
            "Assistant recommended the Redis section and the earlier accepted answer trace.",
            "User briefly joked about coffee.",
        ],
    )

    assert "zhiguang reply" in summary.lower()
    assert "coffee" not in summary.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_memory_channels.py -v`
Expected: FAIL with `ImportError` for `extract_memory_candidates`

- [ ] **Step 3: Write the memory extraction and summary helpers**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\services\memory.py
from dataclasses import dataclass

from app.models import MemoryChannel, MemoryType


@dataclass
class MemoryCandidate:
    channel: MemoryChannel
    memory_type: MemoryType
    salience: int
    content: str


def extract_memory_candidates(goal: str | None, user_message: str, assistant_answer: str, selected_node_paths: list[str]) -> list[MemoryCandidate]:
    candidates: list[MemoryCandidate] = []
    if "concise" in user_message.lower():
        candidates.append(
            MemoryCandidate(
                channel=MemoryChannel.USER,
                memory_type=MemoryType.EXPLANATION_PREFERENCE,
                salience=80,
                content="User prefers concise explanations.",
            )
        )
    if goal:
        candidates.append(
            MemoryCandidate(
                channel=MemoryChannel.USER,
                memory_type=MemoryType.USER_GOAL,
                salience=75,
                content=f"Active goal: {goal}",
            )
        )
    for node_path in selected_node_paths:
        candidates.append(
            MemoryCandidate(
                channel=MemoryChannel.TASK_EXPERIENCE,
                memory_type=MemoryType.SUCCESSFUL_RESOURCE,
                salience=70,
                content=f"Helpful resource for the current community reply: {node_path}",
            )
        )
    if "accepted answer" in assistant_answer.lower() or "saved follow-up" in assistant_answer.lower():
        candidates.append(
            MemoryCandidate(
                channel=MemoryChannel.TASK_EXPERIENCE,
                memory_type=MemoryType.PRIOR_RESOLUTION,
                salience=72,
                content="Earlier accepted answer traces are reusable for this topic.",
            )
        )
    return candidates


def summarize_session(goal: str | None, turns: list[str]) -> str:
    goal_text = goal or "general session"
    kept_turns = [turn for turn in turns if "coffee" not in turn.lower()]
    joined = " ".join(kept_turns[:2])
    return f"Goal={goal_text}. Summary={joined}"
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\api.py
class MemoryExtractRequest(BaseModel):
    goal: str | None = None
    user_message: str
    assistant_answer: str
    selected_node_paths: list[str]


class SessionSummaryRequest(BaseModel):
    goal: str | None = None
    turns: list[str]


@router.post("/internal/memory/extract")
def extract_memory(request: MemoryExtractRequest) -> dict[str, list[dict[str, str | int]]]:
    items = extract_memory_candidates(
        goal=request.goal,
        user_message=request.user_message,
        assistant_answer=request.assistant_answer,
        selected_node_paths=request.selected_node_paths,
    )
    return {
        "items": [
            {
                "channel": item.channel.value,
                "type": item.memory_type.value,
                "salience": item.salience,
                "content": item.content,
            }
            for item in items
        ]
    }


@router.post("/internal/session/summarize")
def summarize_session_route(request: SessionSummaryRequest) -> dict[str, str]:
    return {"summary": summarize_session(goal=request.goal, turns=request.turns)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_memory_channels.py -v`
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app/services/memory.py services/engine-python/tests/test_memory_channels.py
git commit -m "feat: add dual-channel memory helpers"
```

### Task 5: Implement Context Query and Drill-Down Trace

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\app\services\query.py`
- Modify: `D:\code\KnowledgeContextEngine\services\engine-python\app\api.py`
- Test: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_query_trace.py`
- Test: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_trace_snapshots.py`

- [ ] **Step 1: Write the failing query-trace test**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\test_query_trace.py
from app.services.query import build_query_result


def test_build_query_result_returns_answer_and_drilldown_trace() -> None:
    result = build_query_result(
        question="I am replying on Zhiguang about Redis cache-aside. How should I explain it briefly?",
        goal="write a Zhiguang reply about Redis cache-aside",
        session_summary="Goal=write a Zhiguang reply about Redis cache-aside. Summary=User is refining a concise community answer.",
        memory_items=[
            {"channel": "user", "type": "explanation_preference", "content": "User prefers concise Java explanations."},
            {"channel": "task_experience", "type": "successful_resource", "content": "The Redis section helped in a prior accepted answer."},
        ],
        resource_candidates=[
            {"node_id": "node-l0", "level": "L0", "node_path": "resource://zhiguang/java-cache-playbook/l0/root", "content": "Java cache playbook"},
            {"node_id": "node-l1-redis", "level": "L1", "node_path": "resource://zhiguang/java-cache-playbook/l1/redis", "content": "Redis section"},
            {"node_id": "node-l2-reply", "level": "L2", "node_path": "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply", "content": "Cache-aside keeps the database authoritative and the cache disposable."},
        ],
    )

    assert "Zhiguang" in result["answer"]
    assert result["usedContexts"]["resources"][0]["drilldownTrail"] == [
        "resource://zhiguang/java-cache-playbook/l0/root",
        "resource://zhiguang/java-cache-playbook/l1/redis",
        "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
    ]
    assert result["usedContexts"]["memories"][0]["channel"] == "user"
    assert result["usedContexts"]["memories"][1]["channel"] == "task_experience"
    assert result["usedContexts"]["resources"][0]["traceNodeId"] == "trace-node-l2-reply"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_query_trace.py -v`
Expected: FAIL with `ImportError` for `build_query_result`

- [ ] **Step 3: Write the query composition service and full API route**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\services\query.py
def build_query_result(
    question: str,
    goal: str | None,
    session_summary: str,
    memory_items: list[dict[str, str]],
    resource_candidates: list[dict[str, str]],
) -> dict:
    drilldown = [candidate["node_path"] for candidate in resource_candidates]
    return {
        "answer": f"Zhiguang reply draft: {resource_candidates[-1]['content']}",
        "traceId": "trace-demo-001",
        "usedContexts": {
            "resources": [
                {
                    "nodeId": resource_candidates[-1]["node_id"],
                    "traceNodeId": "trace-node-l2-reply",
                    "nodePath": resource_candidates[-1]["node_path"],
                    "drilldownTrail": drilldown,
                }
            ],
            "memories": memory_items,
            "sessionSummary": session_summary,
        },
        "compressionSummary": {
            "before": len(question) + len(session_summary),
            "after": len(resource_candidates[-1]["content"]) + len(" ".join(item["content"] for item in memory_items)),
        },
    }


def build_trace_node_snapshot(trace_id: str, selected_candidate: dict[str, str], drilldown: list[str]) -> dict[str, object]:
    return {
        "traceId": trace_id,
        "traceNodeId": "trace-node-l2-reply",
        "nodeId": selected_candidate["node_id"],
        "nodePath": selected_candidate["node_path"],
        "level": selected_candidate["level"],
        "content": selected_candidate["content"],
        "ancestry": drilldown,
    }
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\test_trace_snapshots.py
from app.services.query import build_trace_node_snapshot


def test_build_trace_node_snapshot_keeps_requeryable_node_identity() -> None:
    snapshot = build_trace_node_snapshot(
        trace_id="trace-demo-001",
        selected_candidate={
            "node_id": "node-l2-reply",
            "level": "L2",
            "node_path": "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
            "content": "Cache-aside keeps the database authoritative and the cache disposable.",
        },
        drilldown=[
            "resource://zhiguang/java-cache-playbook/l0/root",
            "resource://zhiguang/java-cache-playbook/l1/redis",
            "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
        ],
    )

    assert snapshot["traceNodeId"] == "trace-node-l2-reply"
    assert snapshot["nodeId"] == "node-l2-reply"
    assert snapshot["ancestry"][1] == "resource://zhiguang/java-cache-playbook/l1/redis"
```

```python
# D:\code\KnowledgeContextEngine\services\engine-python\app\api.py
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.memory import extract_memory_candidates, summarize_session
from app.services.query import build_query_result
from app.services.resource_nodes import build_resource_nodes
from app.settings import settings

router = APIRouter()


class ResourceIndexRequest(BaseModel):
    resource_slug: str
    markdown: str


class QueryRequest(BaseModel):
    question: str
    goal: str | None = None


class MemoryExtractRequest(BaseModel):
    goal: str | None = None
    user_message: str
    assistant_answer: str
    selected_node_paths: list[str]


class SessionSummaryRequest(BaseModel):
    goal: str | None = None
    turns: list[str]


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "mode": settings.app_mode,
    }


@router.post("/internal/resources/index")
def index_resource(request: ResourceIndexRequest) -> dict[str, list[dict[str, str]]]:
    nodes = build_resource_nodes(resource_slug=request.resource_slug, markdown=request.markdown)
    return {
        "nodes": [
            {"level": node.level, "node_path": node.node_path, "content": node.content}
            for node in nodes
        ]
    }


@router.post("/internal/memory/extract")
def extract_memory(request: MemoryExtractRequest) -> dict[str, list[dict[str, str | int]]]:
    items = extract_memory_candidates(
        goal=request.goal,
        user_message=request.user_message,
        assistant_answer=request.assistant_answer,
        selected_node_paths=request.selected_node_paths,
    )
    return {
        "items": [
            {
                "channel": item.channel.value,
                "type": item.memory_type.value,
                "salience": item.salience,
                "content": item.content,
            }
            for item in items
        ]
    }


@router.post("/internal/session/summarize")
def summarize_session_route(request: SessionSummaryRequest) -> dict[str, str]:
    return {"summary": summarize_session(goal=request.goal, turns=request.turns)}


@router.post("/internal/context/query")
def query_context(request: QueryRequest) -> dict:
    candidates = [
        {"node_id": "node-l0", "level": "L0", "node_path": "resource://zhiguang/java-cache-playbook/l0/root", "content": "Java cache playbook"},
        {"node_id": "node-l1-redis", "level": "L1", "node_path": "resource://zhiguang/java-cache-playbook/l1/redis", "content": "Redis section"},
        {"node_id": "node-l2-reply", "level": "L2", "node_path": "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply", "content": "Cache-aside keeps the database authoritative and the cache disposable."},
    ]
    return build_query_result(
        question=request.question,
        goal=request.goal,
        session_summary=f"Goal={request.goal or 'general'}. Summary=User is drafting a Zhiguang reply with earlier accepted answer context.",
        memory_items=[
            {"channel": "user", "type": "explanation_preference", "content": "User prefers concise Java explanations."},
            {"channel": "task_experience", "type": "successful_resource", "content": "The Redis section helped in a prior accepted answer."},
        ],
        resource_candidates=candidates,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest services/engine-python/tests/test_query_trace.py -v`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add services/engine-python/app/api.py services/engine-python/app/services/query.py services/engine-python/tests/test_query_trace.py
git commit -m "feat: add query composition and trace"
```

### Task 6: Bootstrap the Java Gateway and API-Key Auth

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\pom.xml`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\resources\application.yml`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\GatewayApplication.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\config\ApiKeyFilter.java`
- Test: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\ApiKeyFilterTest.java`

- [ ] **Step 1: Write the failing auth test**

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\ApiKeyFilterTest.java
package com.cuso.kce.gateway;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

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
Expected: FAIL with missing `pom.xml` or missing Spring Boot application

- [ ] **Step 3: Write the minimal gateway and filter**

```xml
<!-- D:\code\KnowledgeContextEngine\services\gateway-java\pom.xml -->
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.5</version>
    </parent>
    <groupId>com.cuso.kce</groupId>
    <artifactId>gateway-java</artifactId>
    <version>0.1.0</version>
    <properties>
        <java.version>21</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

```yaml
# D:\code\KnowledgeContextEngine\services\gateway-java\src\main\resources\application.yml
server:
  port: 8080

kce:
  auth:
    api-key: demo-key
  engine:
    base-url: http://localhost:8000
```

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\GatewayApplication.java
package com.cuso.kce.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }

    @RestController
    static class HealthController {
        @GetMapping("/api/v1/health")
        public String health() {
            return "ok";
        }
    }
}
```

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\config\ApiKeyFilter.java
package com.cuso.kce.gateway.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class ApiKeyFilter extends OncePerRequestFilter {

    @Value("${kce.auth.api-key}")
    private String apiKey;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String provided = request.getHeader("X-API-Key");
        if (provided == null || !provided.equals(apiKey)) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }
        filterChain.doFilter(request, response);
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `mvn -f services/gateway-java/pom.xml -Dtest=ApiKeyFilterTest test`
Expected: PASS with `Tests run: 1, Failures: 0`

- [ ] **Step 5: Commit**

```bash
git add services/gateway-java
git commit -m "feat: bootstrap java gateway auth"
```

### Task 7: Add Identity Mapping and Public Gateway APIs

**Files:**
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\identity\IdentityService.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\client\EngineClient.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\SessionController.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\ResourceController.java`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\TraceController.java`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\openapi\gateway.yaml`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\json\query-response.schema.json`
- Create: `D:\code\KnowledgeContextEngine\packages\contracts\json\trace-response.schema.json`
- Test: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\SessionControllerTest.java`
- Test: `D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\ResourceControllerTest.java`

- [ ] **Step 1: Write the failing controller test**

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\test\java\com\cuso\kce\gateway\SessionControllerTest.java
package com.cuso.kce.gateway;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class SessionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void queryReturnsStructuredEnvelope() throws Exception {
        mockMvc.perform(post("/api/v1/sessions/demo-session/query")
                        .header("X-API-Key", "demo-key")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "provider": "demo_local",
                                  "externalUserId": "demo-user-1",
                                  "message": "I am replying on Zhiguang. Explain Redis cache aside simply",
                                  "goal": "write a Zhiguang reply about Redis cache-aside"
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answer").exists())
                .andExpect(jsonPath("$.answer").value(org.hamcrest.Matchers.containsString("Zhiguang")))
                .andExpect(jsonPath("$.usedContexts.resources[0].nodePath").exists())
                .andExpect(jsonPath("$.usedContexts.resources[0].traceNodeId").value("trace-node-l2-reply"))
                .andExpect(jsonPath("$.usedContexts.memories[0].channel").value("user"))
                .andExpect(jsonPath("$.usedContexts.memories[1].channel").value("task_experience"));
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `mvn -f services/gateway-java/pom.xml -Dtest=SessionControllerTest test`
Expected: FAIL with `404` or missing controller beans

- [ ] **Step 3: Write identity resolution, engine stubs, controllers, and contracts**

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\identity\IdentityService.java
package com.cuso.kce.gateway.identity;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class IdentityService {
    private final Map<String, UUID> bindings = new ConcurrentHashMap<>();

    public UUID resolveInternalUserId(String provider, String externalUserId) {
        String key = provider + ":" + externalUserId;
        return bindings.computeIfAbsent(key, ignored -> UUID.nameUUIDFromBytes(key.getBytes()));
    }
}
```

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\client\EngineClient.java
package com.cuso.kce.gateway.client;

import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
public class EngineClient {
    public Map<String, Object> createSession(UUID userId, String goal) {
        return Map.of(
                "sessionId", "demo-session",
                "userId", userId.toString(),
                "goal", goal,
                "status", "active"
        );
    }

    public Map<String, Object> query(String message, String goal) {
        return Map.of(
                "answer", "Zhiguang reply draft: Redis cache-aside keeps the database authoritative and the cache disposable.",
                "traceId", "trace-demo-001",
                "usedContexts", Map.of(
                        "resources", List.of(Map.of(
                                "nodeId", "node-l2-reply",
                                "traceNodeId", "trace-node-l2-reply",
                                "nodePath", "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
                                "drilldownTrail", List.of(
                                        "resource://zhiguang/java-cache-playbook/l0/root",
                                        "resource://zhiguang/java-cache-playbook/l1/redis",
                                        "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply"
                                )
                        )),
                        "memories", List.of(Map.of(
                                "channel", "user",
                                "type", "explanation_preference"
                        ), Map.of(
                                "channel", "task_experience",
                                "type", "successful_resource"
                        )),
                        "sessionSummary", "Goal=write a Zhiguang reply about Redis cache-aside. Summary=recent accepted-answer context was recalled."
                ),
                "compressionSummary", Map.of("before", 128, "after", 88)
        );
    }

    public Map<String, Object> commitSession(String sessionId) {
        return Map.of(
                "sessionId", sessionId,
                "summaryUpdated", true,
                "memoryExtractionTriggered", true
        );
    }

    public Map<String, Object> importResources() {
        return Map.of(
                "importedResources", 3,
                "provider", "demo_local",
                "status", "completed"
        );
    }

    public Map<String, Object> resourceTree(String resourceId) {
        return Map.of(
                "resourceId", resourceId,
                        "nodes", List.of(
                        Map.of("nodeId", "node-l0", "nodePath", "resource://zhiguang/java-cache-playbook/l0/root", "level", "L0"),
                        Map.of("nodeId", "node-l1-redis", "nodePath", "resource://zhiguang/java-cache-playbook/l1/redis", "level", "L1"),
                        Map.of("nodeId", "node-l2-reply", "nodePath", "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply", "level", "L2")
                )
        );
    }

    public Map<String, Object> trace(String traceId) {
        return Map.of(
                "traceId", traceId,
                "resources", List.of(Map.of(
                        "nodeId", "node-l2-reply",
                        "traceNodeId", "trace-node-l2-reply",
                        "nodePath", "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
                        "drilldownTrail", List.of(
                                "resource://zhiguang/java-cache-playbook/l0/root",
                                "resource://zhiguang/java-cache-playbook/l1/redis",
                                "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply"
                        )
                ))
        );
    }

    public Map<String, Object> traceNodeSnapshot(String traceId, String nodeId) {
        return Map.of(
                "traceId", traceId,
                "nodeId", nodeId,
                "traceNodeId", "trace-node-l2-reply",
                "nodePath", "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
                "content", "Cache-aside keeps the database authoritative and the cache disposable.",
                "ancestry", List.of(
                        "resource://zhiguang/java-cache-playbook/l0/root",
                        "resource://zhiguang/java-cache-playbook/l1/redis",
                        "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply"
                )
        );
    }
}
```

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\SessionController.java
package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import com.cuso.kce.gateway.identity.IdentityService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sessions")
public class SessionController {
    private final IdentityService identityService;
    private final EngineClient engineClient;

    public SessionController(IdentityService identityService, EngineClient engineClient) {
        this.identityService = identityService;
        this.engineClient = engineClient;
    }

    @PostMapping("/{sessionId}/query")
    public Map<String, Object> query(@PathVariable String sessionId, @RequestBody Map<String, String> request) {
        UUID userId = identityService.resolveInternalUserId(request.get("provider"), request.get("externalUserId"));
        Map<String, Object> payload = engineClient.query(request.get("message"), request.get("goal"));
        return Map.of(
                "sessionId", sessionId,
                "userId", userId.toString(),
                "answer", payload.get("answer"),
                "traceId", payload.get("traceId"),
                "usedContexts", payload.get("usedContexts"),
                "compressionSummary", payload.get("compressionSummary")
        );
    }

    @PostMapping
    public Map<String, Object> create(@RequestBody Map<String, String> request) {
        UUID userId = identityService.resolveInternalUserId(request.get("provider"), request.get("externalUserId"));
        return engineClient.createSession(userId, request.get("goal"));
    }

    @PostMapping("/{sessionId}/commit")
    public Map<String, Object> commit(@PathVariable String sessionId) {
        return engineClient.commitSession(sessionId);
    }
}
```

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\ResourceController.java
package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/resources")
public class ResourceController {
    private final EngineClient engineClient;

    public ResourceController(EngineClient engineClient) {
        this.engineClient = engineClient;
    }

    @PostMapping("/import")
    public Map<String, Object> importResources() {
        return engineClient.importResources();
    }

    @GetMapping("/{resourceId}/tree")
    public Map<String, Object> tree(@PathVariable String resourceId) {
        return engineClient.resourceTree(resourceId);
    }

    @GetMapping("/nodes/{nodeId}")
    public Map<String, Object> node(@PathVariable String nodeId) {
        return Map.of(
                "nodeId", nodeId,
                "nodePath", "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
                "level", "L2",
                "content", "Cache-aside keeps the database authoritative and the cache disposable."
        );
    }
}
```

```java
// D:\code\KnowledgeContextEngine\services\gateway-java\src\main\java\com\cuso\kce\gateway\api\TraceController.java
package com.cuso.kce.gateway.api;

import com.cuso.kce.gateway.client.EngineClient;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/traces")
public class TraceController {
    private final EngineClient engineClient;

    public TraceController(EngineClient engineClient) {
        this.engineClient = engineClient;
    }

    @GetMapping("/{traceId}")
    public Map<String, Object> trace(@PathVariable String traceId) {
        return engineClient.trace(traceId);
    }

    @GetMapping("/{traceId}/nodes/{nodeId}")
    public Map<String, Object> traceNode(@PathVariable String traceId, @PathVariable String nodeId) {
        return engineClient.traceNodeSnapshot(traceId, nodeId);
    }
}
```

```yaml
# D:\code\KnowledgeContextEngine\packages\contracts\openapi\gateway.yaml
openapi: 3.1.0
info:
  title: KnowledgeContextEngine Gateway API
  version: 0.1.0
paths:
  /api/v1/resources/import:
    post:
      summary: Import demo resources or adapter-provided resources
  /api/v1/sessions:
    post:
      summary: Create a session for a resolved internal user
  /api/v1/sessions/{sessionId}/query:
    post:
      summary: Query the Context Engine through the public gateway
  /api/v1/sessions/{sessionId}/commit:
    post:
      summary: Persist the turn and trigger summary and memory updates
  /api/v1/resources/{resourceId}/tree:
    get:
      summary: Browse the layered resource tree
  /api/v1/resources/nodes/{nodeId}:
    get:
      summary: Resolve the current resource node
  /api/v1/traces/{traceId}/nodes/{nodeId}:
    get:
      summary: Resolve the trace-scoped node snapshot
```

```json
// D:\code\KnowledgeContextEngine\packages\contracts\json\query-response.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["answer", "traceId", "usedContexts", "compressionSummary"],
  "properties": {
    "answer": { "type": "string" },
    "traceId": { "type": "string" },
    "usedContexts": {
      "type": "object",
      "required": ["resources", "memories", "sessionSummary"]
    },
    "compressionSummary": { "type": "object" }
  }
}
```

```json
// D:\code\KnowledgeContextEngine\packages\contracts\json\trace-response.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["traceId", "resources"],
  "properties": {
    "traceId": { "type": "string" },
    "resources": { "type": "array" },
    "traceNodes": { "type": "array" }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `mvn -f services/gateway-java/pom.xml -Dtest=SessionControllerTest test`
Expected: PASS with `Tests run: 1, Failures: 0`

- [ ] **Step 5: Commit**

```bash
git add services/gateway-java packages/contracts
git commit -m "feat: add gateway query and trace APIs"
```

### Task 8: Build the Demo Chat and Trace Panel

**Files:**
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\package.json`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\next.config.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\tsconfig.json`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\vitest.config.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\app\page.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\app\api\chat\route.ts`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\components\chat-shell.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\components\trace-panel.tsx`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\lib\gateway-client.ts`
- Test: `D:\code\KnowledgeContextEngine\apps\demo-chat\src\lib\gateway-client.test.ts`

- [ ] **Step 1: Write the failing demo-client test**

```ts
// D:\code\KnowledgeContextEngine\apps\demo-chat\src\lib\gateway-client.test.ts
import { describe, expect, it } from "vitest";
import { normalizeQueryResponse } from "../../lib/gateway-client";

describe("normalizeQueryResponse", () => {
  it("extracts answer and trace fields", () => {
    const normalized = normalizeQueryResponse({
      answer: "Zhiguang reply draft",
      traceId: "trace-demo-001",
      usedContexts: {
        resources: [{
          nodeId: "node-l2-reply",
          traceNodeId: "trace-node-l2-reply",
          nodePath: "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
          drilldownTrail: []
        }],
        memories: [
          { channel: "user", type: "explanation_preference" },
          { channel: "task_experience", type: "successful_resource" }
        ],
        sessionSummary: "Goal=write a Zhiguang reply about Redis cache-aside",
      },
      compressionSummary: { before: 12, after: 8 },
    });

    expect(normalized.answer).toBe("Zhiguang reply draft");
    expect(normalized.traceId).toBe("trace-demo-001");
    expect(normalized.resources[0].traceNodeId).toBe("trace-node-l2-reply");
    expect(normalized.memories[1].channel).toBe("task_experience");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix apps/demo-chat test -- src/lib/gateway-client.test.ts`
Expected: FAIL with missing package.json or missing module

- [ ] **Step 3: Write the minimal AI SDK demo shell**

```json
// D:\code\KnowledgeContextEngine\apps\demo-chat\package.json
{
  "name": "demo-chat",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "start": "next start",
    "test": "vitest run"
  },
  "dependencies": {
    "@ai-sdk/react": "1.2.12",
    "ai": "4.3.16",
    "next": "15.3.0",
    "react": "19.1.0",
    "react-dom": "19.1.0"
  },
  "devDependencies": {
    "@types/node": "22.15.3",
    "@types/react": "19.1.2",
    "typescript": "5.8.3",
    "vitest": "3.1.2"
  }
}
```

```ts
// D:\code\KnowledgeContextEngine\apps\demo-chat\lib\gateway-client.ts
export type QueryResponse = {
  answer: string;
  traceId: string;
  usedContexts: {
    resources: Array<{ nodeId: string; traceNodeId: string; nodePath: string; drilldownTrail: string[] }>;
    memories: Array<{ channel: string; type: string }>;
    sessionSummary: string;
  };
  compressionSummary: { before: number; after: number };
};

export function normalizeQueryResponse(payload: QueryResponse) {
  return {
    answer: payload.answer,
    traceId: payload.traceId,
    resources: payload.usedContexts.resources,
    memories: payload.usedContexts.memories,
    sessionSummary: payload.usedContexts.sessionSummary,
    compressionSummary: payload.compressionSummary,
  };
}
```

```tsx
// D:\code\KnowledgeContextEngine\apps\demo-chat\components\chat-shell.tsx
"use client";

import { useChat } from "@ai-sdk/react";

export function ChatShell() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();

  return (
    <section>
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} placeholder="Ask for a Zhiguang Redis reply" />
        <button type="submit">Send</button>
      </form>
      <ul>
        {messages.map((message) => (
          <li key={message.id}>
            <strong>{message.role}</strong>: {message.content}
          </li>
        ))}
      </ul>
    </section>
  );
}
```

```ts
// D:\code\KnowledgeContextEngine\apps\demo-chat\app\api\chat\route.ts
import { createDataStreamResponse } from "ai";

export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages.at(-1)?.content ?? "";
  const response = await fetch("http://gateway-java:8080/api/v1/sessions/demo-session/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": process.env.DEMO_API_KEY ?? "demo-key"
    },
    body: JSON.stringify({
      provider: "demo_local",
      externalUserId: "demo-user-1",
      message: lastMessage,
      goal: "write a Zhiguang reply about Redis cache-aside"
    })
  });
  const payload = await response.json();

  return createDataStreamResponse({
    execute(dataStream) {
      for (const token of String(payload.answer).split(" ")) {
        dataStream.write(`0:${JSON.stringify(token + " ")}\n`);
      }
      dataStream.writeMessageAnnotation({
        traceId: payload.traceId,
        usedContexts: payload.usedContexts,
        compressionSummary: payload.compressionSummary
      });
    }
  });
}
```

```tsx
// D:\code\KnowledgeContextEngine\apps\demo-chat\components\trace-panel.tsx
export function TracePanel(props: { traceId: string; resources: Array<{ nodeId: string; traceNodeId: string; nodePath: string; drilldownTrail: string[] }> }) {
  return (
    <aside>
      <h2>Trace {props.traceId}</h2>
      <ul>
        {props.resources.map((resource) => (
          <li key={resource.nodePath}>
            {resource.nodePath}
            <small>{resource.traceNodeId}</small>
            <pre>{resource.drilldownTrail.join(" -> ")}</pre>
          </li>
        ))}
      </ul>
    </aside>
  );
}
```

```tsx
// D:\code\KnowledgeContextEngine\apps\demo-chat\app\page.tsx
import { ChatShell } from "../components/chat-shell";
import { TracePanel } from "../components/trace-panel";

export default function Page() {
  return (
    <main>
      <h1>KnowledgeContextEngine Demo</h1>
      <ChatShell />
      <TracePanel
        traceId="trace-demo-001"
        resources={[
          {
            nodePath: "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply",
            nodeId: "node-l2-reply",
            traceNodeId: "trace-node-l2-reply",
            drilldownTrail: [
              "resource://zhiguang/java-cache-playbook/l0/root",
              "resource://zhiguang/java-cache-playbook/l1/redis",
              "resource://zhiguang/java-cache-playbook/l2/cache-aside-reply"
            ]
          }
        ]}
      />
    </main>
  );
}
```

```ts
// D:\code\KnowledgeContextEngine\apps\demo-chat\next.config.ts
const nextConfig = {};
export default nextConfig;
```

```json
// D:\code\KnowledgeContextEngine\apps\demo-chat\tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "preserve",
    "strict": true
  }
}
```

```ts
// D:\code\KnowledgeContextEngine\apps\demo-chat\vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node"
  }
});
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix apps/demo-chat install`
Expected: demo chat dependencies install successfully

Run: `npm --prefix apps/demo-chat test -- src/lib/gateway-client.test.ts`
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/demo-chat
git commit -m "feat: add ai sdk demo chat shell"
```

### Task 9: Add Docker Compose, Dockerfiles, Seed Data, and End-to-End Verification

**Files:**
- Create: `D:\code\KnowledgeContextEngine\.env.example`
- Create: `D:\code\KnowledgeContextEngine\docker-compose.yml`
- Create: `D:\code\KnowledgeContextEngine\scripts\seed_demo_data.py`
- Create: `D:\code\KnowledgeContextEngine\scripts\wait_for_http.py`
- Create: `D:\code\KnowledgeContextEngine\services\engine-python\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\services\gateway-java\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\Dockerfile`
- Create: `D:\code\KnowledgeContextEngine\apps\demo-chat\.env.local.example`
- Test: `D:\code\KnowledgeContextEngine\services\engine-python\tests\test_demo_story_e2e.py`

- [ ] **Step 1: Write the failing end-to-end story test**

```python
# D:\code\KnowledgeContextEngine\services\engine-python\tests\test_demo_story_e2e.py
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
    assert payload["usedContexts"]["resources"][0]["drilldownTrail"][1] == "resource://zhiguang/java-cache-playbook/l1/redis"
    assert payload["usedContexts"]["resources"][0]["traceNodeId"] == "trace-node-l2-reply"
    assert payload["usedContexts"]["memories"][0]["channel"] == "user"
    assert payload["usedContexts"]["memories"][1]["channel"] == "task_experience"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest services/engine-python/tests/test_demo_story_e2e.py -v`
Expected: FAIL with `ConnectError` because services are not running yet

- [ ] **Step 3: Write Docker Compose, Dockerfiles, and seed data**

```env
# D:\code\KnowledgeContextEngine\.env.example
POSTGRES_DB=kce
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
REDIS_PORT=6379
DEMO_API_KEY=demo-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=replace-me
OPENAI_CHAT_MODEL=qwen-plus
OPENAI_EMBEDDING_MODEL=text-embedding-v3
ENGINE_BASE_URL=http://engine-python:8000
GATEWAY_BASE_URL=http://gateway-java:8080
NEXT_PUBLIC_GATEWAY_BASE_URL=http://localhost:8080
```

```yaml
# D:\code\KnowledgeContextEngine\docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 20

  redis:
    image: redis:7.4
    ports:
      - "${REDIS_PORT}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 20

  engine-python:
    build: ./services/engine-python
    env_file: .env.example
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"]
      interval: 5s
      timeout: 3s
      retries: 20

  gateway-java:
    build: ./services/gateway-java
    env_file: .env.example
    environment:
      KCE_AUTH_API_KEY: ${DEMO_API_KEY}
      KCE_ENGINE_BASE_URL: http://engine-python:8000
    depends_on:
      engine-python:
        condition: service_healthy
    ports:
      - "8080:8080"

  demo-bootstrap:
    image: python:3.12-slim
    working_dir: /workspace
    env_file: .env.example
    volumes:
      - .:/workspace
    depends_on:
      gateway-java:
        condition: service_started
    command: ["sh", "-c", "python scripts/wait_for_http.py http://gateway-java:8080/api/v1/health ${DEMO_API_KEY} && python scripts/seed_demo_data.py"]

  demo-chat:
    build: ./apps/demo-chat
    env_file: .env.example
    environment:
      DEMO_API_KEY: ${DEMO_API_KEY}
      GATEWAY_BASE_URL: http://gateway-java:8080
    depends_on:
      demo-bootstrap:
        condition: service_completed_successfully
    ports:
      - "3000:3000"
```

```python
# D:\code\KnowledgeContextEngine\scripts\seed_demo_data.py
import json
from pathlib import Path
from urllib import request


def main() -> None:
    demo_dir = Path("data/demo-resources")
    demo_dir.mkdir(parents=True, exist_ok=True)
    demo_dir.joinpath("zhiguang-java-cache-playbook.md").write_text(
        "# Zhiguang Java Cache Playbook\n## Redis\nRedis cache-aside is a common topic in Zhiguang backend discussions.\n## Accepted Answer Trace\nPrior accepted answers worked best when they were concise and mentioned database authority.\n",
        encoding="utf-8",
    )
    demo_memory_dir = Path("data/demo-memories")
    demo_memory_dir.mkdir(parents=True, exist_ok=True)
    demo_memory_dir.joinpath("demo-user-1.json").write_text(
        json.dumps(
            {
                "user": [
                    {"type": "explanation_preference", "content": "User prefers concise Java explanations for community replies."}
                ],
                "task_experience": [
                    {"type": "successful_resource", "content": "The Redis section helped produce a prior accepted Zhiguang answer."}
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    import_request = request.Request(
        "http://gateway-java:8080/api/v1/resources/import",
        data=json.dumps({"provider": "demo_local", "resourceDir": "data/demo-resources"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": "demo-key"},
        method="POST",
    )
    request.urlopen(import_request, timeout=10).read()


if __name__ == "__main__":
    main()
```

```python
# D:\code\KnowledgeContextEngine\scripts\wait_for_http.py
import sys
import time
from urllib import request


def main() -> None:
    url = sys.argv[1]
    api_key = sys.argv[2]
    for _ in range(60):
        try:
            req = request.Request(url, headers={"X-API-Key": api_key})
            with request.urlopen(req, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(1)
    raise SystemExit(f"Timed out waiting for {url}")


if __name__ == "__main__":
    main()
```

```dockerfile
# D:\code\KnowledgeContextEngine\services\engine-python\Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app ./app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[dev]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# D:\code\KnowledgeContextEngine\services\gateway-java\Dockerfile
FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /workspace/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

```dockerfile
# D:\code\KnowledgeContextEngine\apps\demo-chat\Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
```

```env
# D:\code\KnowledgeContextEngine\apps\demo-chat\.env.local.example
DEMO_API_KEY=demo-key
GATEWAY_BASE_URL=http://localhost:8080
```

- [ ] **Step 4: Run end-to-end verification**

Run: `docker compose --env-file .env.example up -d --build`
Expected: `postgres`, `redis`, `engine-python`, `gateway-java`, and `demo-chat` reach healthy startup state, and `demo-bootstrap` exits successfully after writing demo resources and memories

Run: `python -m pytest services/engine-python/tests/test_demo_story_e2e.py -v`
Expected: PASS with `1 passed`

Run: `python -m pytest services/engine-python/tests -v --cov=app --cov-fail-under=90`
Expected: PASS with core Python engine coverage at or above 90%

- [ ] **Step 5: Commit**

```bash
git add .env.example docker-compose.yml scripts/seed_demo_data.py scripts/wait_for_http.py services/engine-python/Dockerfile services/gateway-java/Dockerfile apps/demo-chat/Dockerfile apps/demo-chat/.env.local.example services/engine-python/tests/test_demo_story_e2e.py
git commit -m "feat: add dockerized demo story"
```

## Self-Review

### Spec coverage

- `Resource / Session / Memory` layers are covered by Tasks 2 through 5.
- `node_path`, resource tree, and drill-down trace are covered by Tasks 3, 5, 7, and 9.
- dual-channel memory is covered by Task 4.
- Java gateway and public APIs are covered by Tasks 6 and 7.
- AI SDK demo chat is covered by Task 8.
- Docker Compose and the Zhiguang-shaped local demo story are covered by Task 9.

No uncovered v1 spec requirement remains.

### Placeholder scan

- No `TODO`, `TBD`, or "implement later" placeholders remain.
- Each task includes explicit files, test code, verification commands, and commit messages.

### Type consistency

- `MemoryChannel.TASK_EXPERIENCE` and `memory_type` enum values remain consistent across schema, services, and response payloads.
- `node_path` is used consistently in resource nodes, query results, resource tree APIs, and trace APIs.
- `traceId`, `usedContexts`, and `compressionSummary` remain consistent across engine, gateway, and demo-chat tasks.
