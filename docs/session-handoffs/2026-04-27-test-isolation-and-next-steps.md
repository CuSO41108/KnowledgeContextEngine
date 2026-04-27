# 2026-04-27 Test Isolation And Next Steps

## 这份 handoff 解决什么问题

前面的 handoff 已经把 V1 运行态恢复、public API、持久化落库这些事实补齐了。这一份专门记录今天继续做手测时确认到的两个重点：

1. 当前 demo-chat 为什么会让人感觉“货不对板”
2. 下一会话应该如何继续做隔离测试，避免被 session / memory 干扰

## 当前任务现在停在哪

当前已经不是“功能有没有跑起来”的问题，而是进入了“怎么正确验证它”的阶段。

已确认：

1. `create -> query -> commit -> trace -> trace-node -> resource-node -> resource-tree` 的 public API 链路是通的
2. `demo-chat -> gateway -> engine -> commit -> DB` 的服务端代理链路也是通的
3. `session / turn / trace / trace snapshot / memory / resource tree` 都已经真实落库

当前还没继续往前做的，是一轮更严格的“隔离手测”和“最终验收表述”。

## 今天额外确认到的关键事实

### 1. AOF 这个例子当前不适合作为正例

用户在 UI 里测试了：

- Goal: `write a Zhiguang reply about AOF of Redis`
- Message: `I am replying on Zhiguang. How should I explain AOF briefly?`

今天重新用全新 user + 全新 session 做了隔离验证后，确认当前 demo 语料里没有 AOF 对应资源。

现有 demo 资源只有这 5 份：

- `a-zhiguang-reply-tone-note`
- `m-zhiguang-distributed-tracing-guide`
- `n-zhiguang-message-queue-delivery-guide`
- `o-zhiguang-search-indexing-guide`
- `z-zhiguang-redis-cache-playbook`

其中 Redis 这份只覆盖 `cache-aside`，不覆盖 `AOF`。所以 AOF 问题更像是“语料缺口 + selector fallback 到 tone note”，不是核心链路坏了。

### 2. demo-chat 的“Start fresh session”只换 session，不换 user

当前 demo-chat 的关键行为是：

1. `Start fresh session` 会换一个新的 `sessionId`
2. 但 `/api/chat` 默认仍然会走固定 `externalUserId = demo-user-1`

因此：

1. `sessionSummary` 的污染来自“同一个 session 连续追问”
2. `memories` 里的多个 `USER_GOAL`、`TASK_EXPERIENCE` 来自“同一个 user 跨 session 累积”

这不是数据库串数据，而是当前 UI 默认身份模型如此。

### 3. 不同浏览器 / 网络 / 设备，目前不会自动变成不同用户

当前唯一用户标识不是浏览器指纹，也不是 IP，而是：

- `provider + externalUserId`

网关会把它映射成稳定 UUID。

所以如果还是走 demo-chat 当前默认值：

- 换浏览器
- 换网络
- 换设备

结果通常仍然会共享同一个长期 memory，只要请求里的 `externalUserId` 还是同一个值。

## 下一会话继续时，正确的测试方法

### 场景 1：测“这组 goal/message 有没有命中对的资源”

不要只按 UI 点 `Start fresh session`。

应该：

1. 换一个全新的 `externalUserId`
2. 再换一个全新的 `sessionId`

这样才能把 user-level memory 和 session-level summary 都隔离掉。

### 场景 2：测“follow-up query 会不会利用刚写入的 memory”

应该：

1. 保持同一个 `externalUserId`
2. 保持同一个 `sessionId`
3. 连续问两轮

这样才能验证 commit 后的 recall。

### 场景 3：测“跨 session 的长期记忆会不会被召回”

应该：

1. 保持同一个 `externalUserId`
2. 使用不同的 `sessionId`

这样才能看出 user memory 是否跨 session 生效。

### 场景 4：测“重启后持久化还在不在”

应该记录并复用：

1. `externalUserId`
2. `sessionId`
3. `traceId`

重启相关服务后，再查同一组 session / trace / node / memory。

## 建议继续使用的正例集合

这几组是当前语料内的正例，更适合继续做路由准确性手测：

1. Redis cache-aside
   - Goal: `write a Zhiguang reply about Redis cache-aside`
   - Message: `I am replying on Zhiguang. How should I explain Redis cache-aside briefly?`
2. 分布式追踪
   - Goal: `写一条关于分布式追踪的 Zhiguang 回复`
   - Message: `我想在知广项目上解释分布式追踪，请覆盖 trace、span、调用链、采样和日志关联。`
3. 消息队列
   - Goal: `写一条关于消息队列的 Zhiguang 回复`
   - Message: `我只想解释重复消费、幂等和死信队列，不展开削峰填谷。`
4. 搜索索引
   - Goal: `写一条关于搜索索引的 Zhiguang 回复`
   - Message: `我只想解释排序信号和增量刷新，不展开倒排索引。`

负例建议保留：

1. Redis AOF

它适合用来证明“当前 selector 没坏，但 demo 语料缺这一块”。

## 下一会话最值得做的几步

优先级建议如下：

1. 先把 `create -> query -> commit` 的隔离测试模板整理并跑一轮
   - 每个正例都用新的 `externalUserId + sessionId`
   - 核对 `answer / nodePath / trace / tree / node`
2. 再做一轮 follow-up query 测试
   - 验证同 session 和记忆召回是否符合预期
3. 再决定是否要改 demo-chat
   - 选项 A：仅补文档说明“Start fresh session 不会换 user”
   - 选项 B：给 UI 增加可选 `externalUserId`
   - 选项 C：给 UI 增加“Start fresh user + session”
4. 如果要解决“货不对板”的核心观感问题，再决定是否补 demo 语料
   - 例如补一份 Redis AOF 资源
5. 最后再更新正式验收结论
   - 区分“当前 demo 核心能力已达标”
   - 和“是否按最初 spec 100% 完成”

## 当前仍然未完成的更大范围事项

如果下一会话不只是做手测，还想继续推进“严格对齐最初 V1 scope”，仍有两项历史缺口没补：

1. `pgvector` 真检索还没实现
2. `POST /api/v1/adapters/zhiguang/sync` 入口还没补

这两项不阻塞当前 demo 验收，但会影响“是否可以宣称最初 V1 字面范围已全部完成”。

## 工作区状态提醒

当前分支：

- `codex/core-subtopic-routing-quality`

当前不是干净工作区：

1. 有多处已修改未提交文件
2. `docs/session-handoffs/` 整体仍是未跟踪目录
3. 还有若干临时图片未清理

所以下一会话如果要继续：

1. 先读这份 handoff
2. 再看 `git status`
3. 不要误把 handoff 文档和临时图片一起当成无关文件清掉
