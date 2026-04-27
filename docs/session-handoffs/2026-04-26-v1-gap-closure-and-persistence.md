# 2026-04-26 V1 Gap Closure And Persistence

## 当前阶段在做什么

当前重点已经从上一轮的 `trace replay / selector hardening`，切到补齐最初 V1 里还没达标的几个核心项：

1. `POST /api/v1/sessions` 公开创建/确保会话
2. `POST /api/v1/sessions/{sessionId}/commit` 公开提交 turn，持久化 session state 和 memory
3. `GET /api/v1/resources/{resourceId}/tree` 公开资源树浏览
4. 让资源、trace、session、memory 真正落到数据库，而不是仅靠进程内存
5. 把 demo-chat 和 seed flow 接到新的 `create -> query -> commit` 公共链路

当前工作分支：

- `codex/core-subtopic-routing-quality`

## 这轮已经完成的改动

### 1. engine-python 持久化骨架已经补上

新增/修改的核心点：

- `services/engine-python/app/db.py`
  - 新增 `KCE_RUNTIME_DATABASE_URL` override
  - 暴露 `get_db_session()`
- `services/engine-python/app/main.py`
  - 启动时 `Base.metadata.create_all(bind=engine)`
- `services/engine-python/app/models.py`
  - 补了 `slug / session_key / provider / trace_id / public_node_id / used_*_json / answer_text / summary` 等运行态字段
- `services/engine-python/app/services/persistence.py`
  - 新增整套 DB 持久化辅助逻辑
  - 包括 resource upsert、session ensure、trace persist、trace snapshot 查询、memory recall、session commit
- `services/engine-python/app/api.py`
  - `/internal/resources/index` 改为 DB-backed
  - 新增 `/internal/sessions`
  - 新增 `/internal/sessions/{sessionKey}/commit`
  - 新增 `/internal/users/{userId}/memories`
  - 新增 `/internal/resources/providers/{provider}/trees`
  - `/internal/context/query` 在带 `session_key + user_id` 时持久化 trace
  - `/internal/resources/{resourceId}/tree`
  - `/internal/resources/nodes/{nodeId}`
  - `/internal/traces/{traceId}`
  - `/internal/traces/{traceId}/nodes/{nodeId}`
    都优先从 DB 读取

### 2. gateway-java 公共 API surface 已补齐

新增/修改的核心点：

- `services/gateway-java/src/main/java/com/cuso/kce/gateway/api/SessionController.java`
  - 新增 `POST /api/v1/sessions`
  - 新增 `POST /api/v1/sessions/{sessionId}/commit`
  - `query(...)` 现在会把 `externalUserId` 继续传给 engine client
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/api/ResourceController.java`
  - 新增 `GET /api/v1/resources/{resourceId}/tree`
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/client/EngineClient.java`
  - `importResources(...)` 现在传 `provider / resource_slug / source_uri`
  - `query(...)` 现在会：
    - 先 ensure session
    - 从 engine 拉 provider 资源树
    - 拉用户 memories
    - 带 `session_key + user_id` 调 `/internal/context/query`
  - 新增：
    - `createSession(...)`
    - `commitSession(...)`
    - `getResourceTree(...)`
    - provider tree metadata refresh / memory merge / summary merge

### 3. demo-chat 和 seed flow 已切到新链路

- `apps/demo-chat/app/api/chat/route.ts`
  - 现在是：
    - `POST /api/v1/sessions`
    - `POST /api/v1/sessions/{sessionId}/query`
    - `POST /api/v1/sessions/{sessionId}/commit`
  - 如果 create 或 commit 失败，会显式返回错误，不再默默吞掉
- `scripts/seed_demo_data.py`
  - 现在会：
    - 导入资源
    - 创建 session
    - 首轮 query
    - commit
    - 再次 ensure session 验证 `turnCount / summary`
    - follow-up query 验证能召回 `task_experience` memory

### 4. OpenAPI 契约已经同步

- `packages/contracts/openapi/gateway.yaml`
  - 新增：
    - `GET /api/v1/resources/nodes/{nodeId}`
    - `GET /api/v1/resources/{resourceId}/tree`
    - `POST /api/v1/sessions`
    - `POST /api/v1/sessions/{sessionId}/commit`
    - `GET /api/v1/traces/{traceId}/nodes/{nodeId}`

## 这轮新增/更新的测试

### Python

- `services/engine-python/tests/conftest.py`
  - 改成 sqlite runtime test DB，并在每个 test 前重建 schema
- 新增 `services/engine-python/tests/test_persistence_api.py`
  - provider resource tree / current node snapshot
  - session create + query + commit
  - persisted summary / memories / trace snapshot 回读

### Java

- `services/gateway-java/src/test/java/com/cuso/kce/gateway/SessionControllerTest.java`
  - 新增 create session test
  - 更新 query mock/verify 为 6 参数签名
  - 新增 commit session test
- `services/gateway-java/src/test/java/com/cuso/kce/gateway/ResourceControllerTest.java`
  - 新增 resource tree public API test

## 这轮已经做过的验证

### 1. gateway-java tests

已跑：

```powershell
mvn -f services/gateway-java/pom.xml test
```

结果：

- `16/16` tests passed

### 2. engine-python tests

已跑：

```powershell
python -m pytest services/engine-python/tests -v
```

结果：

- `39/39` passed

### 3. demo-chat tests + build

已跑：

```powershell
npm --prefix apps/demo-chat test
npm --prefix apps/demo-chat run build
```

结果：

- `13/13` tests passed
- Next build passed

### 4. Docker Compose / bootstrap 验证

我发起过：

```powershell
docker compose up -d --build
```

这个命令在当前线程里被用户中断了提示，但后台实际完成了重建。当前状态：

- `engine-python` `Up`
- `gateway-java` `Up`
- `demo-chat` `Up`
- `demo-bootstrap` `Exited (0)`

已确认：

```powershell
docker compose ps -a
docker compose logs demo-bootstrap --tail 200
```

`demo-bootstrap` 成功输出：

- `importedCount: 5`
- `committedMemoryCount: 3`
- `persistedTurnCount: 1`
- `seedTraceId: 254e8a9c-7050-461b-b20e-c23e526b7638`
- `followUpTraceId: fecd7e5c-55fb-4993-ae22-a2d8f2b0e188`

engine log 里也能看到新的完整链路已发生：

- `/internal/sessions`
- `/internal/resources/providers/demo_local/trees`
- `/internal/users/{userId}/memories`
- `/internal/context/query`
- `/internal/sessions/demo-history/commit`

### 5. public API smoke check

在当前 Docker 栈上，我又补做了一轮最小 public smoke check，真实调用了：

- `POST /api/v1/sessions`
- `GET /api/v1/resources/z-zhiguang-redis-cache-playbook/tree`
- `POST /api/v1/sessions/{sessionId}/query`
- `POST /api/v1/sessions/{sessionId}/commit`
- `GET /api/v1/traces/{traceId}`
- `GET /api/v1/traces/{traceId}/nodes/{nodeId}`
- `GET /api/v1/resources/nodes/{nodeId}`
- 再次 `POST /api/v1/sessions` 验证持久化后的 session state

实际 smoke 结果：

- `sessionId`: `demo-smoke-d623be9c`
- `queryTraceId`: `3e4f7d2d-52fc-40f8-873c-f001122f3f3e`
- `queryNodeId`: `z-zhiguang-redis-cache-playbook:l2:s001:000`
- `resourceTreeNodes`: `7`
- `turnCount` after re-ensure: `1`
- `created` after re-ensure: `false`

这说明最小 public 会话链路和资源/trace 可寻址链路已经在运行态走通。

## 当前判断

从代码和 bootstrap 结果看，之前最明显的未满足项已经基本补上：

1. 用户/会话创建：已补 public create session
2. 资源树公共 API：已补 public tree route
3. 持久化：query/trace/session/memory 已接到 DB
4. demo 个性化链路：seed 已走 create/query/commit/follow-up

但还差最后一轮“显式验收复核”，不要直接宣布全部通过。

## 还没做完的事

下个会话最值得先做的是这几项：

1. 做一轮显式 public API smoke check
   - `POST /api/v1/sessions`
   - `POST /api/v1/sessions/{id}/query`
   - `POST /api/v1/sessions/{id}/commit`
   - `GET /api/v1/resources/{resourceId}/tree`
   - `GET /api/v1/resources/nodes/{nodeId}`
   - `GET /api/v1/traces/{traceId}`
   - `GET /api/v1/traces/{traceId}/nodes/{nodeId}`
2. 直接查 Postgres，证明 session / turn / memory / trace 真的落库
   - 建议查：
     - `users`
     - `identity_bindings`
     - `sessions`
     - `session_turns`
     - `memories`
     - `retrieval_traces`
     - `retrieval_trace_nodes`
     - `resources`
     - `resource_nodes`
3. 用浏览器手动点一次 `http://localhost:3000`
   - 确认 demo-chat UI 的真实提问也会成功 commit
   - 顺便确认 trace panel 还能正常展示
4. 重新写一版最新验收结论
   - 很可能之前的“6 满足 / 2 部分 / 2 未满足”需要更新
5. 视情况补一个 public E2E test
   - 现在 `services/engine-python/tests/test_demo_story_e2e.py` 还是直接打 public `query`
   - 它没有覆盖 public `create + commit + tree + trace node` 新 surface

## 当前工作区状态

当前 `git status --short` 里，和这轮有关的主要改动包括：

- `apps/demo-chat/app/api/chat/route.ts`
- `packages/contracts/openapi/gateway.yaml`
- `scripts/seed_demo_data.py`
- `services/engine-python/app/api.py`
- `services/engine-python/app/db.py`
- `services/engine-python/app/main.py`
- `services/engine-python/app/models.py`
- `services/engine-python/app/services/persistence.py`
- `services/engine-python/tests/conftest.py`
- `services/engine-python/tests/test_persistence_api.py`
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/api/ResourceController.java`
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/api/SessionController.java`
- `services/gateway-java/src/main/java/com/cuso/kce/gateway/client/EngineClient.java`
- `services/gateway-java/src/test/java/com/cuso/kce/gateway/ResourceControllerTest.java`
- `services/gateway-java/src/test/java/com/cuso/kce/gateway/SessionControllerTest.java`

注意：

- `docs/session-handoffs/` 当前整体是未跟踪目录
- 还有 3 个未跟踪调试图片，不要误提交：
  - `tmp-demo-chat-pr5-discovery.png`
  - `tmp-demo-chat-pr5-retest.png`
  - `tmp-empty-goal-debug.png`

## 下个会话建议怎么接

建议顺序：

1. 先读本文件和 `docs/session-handoffs/2026-04-26-core-contract-and-selection-check.md`
2. 先跑 public API smoke check
3. 再查 Postgres 落库事实
4. 再看 demo-chat 浏览器手测
5. 最后重新更新验收结论，而不是先继续做下一轮优化
