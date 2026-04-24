# KnowledgeContextEngine Design Spec

**Date:** 2026-04-24

**Repository:** `D:\code\KnowledgeContextEngine`

**Positioning:** A standalone, Context Engine-first project for knowledge-community scenarios. The project can run independently with local demo data, and it also reserves clean integration points for Zhiguang or other content platforms.

## 1. Original Goal

This project is not another agent-framework exercise.

Its primary goal is to demonstrate a reusable Context Engine that:

- abstracts context into `Resource / Session / Memory` layers
- supports layered retrieval, context fusion, and context compression
- supports lightweight personalized retrieval through long-term memory
- exposes addressable and drill-downable context surfaces so the system feels like a context system, not a flat chunk-RAG pipeline
- remains a complete runnable question-answering project
- can later integrate with Zhiguang without being reduced to a submodule of Zhiguang

The agent harness is intentionally thin. The core value is in the context system itself.

## 2. V1 Design Principles

- **Context Engine first:** the main technical highlight is context modeling and orchestration, not agent autonomy.
- **MVP only:** every highlight enters v1 in its minimum useful form.
- **Standalone first:** the project must remain useful without any external business backend.
- **Dual-mode support:** local demo mode must work end-to-end, while Zhiguang integration points remain explicit and clean.
- **Clear boundaries:** UI, gateway, engine, storage, and adapters must not bleed responsibilities into each other.
- **Traceable behavior:** retrieval and context composition must be observable.
- **Simple auth:** v1 prefers clear, lightweight boundaries over complex identity systems.
- **Visible context surface:** v1 must expose enough tree/path/drill-down behavior that the project is recognizable as a context system rather than a generic RAG service.
- **Core over shell:** retrieval, memory, compression, and trace quality take priority over UI polish or heavy platform packaging.

## 3. Core Concepts

### 3.1 Context Layers

The three context layers are **not** three storage tiers. They are three context sources.

- **Resource Context**
  - External knowledge sources such as articles, documents, favorites, imported resources, and search candidates.
  - Represents "what the system can look up".

- **Session Context**
  - Short-term conversational state such as recent turns, current goal, and rolling session summary.
  - Represents "what is happening in the current conversation".

- **Memory Context**
  - Long-term information accumulated across users and tasks, such as preferences, repeated interests, study focus, successful resource usage patterns, and reusable facts inferred from prior interaction.
  - Represents "what the system should remember across sessions".

### 3.2 Memory Channels

V1 memory must not be limited to user profile extraction.

V1 memory is split into two logical channels:

- **User Memory**
  - stable or semi-stable user information such as interests, learning goals, topic preferences, repeated follow-up patterns, and preferred explanations

- **Task / Experience Memory**
  - reusable information from prior sessions such as high-value resources, effective retrieval paths, frequently reused knowledge fragments, and patterns about which context combinations worked well

Both channels may live in the same physical table in v1, but they must remain distinguishable by schema and retrieval logic.

### 3.3 Resource Granularity Layers

`L0 / L1 / L2` describe **resource detail levels**, not business context types.

- **L0**
  - One-line summary or resource card used for coarse recall and fast resource selection.

- **L1**
  - Section-level or overview-level representation used for deciding whether to drill down.

- **L2**
  - Fine-grained chunks or original content snippets used for grounding the final answer.

The intended retrieval flow is:

1. coarse recall on `L0`
2. drill-down on related `L1`
3. final grounding on selected `L2`
4. fuse with `Session Context` and `Memory Context`

### 3.4 Context Addressability and Drill-Down

To preserve a recognizable "context system" identity, resources must be externally addressable in v1.

V1 does not need a full virtual filesystem interface, but it must expose at least:

- a stable `node_path` or equivalent address for each resource node
- a browsable resource tree for `L0 / L1 / L2`
- a drill-down trail in retrieval trace showing how the system moved from coarse resource selection to final grounding

This means the system should be able to explain a query in terms of:

1. which `L0` resource cards were considered
2. which `L1` sections or overviews were drilled into
3. which `L2` chunks were finally used

This visible path is one of the main distinctions between this project and ordinary flat chunk-RAG systems.

### 3.5 Goal Field

`goal` is an optional session-level field used as a lightweight task anchor.

In v1 it is used for:

- biasing retrieval toward the current topic or learning objective
- improving session compression by preserving goal-relevant details
- increasing memory extraction quality by filtering for goal-relevant facts

`goal` is not a workflow engine, planner, or task graph.

## 4. V1 Architecture

### 4.1 Repository Structure

```text
KnowledgeContextEngine/
  apps/
    demo-chat/                  # Thin TypeScript demo harness using Vercel AI SDK
  services/
    engine-python/              # Core Context Engine
    gateway-java/               # Public API, identity mapping, adapter boundary
  packages/
    contracts/                  # OpenAPI / JSON schemas / shared contracts
  data/
    demo-resources/             # Local demo resources
    demo-memories/              # Optional demo seed memories
  docker/
  docs/
    architecture/
    superpowers/
      specs/
      plans/
  scripts/
  docker-compose.yml
  .env.example
```

### 4.2 Service Responsibilities

#### `apps/demo-chat`

- built with TypeScript and Vercel AI SDK
- provides a runnable chat UI and streaming demo
- shows answer and retrieval trace
- exposes resource tree / node drill-down views through the public APIs
- does not implement retrieval, memory, or storage logic

#### `services/engine-python`

The Python service is the core of the project.

It is responsible for:

- resource ingest
- chunking
- `L0 / L1 / L2` generation
- stable node-path generation
- embedding and vector recall
- session context assembly
- memory extraction and memory recall
- rerank and context fusion
- context compression
- final context composition

#### `services/gateway-java`

The Java service is the public boundary and future platform-integration layer.

It is responsible for:

- stable external REST API
- lightweight auth
- internal `UUID` user mapping
- `provider/external_user_id` identity binding
- request validation and boundary checks
- future Zhiguang adapter integration
- proxying to the Python engine

### 4.3 Why Keep Gateway Java in V1

Gateway Java exists in v1 to preserve the target architecture:

- Java side demonstrates clean service integration and backend engineering
- Python side stays focused on context logic
- the project remains ready to integrate with Zhiguang later

The v1 gateway remains intentionally thin.

## 5. Runtime Modes

### 5.1 Demo Mode

Used for independent operation without Zhiguang.

- resources come from `data/demo-resources/`
- identities come from local demo bindings
- no complex auth
- the project must fully answer questions end-to-end in this mode

### 5.2 Zhiguang Mode

Used for future integration with Zhiguang.

- resources come from adapter sync APIs
- users are identified by `provider=zhiguang` and `external_user_id`
- behavior events such as favorites, reading records, or historical questions can be synced later

V1 does not require a full production-grade Zhiguang integration, but it must preserve clean extension points.

### 5.3 Primary V1 Demo Story

V1 should not present itself as "a document Q&A system that might integrate with Zhiguang later".

The primary demo story should be:

- a user asks a question in a knowledge-community scenario
- the system combines:
  - the current article or selected resource
  - related resources or sections
  - the user's prior interests or long-term memory
  - the current session summary
- the system returns a personalized answer
- the system explains why those resources, memories, and session summaries were selected
- the system shows the drill-down path from broad resource selection to final grounding

Demo mode should simulate this story with seeded local resources and seeded user history, even before real Zhiguang integration exists.

## 6. Identity and Isolation Model

### 6.1 User Identity

Internal users use `UUID` identifiers.

External identities are mapped through bindings:

- `provider`
- `external_user_id`
- optional `external_tenant_id`

This supports:

- standalone demo users
- future Zhiguang users
- future additional providers

### 6.2 V1 Access Scope

V1 only supports **user-level isolation**.

V1 explicitly does **not** support:

- complex tenancy
- organization/workspace RBAC
- resource-level ACL systems

This means v1 must isolate by user, but does not implement enterprise-grade multi-tenant security.

## 7. Storage and Persistence

### 7.1 Primary Stores

- **PostgreSQL + pgvector**
  - source of truth for metadata, sessions, memories, traces, and vectors
- **Redis**
  - optional cache for session/retrieval acceleration
- **Local filesystem**
  - demo resource input under `data/demo-resources/`

### 7.2 Core Tables

V1 should stay close to the following minimal schema:

- `users`
  - internal users with `UUID`

- `identity_bindings`
  - maps internal users to external identities

- `resources`
  - resource metadata such as title, provider, source URI, tags, status

- `resource_nodes`
  - stores `L0 / L1 / L2` nodes
  - includes `resource_id`, `level`, `parent_node_id`, `node_path`, text fields, embedding

- `sessions`
  - session header, mode, goal, summary, status

- `session_turns`
  - one row per interaction turn

- `memories`
  - long-term memory entries with `memory_channel`, `memory_type`, salience, source references, and embedding

- `retrieval_traces`
  - retrieval candidates, selections, drill-down trail, compression info, and metrics

### 7.3 Why a Unified `resource_nodes` Table

V1 should not split `L0 / L1 / L2` into separate tables.

A unified node table:

- keeps the schema simple
- supports future traversal
- keeps the retrieval pipeline flexible
- remains sufficient for MVP-level layered recall

## 8. Model and Provider Strategy

V1 uses a **single provider** strategy.

The implementation should support one OpenAI-compatible provider configuration:

- `base_url`
- `api_key`
- `chat_model`
- `embedding_model`

This is intentionally simple.

V1 should reserve configuration compatibility for **Alibaba Cloud Bailian** by allowing the above values to be swapped through configuration. No full multi-provider abstraction layer is required in v1.

## 9. Configuration Strategy

### 9.1 General Rule

- secrets come from `.env`
- non-secret settings live in `yml` or `yaml`

### 9.2 Root-Level Files

- `.env.example`
  - database passwords
  - API keys
  - provider secrets
  - overridable ports if needed

- `docker-compose.yml`
  - one-command local startup

### 9.3 Service-Level Config

- Java:
  - `services/gateway-java/src/main/resources/application.yml`

- Python:
  - `services/engine-python/config.yaml` or equivalent settings file

- Demo chat:
  - `apps/demo-chat/.env.local.example`

### 9.4 Docker Compose Requirement

V1 must provide a working `docker-compose.yml` that supports a runnable local setup.

Preferred v1 containers:

- `postgres`
- `redis`
- `engine-python`
- `gateway-java`
- `demo-chat`

The local experience should be close to "clone -> configure secrets -> docker compose up".

## 10. Public and Internal API Boundaries

### 10.1 Public APIs in `gateway-java`

V1 public APIs should include:

- `POST /api/v1/resources/import`
  - import demo resources or adapter-provided resources

- `GET /api/v1/resources/{resourceId}/tree`
  - browse the resource tree and its `L0 / L1 / L2` structure

- `GET /api/v1/resources/nodes/{nodeId}`
  - inspect a resource node and its path metadata

- `POST /api/v1/sessions`
  - create a session

- `POST /api/v1/sessions/{sessionId}/query`
  - main user-facing question-answering entry

- `POST /api/v1/sessions/{sessionId}/commit`
  - persist the turn and trigger summary/memory updates

- `GET /api/v1/traces/{traceId}`
  - inspect retrieval behavior

- `POST /api/v1/adapters/zhiguang/sync`
  - reserved adapter sync entry for future Zhiguang integration

### 10.2 Internal APIs in `engine-python`

V1 internal APIs should include:

- `POST /internal/resources/index`
- `POST /internal/context/query`
- `POST /internal/memory/extract`
- `POST /internal/session/summarize`

`engine-python` must not be directly exposed to the public internet in v1.

## 11. Main Query Flow

The core user flow should be:

1. user sends a question from `demo-chat` or another caller
2. `gateway-java` authenticates the caller and resolves the internal user
3. `gateway-java` forwards the request to `engine-python`
4. `engine-python` performs:
   - recent session recall
   - memory recall
   - layered resource recall
   - drill-down path construction
   - rerank and filtering
   - context compression
   - final context assembly
   - answer generation
5. `gateway-java` returns:
   - answer
   - trace id
   - used context metadata
   - compression summary
6. the turn is committed and may trigger session summarization and memory extraction

This keeps the project as a complete Q&A system, not just a context-preparation utility.

## 12. Response Schema Strategy

V1 should return a **structured envelope** with a text answer.

Example shape:

```json
{
  "answer": "text answer",
  "traceId": "uuid",
  "citations": [],
  "usedContexts": {
    "resources": [
      {
        "nodePath": "resource://...",
        "drilldownTrail": []
      }
    ],
    "memories": [
      {
        "channel": "user|task_experience",
        "type": "..."
      }
    ],
    "sessionSummary": "..."
  },
  "compressionSummary": {
    "before": 0,
    "after": 0
  }
}
```

V1 does not need general-purpose schema-controlled LLM output.

However, these internal artifacts should be schema-first from the start:

- import payloads
- retrieval traces
- memory extraction result
- context composition result

The schema must be strong enough to express:

- memory channel and memory type
- resource node path
- drill-down trail from `L0` to `L2`

## 13. Security Baseline

### 13.1 Auth Strategy

V1 uses simple API-key-based auth.

- `demo-chat` uses a local demo key
- future integrations use separate keys

JWT and full platform auth are deferred.

### 13.2 Boundary Rules

- only `gateway-java` is publicly exposed
- `engine-python` is internal-only
- frontends do not talk directly to databases
- adapters do not write directly into memory or trace tables

### 13.3 Isolation Rules

- sessions are isolated by internal `user_id`
- memories are isolated by internal `user_id`
- traces are isolated by internal `user_id`
- resources must carry provider/source metadata to avoid accidental cross-mode pollution

### 13.4 Required V1 Protections

- input length limits
- file import whitelist and path validation
- retrieval candidate limits
- safe trace output with no raw secret leakage
- memory write filtering based on simple salience/quality checks
- log scrubbing for keys and sensitive content

### 13.5 Known Risks That Must Be Explicitly Managed

- cross-user memory leakage
- prompt injection from imported resources
- memory poisoning from malicious input
- retrieval trace overexposure
- path traversal during local imports
- excessive compute/cost due to long documents or oversized recall

## 14. V1 MVP Scope

The following items must be completed in v1:

1. internal `UUID` users and identity binding
2. local demo resource import
3. `L0 / L1 / L2` resource node generation with stable `node_path`
4. vector indexing with pgvector
5. session creation and turn persistence
6. lightweight session summary compression
7. dual-channel long-term memory extraction and recall
8. fused query pipeline across resource/session/memory
9. resource tree / node browse APIs
10. final answer generation
11. retrieval trace inspection with drill-down trail
12. demo-chat runnable end-to-end
13. Zhiguang-shaped demo story using local seeded data
14. Zhiguang adapter contract reserved
15. Docker Compose-based local startup
16. configuration split between `.env` and `yml`

## 15. V1 Enhancements That Should Be Included If They Do Not Threaten Feasibility

- `goal` field on session creation and query
- citations in final answer response
- provider/source filtering in retrieval
- Redis caching for hot session or retrieval paths
- richer trace metrics and trace UI

These should not be allowed to derail the MVP.

## 16. Explicit Non-Goals for V1

The following are out of scope for v1:

- complex multi-tenant systems
- organization/workspace RBAC
- production-grade Zhiguang integration
- workflow-heavy autonomous agent systems
- complex tool ecosystems
- Kafka or message-bus architecture
- multiple vector-store backends
- general web crawling/search ingestion
- heavy virtual filesystem semantics
- generalized multi-provider model-routing
- full virtual filesystem commands such as `ls/find/cd` as first-class user APIs

## 17. Acceptance Criteria

V1 is considered successful if the project can demonstrate the following:

1. start locally via Docker Compose with only minimal secret setup
2. import local demo resources
3. create a user and session
4. ask questions through the demo chat
5. receive answers grounded in retrieved resource/session/memory context
6. inspect a retrieval trace that shows the `L0 -> L1 -> L2` drill-down path
7. inspect addressable resource nodes through the public APIs
8. persist the interaction as session state and both user/task-experience memory
9. demonstrate a Zhiguang-shaped personalized Q&A story using local seeded data
10. preserve clear adapter boundaries for future Zhiguang integration

## 18. OpenViking-Inspired but Intentionally Reduced

This design borrows ideas from OpenViking, but does not replicate its full system.

Borrowed ideas:

- unified context abstraction
- layered resource representation
- drill-down retrieval
- addressable context surfaces
- observable retrieval process
- session-end memory iteration

Deliberately reduced in v1:

- heavy virtual filesystem semantics
- broad multi-language systems complexity
- full instruction/skill ecosystem
- enterprise-scale feature surface

The result should feel inspired by a context operating system, while remaining small enough to finish as a strong MVP.
