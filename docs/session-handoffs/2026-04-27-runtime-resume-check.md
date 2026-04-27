# 2026-04-27 Runtime Resume Check

## 为什么会有这份补充

今天接着 `2026-04-26-v1-gap-closure-and-persistence.md` 和 `2026-04-26-v1-acceptance-recheck.md` 往下做时，先发现一个环境差异：

- 代码和测试状态还在
- 但本机 Docker daemon 当时没起来

所以这份文档只记录“恢复运行态后重新确认了什么”，避免下个会话再重复排查。

## 今天先确认到的当前进度

结合前两份 handoff，可以把当前进度概括成：

1. V1 核心代码改动已经在工作区里
2. public `create -> query -> commit -> tree -> trace -> trace-node` 代码链路已经实现
3. 自动化测试已经覆盖到 public E2E
4. 今天补做的是运行态恢复和 fresh 事实复核，不是再写一轮新代码

## 今天做了什么

### 1. 恢复 Docker 运行态

一开始：

- `docker compose ps -a` 直接失败
- `com.docker.service` 是 `Stopped`

之后通过启动 Docker Desktop，让 daemon 恢复可用，然后执行：

```powershell
docker compose up -d
```

当前 compose 状态重新恢复为：

- `postgres` `Up`
- `redis` `Up`
- `engine-python` `Up`
- `gateway-java` `Up`
- `demo-chat` `Up`
- `demo-bootstrap` `Exited (0)`

并且这次重新启动后，`demo-bootstrap` 又成功跑了一次，日志里显示：

- `importedCount: 5`
- `persistedTurnCount: 2`
- `committedMemoryCount: 0`

这里的 `0` 仍然是因为旧种子用户已存在相同 memory，dedupe 生效，不是 commit 失败。

### 2. 用全新 user/session 重跑了一轮 public verify

为了避免旧种子数据干扰，我今天重新用了一个全新的 user/session：

- `sessionId`: `public-verify-cde8d4a6`
- `externalUserId`: `public-verify-user-cde8d4a6`
- `traceId`: `026769f9-90d0-455b-8b49-657ce6bc61ac`
- `followUpTraceId`: `52c27d2b-e3eb-4529-9ca0-2b54d9d69588`
- `nodeId`: `z-zhiguang-redis-cache-playbook:l2:s001:000`
- `committedMemoryCount`: `3`
- `followUpHasTaskExperience`: `true`

这说明：

1. public create session 正常
2. 首轮 query 正常
3. commit 正常写出 3 条 memory
4. follow-up query 已能召回 `task_experience`

### 3. 直接查 Postgres 的 fresh 事实

围绕 `public-verify-cde8d4a6 / public-verify-user-cde8d4a6`，今天直接查库确认到：

#### identity_bindings

- `user_id`: `fea7ffad-9b73-378b-be3e-4c8a622e8a2a`
- `provider`: `demo_local`
- `external_user_id`: `public-verify-user-cde8d4a6`

#### sessions

- `session_key`: `public-verify-cde8d4a6`
- `provider`: `demo_local`
- `goal`: `write a Zhiguang reply about Redis cache-aside`
- `summary`: 已持久化

#### session_turns

- `turn_count = 1`

#### retrieval_traces

- `trace_count = 2`
- `used_memories_json` 长度范围：`3 ~ 3`
- `used_resources_json` 长度范围：`1 ~ 1`

#### retrieval_trace_nodes

- 两条 trace 都有 snapshot
- `public_node_id = z-zhiguang-redis-cache-playbook:l2:s001:000`

#### memories

该用户最终有 3 条 memory：

- `task_experience / successful_resource`
- `user / explanation_preference`
- `user / user_goal`

#### resources / resource_nodes

今天重新确认：

- `resources where provider = demo_local`: `5`
- `resource_nodes where is_current = true`: `30`

所以“session / turn / trace / trace snapshot / memory / resource current tree”这几层落库事实今天再次被 fresh 证实了。

### 4. 重新验证 demo-chat 服务端代理链路

虽然今天没做成真正的 in-app browser 手点，但我重新打了：

- `POST http://localhost:3000/api/chat`

这次使用的新会话是：

- `sessionId`: `demo-chat-http-f1f6095a`
- `externalUserId`: `demo-chat-user-24456aec`

返回仍然是完整的流式事件：

- `text-start`
- `message-metadata`
- `text-delta`
- `text-end`

随后直接查库确认：

- `sessions.session_key = demo-chat-http-f1f6095a`
- `session_turns.turn_count = 1`
- `retrieval_traces.trace_count = 1`

所以 `demo-chat -> gateway -> engine -> commit -> DB` 这条服务端代理链路今天也重新被实测了一次。

## 今天没能补上的只有一件事

### in-app browser 可视手点仍然被本地 runtime 卡住

今天再次尝试走 `browser-use` 时，`node_repl` 还是直接报：

- 当前解析到的 Node：`v22.19.0`
- 需要：`>= v22.22.0`

今天额外查到：

- 工作区自带 bundled Node 实际是：`v24.14.0`
- 路径：`C:\Users\m1382\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`

也就是说，问题不是“机器上没有更高版本 Node”，而是当前 `node_repl` 没有用到这个 bundled runtime。

## 当前结论

到今天这一步，可以更明确地说：

1. V1 核心运行时代码已经闭环
2. public E2E 自动化已经补上
3. today fresh DB facts 再次证明持久化是真的
4. demo-chat 服务端代理链路 today 也重新验证通过
5. 当前唯一没完成的，是 `browser-use` 受本地 `node_repl` Node 版本影响，没能做“浏览器里手点输入框”的可视 smoke

## 下个会话如果继续，最值得做什么

优先级建议：

1. 如果要补可视验收：
   - 先解决 `node_repl` 使用旧 Node 的问题
   - 目标是让它走到 bundled `v24.14.0`
2. 如果不想继续折腾浏览器 runtime：
   - 可以直接把当前结论整理成正式验收结论
   - 当前证据已经足够支撑“V1 核心模块已满足”
