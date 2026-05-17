# KnowledgeContextEngine

[![CI](https://github.com/CuSO41108/KnowledgeContextEngine/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/CuSO41108/KnowledgeContextEngine/actions/workflows/ci.yml)

KnowledgeContextEngine 是一个面向知识社区场景的 Agent Context Engine，目标是为问答、长期记忆和后续 Agent 执行提供可追踪的上下文基础设施。

普通 RAG 往往停留在“文档切片 + topK 拼 prompt”。本项目更关注 context engineering：如何把资源、会话和长期记忆拆开建模，并让每次回答都能解释证据来源、选择原因和上下文压缩过程。

## 项目思考

我最初参考的是 OpenViking 一类 Context Database / Agent Context 系统的思路。它们把 Agent 运行所需的 memory、resources、skills 和 session context 统一管理，并强调分层加载、可观察检索轨迹和上下文自迭代。

KnowledgeContextEngine 的设计目标是把问答过程中的上下文变成可建模、可追踪、可评测的工程对象。相比普通的“文档切片 + topK 拼 prompt”式 RAG，本项目更强调以下几个设计原则：

- **证据约束回答**：在当前资源范围内选择可用证据；证据不足时返回拒答或谨慎回答。
- **可观察检索**：为每次回答保留命中词、分数、节点路径、选择原因和 trace 快照。
- **多源上下文融合**：将资源文档、会话目标、用户偏好、历史成功资源和任务经验统一建模。
- **分层证据组织**：通过 L0 / L1 / L2 资源节点支持从粗粒度概览到细粒度证据的 drill-down。
- **评测驱动迭代**：用固定评测集验证检索命中、拒答、记忆抽取和 trace 可回查，而不是只依赖单次 demo 效果。

## 核心能力

- `Resource / Session / Memory` 三层上下文建模。
- `L0 / L1 / L2` 资源节点分层，支持稳定 `nodePath` 和 drill-down 轨迹。
- 当前资源范围内的 BM25-like 关键词检索，带节点类型权重、排除意图处理和证据 trace。
- 双通道长期记忆：用户偏好记忆与任务经验记忆分开写入和召回。
- 检索 trace 可回查，保留命中节点、快照内容、分数、命中词和选择原因。
- 确定性 evaluation harness，用固定问题集验证检索、拒答、记忆和 trace，而不是只看一次 LLM 输出。
- OpenAI-compatible 答案生成可选；没有模型 key 时仍可用确定性 fallback 跑完整 demo 和测试。

## 架构概览

- `services/engine-python`
  核心上下文引擎，负责资源索引、节点构建、检索评分、记忆提取、上下文融合、答案生成和 trace 持久化。
- `services/gateway-java`
  对外 API 边界，负责 API Key 鉴权、身份映射、请求校验，以及把前端或业务后端请求代理到 Python engine。Gateway 到 engine 的 `/internal/*` 调用使用内部 Bearer token 保护。
- `apps/demo-chat`
  轻量演示前端，用来展示回答和 trace；它不承担检索、记忆或上下文编排逻辑。
- `data/demo-resources`
  本地 demo 使用的知识社区风格 Markdown 资源。
- `eval`
  v1 评测集，记录问题、预期证据节点、是否应拒答和质量备注。
- `scripts`
  数据种子、等待服务、评测 harness 等本地工具。

### V1 接入边界

`provider` 在本项目里表示资源来源命名空间，而不是模型厂商。例如：

- `demo_local` 表示本地 demo Markdown 资源。
- `zhiguang` 表示从知光后端同步进来的知文资源。

知光详情页问答的 v1 主链路是当前资源限定检索：业务后端先把当前知文按需同步到 KCE，拿到 `resourceId`，再用这个 `resourceId` 调用 session query。Python engine 在当前知文内选择 L0/L1/L2 证据节点，并返回 answer、used contexts、compression summary 和可回查 trace。

`/api/v1/resources/import` 是本地 demo 的目录导入能力；真实业务接入优先走类似 `/api/v1/adapters/zhiguang/sync` 的 payload 同步接口。

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

### 方式二：运行核心评测集

```powershell
python scripts/run_kce_eval_v1.py
```

该脚本会用本地 SQLite 临时库启动 engine，关闭真实 LLM，运行检索、记忆、session compression、拒答和 trace 可回查案例。输出里会包含：

- `postId`
- `question`
- `expectedEvidenceNode`
- `shouldRefuse`
- `actualAnswer`
- `qualityNotes`
- 实际命中的 `selectedNodePaths`

## 可选：真实 LLM 答案生成

默认情况下，`engine-python` 使用确定性 fallback，方便测试和 demo 在没有模型 key 的情况下运行。要接入真实 OpenAI-compatible 聊天模型，可在 `.env` 中开启：

```env
ANSWER_LLM_ENABLED=true
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=your-key
OPENAI_CHAT_MODEL=qwen-plus
ANSWER_MAX_TOKENS=700
ANSWER_CONTEXT_MAX_CHARS=6000
```

DeepSeek 也可以通过同一套 OpenAI-compatible 配置接入：

```env
ANSWER_LLM_ENABLED=true
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=your-deepseek-key
OPENAI_CHAT_MODEL=deepseek-v4-flash
ANSWER_MAX_TOKENS=700
ANSWER_CONTEXT_MAX_CHARS=6000
```

如果 provider 不可用或未配置，系统会保留 trace 和上下文元数据，并自动回退到确定性答案。

## 本地测试

```powershell
mvn -f services/gateway-java/pom.xml test
npm --prefix apps/demo-chat test
python -m pytest services/engine-python/tests -v --ignore=services/engine-python/tests/test_demo_story_e2e.py --cov=app.services --cov-fail-under=90
python scripts/run_kce_eval_v1.py
```

`test_demo_story_e2e.py` 需要先启动并 seed Docker demo stack；CI 会把它作为单独任务运行，避免本机已有 `localhost:8080` 服务污染结果。

## 本地开发依赖

- Java 21
- Node.js 22
- Python 3.12+
- Docker Desktop / Docker Compose
