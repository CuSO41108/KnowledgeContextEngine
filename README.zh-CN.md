# KnowledgeContextEngine

[English](./README.md)

KnowledgeContextEngine 是一个面向知识社区场景的独立上下文引擎示例项目。它将上下文建模为 `Resource / Session / Memory` 三层结构，支持可追踪的分层检索与 drill-down 路径，并提供一个由 Python 引擎、Java 网关、Next.js 聊天界面组成的可运行端到端 demo。

## 项目展示重点

- 基于 `Resource / Session / Memory` 的分层上下文建模。
- 区分用户偏好与任务经验的双通道长期记忆。
- 支持 `L0 / L1 / L2` 分层资源检索与可回放的 trace 快照。
- 提供轻量公共网关边界，便于未来对接外部平台。
- 通过 Docker Compose 提供可直接运行的本地演示与种子数据流程。

## 架构概览

- `services/engine-python`
  核心上下文引擎，负责资源索引、稳定节点标识、记忆提取、trace 生成与上下文融合。
- `services/gateway-java`
  对外 API 边界，负责 API Key 鉴权、请求校验、身份映射以及对 Python 引擎的代理调用。
- `apps/demo-chat`
  轻量 Next.js 演示前端，调用网关并展示实时 trace 元数据。
- `packages/contracts`
  对外响应结构使用的 JSON Schema 与 OpenAPI 契约。
- `data/demo-resources`
  本地 demo 启动时导入的 markdown 资源种子数据。

## 仓库结构

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

## 快速开始

### 方式一：使用 Docker Compose 跑完整 demo

1. 生成本地环境文件：

   ```powershell
   Copy-Item .env.example .env
   ```

2. 启动整套服务：

   ```powershell
   docker compose up -d --build
   ```

3. 打开以下地址：

   - UI: [http://localhost:3000](http://localhost:3000)
   - Gateway API: [http://localhost:8080/api/v1/health](http://localhost:8080/api/v1/health)
   - Engine 健康检查: [http://localhost:8000/health](http://localhost:8000/health)

`demo-bootstrap` 会先完成 demo 数据导入并成功退出，随后 `demo-chat` 才会启动。

### 方式二：本地运行测试

```powershell
mvn -f services/gateway-java/pom.xml test
npm --prefix apps/demo-chat test
python -m pytest services/engine-python/tests -v --cov=app.services --cov-fail-under=90
```

## 本地开发依赖

- Java 21
- Node.js 22
- Python 3.12+
- Docker Desktop / Docker Compose

## 契约与文档

- 设计说明：[docs/superpowers/specs/2026-04-24-knowledge-context-engine-design.md](./docs/superpowers/specs/2026-04-24-knowledge-context-engine-design.md)
- 实施计划：[docs/superpowers/plans/2026-04-24-knowledge-context-engine-v1.md](./docs/superpowers/plans/2026-04-24-knowledge-context-engine-v1.md)
- OpenAPI 契约：[packages/contracts/openapi/gateway.yaml](./packages/contracts/openapi/gateway.yaml)
- Query 响应 Schema：[packages/contracts/json/query-response.schema.json](./packages/contracts/json/query-response.schema.json)
- Trace 响应 Schema：[packages/contracts/json/trace-response.schema.json](./packages/contracts/json/trace-response.schema.json)

## 当前范围

当前仓库重点是一个可运行的本地 demo 和清晰的服务边界。后续如果要接入知识社区主业务后端，建议通过现有网关边界扩展，而不是把上下文引擎直接耦合成某个业务模块。
