# KnowledgeContextEngine

[![CI](https://github.com/CuSO41108/KnowledgeContextEngine/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/CuSO41108/KnowledgeContextEngine/actions/workflows/ci.yml)
[简体中文](./README.zh-CN.md)

KnowledgeContextEngine is a standalone context-engine demo for knowledge-community scenarios. It models context as `Resource / Session / Memory`, supports traceable retrieval with drill-down paths, and ships with a runnable end-to-end demo built from a Python engine, a Java gateway, and a Next.js chat UI.

## What It Demonstrates

- Layered context modeling across `Resource`, `Session`, and `Memory`.
- Dual-channel long-term memory for both user preferences and task / experience signals.
- Traceable retrieval with `L0 / L1 / L2` resource drill-down and reusable trace snapshots.
- A thin public gateway boundary that can later integrate with external platforms.
- A fully runnable local demo with seeded data and Docker Compose orchestration.

## Architecture

- `services/engine-python`
  The core context engine. It handles resource indexing, stable node identity, memory extraction, trace generation, and context fusion.
- `services/gateway-java`
  The public API boundary. It handles API-key auth, request validation, identity mapping, and proxying to the Python engine.
- `apps/demo-chat`
  A thin Next.js demo chat that calls the gateway and renders live trace metadata.
- `packages/contracts`
  Shared JSON Schema and OpenAPI artifacts for public payload contracts.
- `data/demo-resources`
  Seed markdown resources used by the local demo bootstrap flow.

## Repository Layout

```text
KnowledgeContextEngine/
  apps/
    demo-chat/
  services/
    engine-python/
    gateway-java/
  packages/
    contracts/
  data/
    demo-resources/
  docs/
    superpowers/
      specs/
      plans/
  scripts/
  docker-compose.yml
  .env.example
```

## Quick Start

### Option 1: Full demo with Docker Compose

1. Create a local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Start the full stack:

   ```powershell
   docker compose up -d --build
   ```

3. Open the demo chat:

   - UI: [http://localhost:3000](http://localhost:3000)
   - Gateway API: [http://localhost:8080/api/v1/health](http://localhost:8080/api/v1/health)
   - Engine health: [http://localhost:8000/health](http://localhost:8000/health)

`demo-bootstrap` seeds the demo resources and exits successfully before `demo-chat` starts.

### Option 2: Run tests locally

```powershell
mvn -f services/gateway-java/pom.xml test
npm --prefix apps/demo-chat test
python -m pytest services/engine-python/tests -v --cov=app.services --cov-fail-under=90
```

## Local Development Prerequisites

- Java 21
- Node.js 22
- Python 3.12+
- Docker Desktop / Docker Compose

## Contracts and Docs

- Design spec: [docs/superpowers/specs/2026-04-24-knowledge-context-engine-design.md](./docs/superpowers/specs/2026-04-24-knowledge-context-engine-design.md)
- Implementation plan: [docs/superpowers/plans/2026-04-24-knowledge-context-engine-v1.md](./docs/superpowers/plans/2026-04-24-knowledge-context-engine-v1.md)
- OpenAPI contract: [packages/contracts/openapi/gateway.yaml](./packages/contracts/openapi/gateway.yaml)
- Query response schema: [packages/contracts/json/query-response.schema.json](./packages/contracts/json/query-response.schema.json)
- Trace response schema: [packages/contracts/json/trace-response.schema.json](./packages/contracts/json/trace-response.schema.json)

## Current Scope

This repository currently focuses on a runnable local demo and clean service boundaries. It is designed so the gateway can later connect to external knowledge-community backends through explicit integration points instead of turning the context engine into a tightly coupled application module.
