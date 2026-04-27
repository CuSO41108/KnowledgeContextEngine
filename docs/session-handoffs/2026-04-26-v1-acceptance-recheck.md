# 2026-04-26 V1 Acceptance Recheck

## 这轮接着做了什么

本轮是接着 `2026-04-26-v1-gap-closure-and-persistence.md` 往下收口，不再假设 handoff 里的结果仍然成立，而是重新做了一轮 fresh 验收。

目标是确认两件事：

1. 之前补上的 public `create -> query -> commit -> tree -> trace -> trace-node` 链路是否真的在当前工作区和当前 Docker 栈上可用
2. 项目 V1 现在到底还缺“生产模块”，还是只缺“自动化覆盖/验收证据”

## 结论先说

当前没有发现新的 V1 生产模块缺口。

这轮真正补上的缺口是：

- `services/engine-python/tests/test_demo_story_e2e.py`
  - 新增 `test_public_session_flow_persists_turn_memory_and_trace_surfaces`
  - 把之前 handoff 里提到还没自动化覆盖到的 public surface 真正补上：
    - `POST /api/v1/sessions`
    - `POST /api/v1/sessions/{sessionId}/query`
    - `POST /api/v1/sessions/{sessionId}/commit`
    - `GET /api/v1/resources/{resourceId}/tree`
    - `GET /api/v1/traces/{traceId}`
    - `GET /api/v1/traces/{traceId}/nodes/{nodeId}`
    - `GET /api/v1/resources/nodes/{nodeId}`
    - follow-up query 对 `task_experience` memory 的召回

也就是说，这次补的是“验收级自动化缺口”，不是再补一块新的运行时代码。

## fresh public smoke 里发现并澄清的点

### 1. 旧种子用户的 `committedMemoryCount` 可能是 `0`

我先用已有种子用户跑了一轮 fresh smoke：

- `sessionId`: `demo-smoke-06cc5c53`
- `traceId`: `65858247-04a1-4c40-894f-4b5b8ada1213`
- `nodeId`: `z-zhiguang-redis-cache-playbook:l2:s001:000`
- `commitStatus`: `ok`
- `committedMemoryCount`: `0`

这不是 commit 失败，而是 dedupe 生效了。

原因是 `demo-user-1` 之前已经被 bootstrap 写入过同样的 3 条 memory：

- `user_goal`
- `explanation_preference`
- `successful_resource`

`commit_session_turn(...)` 当前返回的是“新增写入的 memory 数”，不是“用户当前持有的 memory 总数”。

### 2. 持久化本身没有问题

即使在 `committedMemoryCount = 0` 的 smoke 里，数据库仍然确认了：

- `sessions` 里有 `demo-smoke-06cc5c53`
- `session_turns` 里有对应 turn
- `retrieval_traces` 里有对应 trace
- `retrieval_trace_nodes` 里有对应 snapshot
- `memories` 里该用户已有 3 条可召回 memory

所以这里不是“没有落库”，而是“没有新增 memory”。

## 用全新 user/session 做的验收结果

为了排除 dedupe 干扰，我又用全新的 `externalUserId/sessionId` 跑了一轮完整 public verify：

- `sessionId`: `public-verify-ff25e8b1`
- `externalUserId`: `public-verify-user-ff25e8b1`
- `traceId`: `9a0aeef3-dbbb-43d4-a3b6-e8dbf5cdc9a4`
- `nodeId`: `z-zhiguang-redis-cache-playbook:l2:s001:000`
- `committedMemoryCount`: `3`
- `followUpHasTaskExperience`: `true`

这说明对一个全新用户来说，public `create -> query -> commit` 链路会：

1. 建 session
2. 写 turn
3. 写 trace
4. 写 trace snapshot
5. 写出 3 条 memory
6. 在 follow-up query 中召回 `task_experience`

## 直接查 Postgres 的 fresh 事实

针对 `public-verify-ff25e8b1` 这轮会话，直接查库得到：

### sessions

- `session_key`: `public-verify-ff25e8b1`
- `provider`: `demo_local`
- `goal`: `write a Zhiguang reply about Redis cache-aside`
- `summary`: 已持久化

### session_turns

- `turn_count`: `1`

### retrieval_traces

- `trace_count`: `2`
  - 首轮 query 一条
  - follow-up query 一条

每条 trace 都带：

- `used_memories = 3`
- `used_resources = 1`

### retrieval_trace_nodes

两条 trace 都有 node snapshot：

- `public_node_id`: `z-zhiguang-redis-cache-playbook:l2:s001:000`
- snapshot content 已持久化

### memories

该全新用户最终有 3 条 memory：

- `user_goal`
- `explanation_preference`
- `successful_resource`

### resources / resource_nodes

当前库里还确认到：

- `resources` for `demo_local`: `5`
- `resource_nodes where is_current = true`: `30`

## demo-chat 验证结果

### 浏览器手点

这轮没有完成真正的 in-app browser 手点验证，不是因为页面异常，而是本地 browser runtime 被卡住了：

- `node_repl` 当前解析到的 Node 版本：`v22.19.0`
- browser-use 需要：`>= v22.22.0`

所以这轮无法继续用 in-app browser 做 UI 点击。

### fallback 验证

为了不把验收卡死在工具环境上，我直接打了：

- `POST http://localhost:3000/api/chat`

实际返回了完整的流式消息：

- `text-start`
- `message-metadata`
  - 带 `trace.answer`
  - 带 `trace.traceId`
  - 带 `trace.memories`
  - 带 `trace.resources`
  - 带 `trace.compressionSummary`
- `text-delta`
- `text-end`

并且随后直接查库确认：

- `sessions.session_key = demo-chat-http-smoke` 已存在
- `session_turns` 对应 turn 已写入

所以虽然这轮没做成“浏览器里手点输入框”，但 demo-chat 的服务端代理链路已经被实际打通，并且 commit 也确实发生了。

## 本轮 fresh 自动化验证

这轮重新跑过的命令和结果：

### Python

```powershell
python -m pytest services/engine-python/tests -v
```

结果：

- `40/40` passed

其中包含新增的 public E2E：

- `test_public_session_flow_persists_turn_memory_and_trace_surfaces`

### Java

```powershell
mvn -f services/gateway-java/pom.xml test
```

结果：

- `16/16` passed

### demo-chat

```powershell
npm --prefix apps/demo-chat test
npm --prefix apps/demo-chat run build
```

结果：

- `13/13` tests passed
- Next build passed

## 当前对 V1 的判断

如果按最初 V1 需求和最近两份 handoff 的目标来看，当前状态可以更新为：

1. public session create：已满足
2. public session commit：已满足
3. public resource tree：已满足
4. public resource node：已满足
5. public trace：已满足
6. public trace node snapshot：已满足
7. session / turn / trace / trace snapshot / memory 落库：已满足
8. follow-up query 对已提交 memory 的召回：已满足
9. demo-chat 服务端代理链路：已满足
10. browser 内可视手点验收：本轮未完成，但阻塞点是本地 browser runtime 版本，不是应用行为异常

所以，当前更准确的说法不是“V1 还缺核心模块”，而是：

- 核心 V1 模块已经闭环
- 自动化 public E2E 缺口已补上
- 还剩一个可选的浏览器手点验收可以在本地 browser runtime 修好后补做

## 如果下个会话还要继续

下个会话建议优先做这两件事之一：

1. 修复本地 browser-use runtime（让 `node_repl` 用到 `>= v22.22.0` 的 Node），再做一次真正的 demo-chat 可视手点 smoke
2. 如果不想继续折腾浏览器工具链，就把当前结论整理进正式验收文档或 PR 描述，准备收尾
