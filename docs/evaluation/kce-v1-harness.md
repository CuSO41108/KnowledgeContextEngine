# KCE V1 Evaluation Harness

This harness is the small control surface for the part of KCE that matters most: retrieval, memory, compression, and traceability. It is not an agent loop benchmark and it deliberately does not score live LLM prose by default.

Run it from the repository root:

```powershell
python scripts/run_kce_eval_v1.py
```

The runner loads `eval/kce_v1_harness_cases.json`, starts the FastAPI app in process, uses a local SQLite runtime database under `.eval-runtime/`, and forces `ANSWER_LLM_ENABLED=false`. That keeps the result deterministic while still exercising the real resource indexing, query selection, memory extraction, session summarization, and trace lookup routes.

## What V1 Already Proves

- Resource context is layered as `L0 / L1 / L2`, with stable `nodePath` values and drill-down trails.
- Query results carry explicit `usedContexts.resources`, `usedContexts.memories`, session summary, and compression counts.
- Trace nodes are re-queryable through trace-scoped snapshots, so an answer can still explain what it used after the resource is reindexed later.
- Memory has two channels: `user` and `task_experience`. Successful resource usage is kept as task experience instead of being mixed into user profile facts.
- Zhiguang adapter metadata can be present in an imported post without becoming the answer for generic summary questions.

## Harness Axes

1. Retrieval focus: does the system pick the right section when the user asks for ranking/refresh, idempotency/dead-letter queues, or sampling/log correlation?
2. Broad summary coverage: does a long article summary include later substantive sections, not only the first matched paragraph?
3. Metadata hygiene: does generic summary avoid `Provider`, `Post ID`, `Content URL`, and checksum sections?
4. Memory separation: does extraction produce both user preference/goal memory and task-experience memory?
5. Session compression: does summarization retain goal-relevant turns and drop chatter?
6. Trace harness: can the selected node be re-opened through `/internal/traces/{traceId}/nodes/{nodeId}`?

## Current Gaps

- Retrieval is still heuristic. The current term alias and scoring path is useful enough for v1 dogfooding, but it is not a true hybrid retriever yet.
- Memory extraction is rule-based. It demonstrates the schema and channel split, but still lacks salience calibration, poisoning checks, and richer evidence for why a memory was written.
- The harness checks structural evidence and deterministic fallback text. Live DeepSeek/OpenAI dogfooding should stay separate because wording can change while the retrieval evidence stays correct.
- Negative/refusal behavior is not yet first-class in the harness. Add cases where evidence is thin and the expected result is refusal or a guarded answer.

## Optimization Direction

- Retrieval maturity v1: add BM25-like lexical scoring, section/title boosts, resource-scope filtering, and a reserved vector interface. Keep evidence traces stable before making ranking more complex.
- Memory maturity v1: add salience thresholds, explicit source references, deduplication, and safety filters for prompt injection or one-off user statements.
- Harness maturity v1: keep JSON cases as the source of truth, add refusal cases, add persisted trace regression checks after reindex, and add optional live-LLM rubric scoring that never replaces deterministic structural checks.
- Generation maturity v1: require answers to cite selected node paths or evidence labels, separate “insufficient evidence” from “short source article,” and record answer length only as a symptom, not a quality metric.

The near-term rule is simple: every retrieval or memory optimization should add one harness case before or with the code change.
