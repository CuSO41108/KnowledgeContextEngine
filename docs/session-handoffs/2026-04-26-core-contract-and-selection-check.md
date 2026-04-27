# 2026-04-26 Core Contract And Selection Check

## 当前阶段在做什么

当前重点不是继续打磨 `apps/demo-chat` 的前端体验，而是把 V1 的核心闭环做扎实：

1. `trace -> replay -> node snapshot` 公开契约是否真的闭环
2. 资源数继续变多后，`gateway-java` 的候选资源选择是否还稳定

当前工作分支：

- `codex/core-subtopic-routing-quality`

最近 5 个关键 commit：

- `5b435dd` `fix: harden trace replay and resource selection`
- `a820b56` `fix: improve subtopic routing quality`
- `0302858` `fix: align trace memories and improve prompt focus`
- `dcc3018` `Merge pull request #5 from CuSO41108/codex/demo-chat-session-validation-fixes`
- `84cd496` `fix: address review feedback and demo polish`

## 这轮之前已经完成的核心修复

这些内容已经在代码里，不是待办：

- demo session 不再污染后续测试
- `memory` 里的 `task_experience` 已经和 trace 选中的 node 对齐
- engine 侧同资源子主题选择已增强，queue/search/tracing 子主题能命中更具体的 `L2` 节点
- 现有核心回归已经通过：
  - `mvn -f services/gateway-java/pom.xml test`
  - `npm --prefix apps/demo-chat test`
  - `python -m pytest services/engine-python/tests -v --cov=app.services --cov-fail-under=90`

## 这轮新发现的核心问题

### 1. trace replay 的 public contract 没完全接出来

设计文档要求：

- `GET /api/v1/traces/{traceId}`
- `GET /api/v1/traces/{traceId}/nodes/{nodeId}`
- `GET /api/v1/resources/nodes/{nodeId}`

但检查时发现 gateway 原先只暴露了：

- `GET /api/v1/traces/{traceId}`

也就是说，engine internal route 虽然有：

- `/internal/traces/{traceId}/nodes/{nodeId}`
- `/internal/resources/nodes/{nodeId}`

但 gateway public surface 还没把“历史快照查看”和“当前节点查看”真正接出来。

### 2. gateway 的资源候选选择在资源变多时不够稳

旧逻辑问题：

- `ResourceCandidateSelector` 只是简单把 `goal + message` 拆词，然后在 candidate evidence 文本里 `contains`
- `EngineClient` 给 selector 的 evidence 只有：
  - `resourceId`
  - node `title`
  - node `nodePath`
- 没有 node `content`

因此在这种场景下会被带偏：

- `goal` 很泛：例如“写一条关于系统可靠性的 Zhiguang 回复”
- `message` 很具体：例如“我只想解释重复消费和死信队列，不展开削峰填谷”
- 关键术语主要出现在某个资源的正文，而不是标题里

当时我补的测试直接证明旧逻辑会错选一个更泛的 overview 资源。

## 这轮已经完成的修复

### A. 补齐 trace / node snapshot 的 gateway public contract

改动文件：

- `services/gateway-java/src/main/java/com/cuso/kce/gateway/api/TraceController.java`
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/api/ResourceController.java`
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/client/EngineClient.java`

新增能力：

- `GET /api/v1/traces/{traceId}/nodes/{nodeId}`
- `GET /api/v1/resources/nodes/{nodeId}`

对应 `EngineClient` 新增：

- `getTraceNodeSnapshot(traceId, nodeId)`
- `getResourceNode(nodeId)`

### B. 强化 gateway 资源候选选择

改动文件：

- `services/gateway-java/src/main/java/com/cuso/kce/gateway/client/ResourceCandidateSelector.java`
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/client/EngineClient.java`

做了这些增强：

- resource evidence 现在包含 node `content`，不再只看标题和路径
- selector 增加了：
  - 焦点词提取（例如“只想解释 ...”）
  - 排除词惩罚（例如“`不展开 ...`”）
  - 中英别名扩展
    - `死信队列 -> dead-letter queues`
    - `幂等 -> idempotent / idempotency`
    - `重复消费 -> duplicate / duplicate deliveries`
    - `排序信号 -> ranking`
    - `增量刷新 -> incremental refresh`
    - 其他 tracing/search 相关词也做了映射
- 打分上提高了 `message` 和 focus terms 的权重，避免泛 goal 抢走具体子主题

## 这轮新增/更新的测试

### gateway tests

- `services/gateway-java/src/test/java/com/cuso/kce/gateway/TraceControllerTest.java`
  - 新增 public trace node snapshot lookup 测试
- `services/gateway-java/src/test/java/com/cuso/kce/gateway/ResourceControllerTest.java`
  - 新增 current resource node lookup 测试
- `services/gateway-java/src/test/java/com/cuso/kce/gateway/client/EngineClientTest.java`
  - 新增 evidence texts 包含 node `content` 的测试
- `services/gateway-java/src/test/java/com/cuso/kce/gateway/client/ResourceCandidateSelectorTest.java`
  - 新增“资源多、goal 泛、message 具体”时仍能选中 queue 资源的稳定性测试

## 这轮已经做过的验证

### 1. 单元/集成测试

已跑通：

```powershell
mvn -f services/gateway-java/pom.xml test
```

结果：

- `13/13` passed

### 2. 运行态验证

已执行：

```powershell
docker compose up -d --build engine-python gateway-java
docker compose rm -f demo-bootstrap
docker compose up --build demo-bootstrap
```

### 3. 真实 HTTP 验证

已验证通过：

- 泛 goal + queue 子主题：
  - 请求：`我只想解释重复消费和死信队列，不展开削峰填谷。`
  - 命中：`resource://n-zhiguang-message-queue-delivery-guide/l2/s002/000`
- 泛 goal + search 子主题：
  - 请求：`我只想解释排序信号和增量刷新，不展开倒排索引。`
  - 命中：`resource://o-zhiguang-search-indexing-guide/l2/s002/000`

同时验证了：

- `GET /api/v1/traces/{traceId}` 能返回 trace
- `GET /api/v1/traces/{traceId}/nodes/{nodeId}` 能返回历史 snapshot
- `GET /api/v1/resources/nodes/{nodeId}` 能返回当前 node snapshot

### 4. 历史快照 vs 当前节点差异验证

我做过一次 reindex 验证：

1. 先 query 得到 `traceId` 和 `nodeId`
2. 再直接重建同一个 resource 的当前内容
3. 然后分别请求：
   - `GET /api/v1/traces/{traceId}/nodes/{nodeId}`
   - `GET /api/v1/resources/nodes/{nodeId}`

结果符合预期：

- trace-scoped lookup 仍返回旧内容
- current node lookup 返回新内容

这证明 replay 不是死日志，而是具备“历史快照”和“当前节点”两个可区分的 surface。

## 当前结论

### 已经确认闭环的部分

- `trace -> replay -> node snapshot` 这条公开链路现在已经闭环
- gateway 在“资源变多 + 泛 goal + 具体子主题”场景下比之前稳定很多

### 还值得继续追的核心点

下一轮建议继续查这两个，不要回到前端细节：

1. gateway 是否还要公开 `resource tree`，把 drill-down 浏览 surface 也补成 public API
2. 资源继续扩到几十份后，当前 heuristic selector 是否还够，还是要升级成真正的 recall + rerank

## 当前工作区状态

当前分支：

- `codex/core-subtopic-routing-quality`

这轮修复已经推送到远端分支，对应 commit：

- `5b435dd` `fix: harden trace replay and resource selection`

当前工作区里还留着 3 个未跟踪调试图片，不要误提交：

- `tmp-demo-chat-pr5-discovery.png`
- `tmp-demo-chat-pr5-retest.png`
- `tmp-empty-goal-debug.png`

## 下个会话建议怎么接

建议下个会话先读本文件，然后继续：

1. 复核 gateway public API surface 是否还缺 `resource tree`
2. 设计一组“更多资源、更相似标题”的 selector 压测
3. 再决定是否把 gateway 选择逻辑从 heuristic 升级为更正式的 recall/rerank
