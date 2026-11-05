# 03 · Architecture & Data Flow — the file you read before writing/extending ISHA

## Top-level components

```
                    ┌──────────────────────────────────────────────┐
  bug report ──────►│  CLI (src/main.py)  or  Dashboard (src/dashboard/app.py) │
                    └───────────────┬──────────────────────────────┘
                                    │ AgentState
                    ┌───────────────▼──────────────────────────────┐
                    │  LangGraph state machine (src/agents/graph.py)│
                    │  planner → regression_test → coder → sandbox  │
                    │           ⇄ critic → approval → merger        │
                    └───┬───────────────┬────────────────┬──────────┘
                        │               │                │
              ┌─────────▼───┐   ┌───────▼────────┐  ┌────▼─────────────┐
              │ RAG / AST   │   │ Tools          │  │ Judgment          │
              │ ingestion   │   │ patch, sandbox,│  │ LAYA judge        │
              │ parser      │   │ worktrees, git │  │ critic/arbitration│
              │ ast_mapper  │   │ offline brain  │  │ guardrails        │
              │ rag/*       │   └────────────────┘  │ approval gate     │
              └─────────────┘                       └──────────────────┘
```

## Single-agent graph (Phase 5) — `build_graph()` in `src/agents/graph.py:34`

```
START → planner → regression_test → coder → sandbox ──┬─(FAILED & budget)→ coder  (retry)
                                                      └─(else)→ critic → approval → END
```

| Node | File | Reads | Writes |
|---|---|---|---|
| `planner_node` | `nodes.py:48` | `issue_text`, `repo_context` | `plan` |
| `regression_test_node` | `nodes.py` | `issue_text`, `plan` | `regression_test` |
| `coder_node` | `nodes.py` | `plan`, `patch`, `test_output`, `retry_count` | `patch`, `retry_count+1` |
| `sandbox_node` | `nodes.py:168` | `patch`, `repo_path` | `test_output` (`PASSED`/`FAILED`) |
| `critic_node` | `review/critic.py` | `patch`, `issue_text` | `critic_verdict`, `critic_score`, `laya_scores` |
| `approval_node` | `approval/gate.py` | verdict, patch, guardrail scan | `approved` |

Retry policy: `_route_after_sandbox()` (`graph.py:26`) — retry while
`"FAILED" in test_output` **and** `retry_count < MAX_RETRIES (3)`.

## Multi-agent graph (Phase 6) — `build_multi_agent_graph()` in `src/agents/graph.py`

```
START → planner → regression_test ──Send──► attempt1 ┐
                                  ├──────► attempt2 ├──► arbitration → approval → merger → END
                                  └──────► attempt3 ┘
```

- `dispatch.py` returns `Send(f"attempt{i}", payload)` — payload carries that branch's
  `strategy` + `worktree`.
- `attempt.py:attempt_node` runs the **entire** coder→sandbox→(retry)→critic chain
  *inside one node*, so branch-local fields never leak into shared state channels.
- Each attempt writes to a thread-safe ledger (`review/arbitration.py:record_attempt`).
- `arbitration_node` drains the ledger, ranks by LAYA composite, and writes back the
  winner's `patch`/`verdict`/`scores`.
- `merger_node` applies the winner (only with `--apply`, only if tests passed and the
  verdict cleared) and cleans up worktrees.

> **Hard-won LangGraph lessons** (worth quoting if asked "what broke?"):
> 1. Shared node names collapse parallel `Send`s — hence per-branch `attempt1..3`.
> 2. Concurrent writes to one field raise `InvalidUpdateError` — hence `_last` reducers
>    on every `AgentState` field.
> 3. `Send` payloads arrive as dicts — hence `coerce_state()` at every node.
> 4. Long loops inside one node keep branch state isolated (see `attempt.py`).

## Cross-cutting flows

**Repo → context**: `RepoParser.parse()` → chunks → `QdrantIndexer.index()` →
`CodeRetriever.search()` → `build_repo_context()` → planner prompt.
Two degradation points: Qdrant unreachable → `mode: "local"` lexical ranking
(`retriever.py:32`); no keys → `offline_brain` (`config.py:74`).

**Patch → verdict**: `patch_engine.apply_patch()` (tries `git apply --3way`, falls back
to a built-in hunk applier) → `sandbox.run_tests()` → trim → critic → LAYA → guardrail
scanner → approval → merger.

**Observability**: node `print`s are captured by the dashboard's `redirect_stdout`;
decisions land in `approvals.jsonl`; optional Langfuse tracing via `ISHA_LITELLM_LANGFUSE=1`.

## Execution modes

| Command | What runs |
|---|---|
| `python src/main.py` | single-agent graph, offline/live brain |
| `python src/main.py --multi` | fan-out graph, 3 worktrees, arbitration |
| `python src/main.py --apply` | writes patch to the real repo (+ git commit if `.git` exists) |
| `python src/main.py --approve cli` | prompts y/N on flagged diffs |
| `python laya_pipeline.py [--live]` | standalone LAYA scoring demo (no graph) |
| `python tests/eval_suite.py` | 3 bug cases → `eval_results.json` |
| `python tests/swebench_runner.py --mode judge\|full` | benchmark → `results.json` |
| `streamlit run src/dashboard/app.py` | 4-tab UI: Run / Diff / Telemetry / Approvals |
| `python -m pytest tests/` | unit tests for the platform |
