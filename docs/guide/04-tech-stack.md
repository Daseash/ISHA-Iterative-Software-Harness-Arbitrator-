# 04 · Tech Stack Deep-Dive — what each piece is, why it's here, where it's used

> Rule for interviews: never list a technology without being able say **why this one**
> and **where it sits in my code**.

## Orchestration & state

| Tech | What it is | Why ISHA uses it | Where |
|---|---|---|---|
| **LangGraph** | Library for building cyclic state machines over LLM steps, with checkpoints and parallel `Send`s | The agent loop is a *graph with retries and fan-out*, not a linear chain. Gives checkpointing (thread ids), conditional edges, interrupts | `src/agents/graph.py`, `attempt.py`, `dispatch.py` |
| **LangGraph `MemorySaver`** | In-memory checkpointer | Resumable runs; the dashboard's approval resume uses it | `graph.py` compile |
| **`interrupt()` / `Command(resume=…)`** | Human-in-the-loop primitive | Pauses the graph mid-run for approval, resumes with a decision | `approval/gate.py:70`, dashboard |
| **pydantic v2** | Typed data models | One strict schema for all state; invalid states become errors early | `src/agents/state.py` |

## Models & gateway

| Tech | What it is | Why | Where |
|---|---|---|---|
| **LiteLLM** | One API for 100+ providers | Swap Gemini↔Groq↔local with env vars, no code change; unified retry/fallbacks | `src/config.py` |
| **Gemini (3.1 flash-lite)** | Long-context planning model | Big context for repo maps; free tier | `PLANNER_MODEL`, `call_planner()` |
| **Groq (qwen3.8-27b)** | Ultra-fast inference API | Keeps the fail→retry loop sub-second | `CODER_MODEL`, `call_coder()` |
| **Deterministic offline brain** | Rule-based planner/coder regressor | Zero-key demos/CI; pipeline never hard-fails | `src/tools/offline_brain.py` (266 lines) |
| **`python-dotenv`** | Loads `.env` into env vars | Secrets never in code; `.env` gitignored, `.env.example` is the template | `config.py:18` |

## Judgment (the differentiator)

| Tech | What it is | Why | Where |
|---|---|---|---|
| **LAYA** | On-device decision engine: typed `choice`/`score`/`noul` questions answered with calibrated probabilities in one forward pass | Free-text LLM opinions are uncalibrated and expensive to re-parse; a probability is directly comparable across candidates | `src/review/laya_judge.py` |
| Composite scoring | `0.5·quality + 0.25·match + 0.25·safety` | Rankable, thresholdable (`< 0.4` → `low_quality`) | `laya_judge.py:89` |
| Serialized inference | one `_INFER_LOCK` | 3 parallel branches share one model instance | `laya_judge.py:70` |

## Code understanding & retrieval

| Tech | What it is | Why | Where |
|---|---|---|---|
| **tree-sitter** | Incremental parser library with grammar files | Real ASTs instead of regex guesses; fast, error-tolerant | `src/tools/ast_mapper.py` |
| **Qdrant** | Vector database (dense + payload filters) | Hybrid semantic search over code chunks | `src/rag/indexer.py`, `retriever.py` |
| **Hashing embedder (384-d)** | Bag-of-tokens → signed hashing vector | Dependency-free, deterministic, works offline | `indexer.py:22` |
| **Lexical fallback** | token overlap ×0.7 + cosine ×0.3 | Same code path works with no server running | `retriever.py:56` |

## Execution & safety

| Tech | What it is | Why | Where |
|---|---|---|---|
| **pytest** | De-facto Python test runner | Objective RED/GREEN signal for the retry loop | `sandbox.py:86` |
| **Sandbox = temp dir copy** | Isolated copy per attempt | Agent edits never touch the real repo | `sandbox.py:38` |
| **Docker sandbox (opt-in)** | pytest in a throwaway container (`ISHA_SANDBOX_MODE=docker`) | Host-independent deps, `--network none`, memory/CPU caps; silent fallback to local | `docker_sandbox.py` |
| **git worktrees** | Multiple working dirs on one repo | 3 parallel agents, one object store, no clobbering | `worktree_manager.py` (non-git → directory copy) |
| **`git apply --3way`** | Applies diffs with context recovery | Real patch semantics; built-in hunk applier as fallback | `patch_engine.py` |
| **Regex guardrails** | Secret + dangerous-call + injection patterns | Deterministic safety that no model judgment should override | `guardrails/scanner.py` |
| **NeMo Guardrails `.co`** | NVIDIA's rail DSL (input/output/dialog rails) | Conversational rails for the dashboard path | `guardrails/rails.co` |
| **Approval gate + JSONL audit** | Human sign-off, append-only log | Bounded autonomy; every decision attributable | `approval/gate.py` |

## Product & evaluation

| Tech | What it is | Why | Where |
|---|---|---|---|
| **Streamlit** | Python web UI in one file | 4-tab ops console without a frontend stack | `src/dashboard/app.py` |
| **Langfuse** | LLM observability (traces, cost, latency) | Production visibility; currently keys valid, tracing toggle `ISHA_LITELLM_LANGFUSE=1` | `config.py:46` |
| **SWE-bench Lite** | Princeton benchmark of real GitHub issues | Credible, comparable numbers instead of self-reported claims | `tests/swebench_runner.py` |
| **pytest + eval harness** | Own fixtures | Regression signal for the platform itself | `tests/eval_suite.py`, `pytest.ini` |

## Deliberate omissions (say these out loud if asked "what's missing")

- **Docker sandbox** — built and opt-in (`ISHA_SANDBOX_MODE=docker`), but not yet the
  default; the default test path is still directory copies on the host.
- **Real Qdrant** — running in local lexical mode until a server/cloud key is added.
- **Containerised SWE-bench scoring** — runner does judge mode + patch-overlap mode;
  full FAIL_TO_PASS execution needs per-instance checkouts.
- **Job queue / multi-tenant concurrency** — single-user by design today.
