# 02 · What an AI Agent Is — and exactly where ISHA implements each part

> Interview definition to memorise:
> **An AI agent is a system where a model decides a sequence of actions towards a goal,
> executes them against tools/environment, observes the results, and iterates using
> feedback — rather than just returning a single text response.**

---

## The canonical agent loop

```
        ┌─────────────────────────────────────────────┐
        │  GOAL (bug report)                          │
        ▼                                             │
   PLAN  ──► ACT (tool / code edit) ──► OBSERVE (env) │
        ▲                                             │
        └──────────── FEEDBACK (tests, critic) ───────┘
                 (repeat until done or budget exhausted)
```

Four ingredients separate an *agent* from a *prompt*:

| Ingredient | Meaning | ISHA implementation (file) |
|---|---|---|
| **Goal** | A concrete objective, not a conversation | `issue_text` field in `src/agents/state.py` |
| **Reasoning/Planning** | Model decomposes the goal | `planner_node` → `call_planner()` (`src/agents/nodes.py`, `src/config.py:72`) |
| **Tools / Action** | Effects on the real world (code, tests, git) | `sandbox.py`, `patch_engine.py`, `git_manager.py`, `worktree_manager.py` |
| **Feedback / Memory** | Results feed back into the next decision | pytest output → trimmed traceback → retry; LAYA verdict → arbitration; LangGraph checkpoints |

Plus two things real agents need beyond the textbook loop:
- **Guardrails** — what the agent is *not* allowed to do (`src/guardrails/`, `src/approval/`).
- **Isolation** — parallel attempts must not corrupt each other (`src/tools/worktree_manager.py`).

---

## ISHA's loop, node by node

### 1. State = the agent's memory (`src/agents/state.py:22`)
A single `AgentState` pydantic model carries everything: `issue_text`, `repo_path`,
`repo_context`, `plan`, `regression_test`, `patch`, `test_output`, `retry_count`,
`critic_verdict`, `critic_score`, `approved`, `worktree`, `strategy`, `laya_scores`.

Two design points worth naming in an interview:
- **Every field has a reducer** (`Annotated[..., _last]`) because parallel branches write
  concurrently — LangGraph raises `InvalidUpdateError` on concurrent writes without one.
- **`coerce_state()`** normalises dict→model at every node boundary, because a `Send()`
  payload arrives as a plain dict.

### 2. Perception = repo ingestion (`src/ingestion/`, `src/tools/ast_mapper.py`)
- `RepoParser` walks the tree and chunks files into retrievable units.
- `ASTMapper` uses **tree-sitter** (with a regex fallback) to build a compact
  `file → class → method` map — this is what lets the planner see structure without
  burning tokens on full file contents.
- `build_repo_context()` (`src/agents/context.py`) fuses the AST map with RAG snippets
  into a ≤4000-char planner prompt.

### 3. Planning (`src/agents/nodes.py` → `planner_node`)
A 2-step root-cause plan: *"what is wrong"* + *"exactly which edit to make"*.
Live model: `gemini/gemini-3.1-flash-lite` with a Groq fallback chain
(`src/config.py:24-39`).

### 4. Prove-before-patch (`regression_test_node`)
The agent must write a test that **fails on the current code**. This is the difference
between "fixed the bug" and "made a test pass".

### 5. Action + feedback loop (`coder_node` → `sandbox_node`)
- `coder_node` emits a unified diff; increments `retry_count` when the previous
  `test_output` contains `FAILED`.
- `sandbox_node` copies the repo (`copy_repo` / git worktree), applies the patch **there**,
  runs pytest, and returns `PASSED`/`FAILED` output. The real repo is never mutated.
- `context_trimmer.trim_traceback()` keeps only the relevant lines so the retry prompt
  stays small — **context management** is a core agent skill.
- Loop is bounded: `MAX_RETRIES = 3` (`src/agents/graph.py:23`). Unbounded retries burn
  tokens and never change strategy.

### 6. Judgment (`src/review/critic.py` + `laya_judge.py`)
Instead of asking an LLM "is this good?", ISHA asks a **typed question** and gets a
calibrated probability back (single forward pass, no text generation to parse):

| Point | Question | Type |
|---|---|---|
| Patch quality | `fix_quality` | `score` (0–2) |
| Relevance | `matches_issue` | `noul` (0–1) |
| Safety | `safe_to_apply` | `noul` |
| Danger | `secrets_or_danger`, `logic_drift` | `noul` |
| Verdict | composite = `0.5·quality + 0.25·match + 0.25·safe` | ranking |
| Final check | `looks_correct` → P ≥ 0.60 | `noul` |

### 7. Parallelism & arbitration (`dispatch.py`, `attempt.py`, `arbitration.py`)
Three strategies (`minimal_diff`, `call_site_aware`, `alt_test_phrasing`) each run their
own full attempt in an isolated worktree, record results in a thread-safe ledger, and
`arbitration_node` picks the highest composite. **Fan-out/fan-in**, not a chain.

### 8. Human-in-the-loop (`src/approval/gate.py`)
Flagged diffs stop. Three modes: `auto` (log it), `cli` (prompt `y/N`), `interrupt`
(LangGraph interrupt → dashboard Approve/Reject button). Every decision appended to
`approvals.jsonl`.

### 9. Safety (`src/guardrails/`)
- Regex scanner for AWS/GitHub/OpenAI keys, private keys, `eval`, `exec`, `os.system`,
  `shell=True`, `rm -rf`, plus prompt-injection phrasing (`scanner.py`).
- NeMo-rails config file for conversational input/output rails (`rails.co`).

---

## Agent-design concepts you should be able to name

| Concept | Where it is in ISHA |
|---|---|
| ReAct-style reason→act→observe | `graph.py` cycle: coder → sandbox → (retry coder) |
| Tool use | pytest, git apply, worktrees, git commit |
| Short-term memory | `AgentState` |
| Long-term/persistent memory | LangGraph `MemorySaver` checkpoints (thread ids) |
| Reflection / self-critique | `critic_node` + retry loop |
| Multi-agent (parallel peers) | `dispatch.py` → `attempt1..3` |
| Multi-agent (sequential roles) | planner → coder → sandbox → critic |
| Arbitration / best-of-n | `arbitration.py` |
| Human-in-the-loop | `approval/gate.py` + `interrupt()` |
| Guardrails | `guardrails/scanner.py`, `rails.co` |
| Bounded autonomy | `MAX_RETRIES`, approval gate, `--apply` opt-in |
| Deterministic degradation | `offline_brain.py` fallback when LLM/Qdrant unavailable |
| Evaluation harness | `tests/eval_suite.py`, `tests/swebench_runner.py` |
