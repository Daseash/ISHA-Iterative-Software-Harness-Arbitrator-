# 🤖 ISHA — Autonomous AI Software Engineering Agent

> An autonomous SWE agent that reads a bug report, plans a fix, writes a regression
> test *first*, patches in an isolated git worktree, self-corrects against failing
> tests, and is judged by a calibrated on-device decision engine before a human
> approves the commit.

**[▶ Live Demo](#live-demo)** · **[Results](#results)** · **[Architecture](#architecture)** · **[Quickstart](#quickstart)**

```
Bug report → Guardrail scan → Plan → Regression test (RED) → Patch
→ Sandbox → Self-correct loop → LAYA verdict → Approval gate → Commit ✅
```

---

## The Problem

Most "AI coding agent" demos show a single happy-path fix on a toy repo and stop
there: no proof the bug was ever real, no proof the patch did what the report asked,
and no way to compare the result against anything anyone else published. A fix that
merely makes an existing suite go green can still be wrong — it can hard-code the
test, touch unrelated code, or never address the reported behaviour at all.

ISHA builds out the parts that make autonomous fixes *trustworthy* instead: a
regression test that must fail **before** the patch and pass after it; three
independent attempts generated in parallel by different strategies and arbitrated;
a LAYA decision engine scoring every patch as calibrated probabilities rather than
free-text opinions; guardrails that scan diffs for secrets and prompt injection; and
a human approval gate with a JSONL audit trail. The whole loop is measured against
SWE-bench Lite rather than claimed anecdotally.

## Results

**Eval suite — `python tests/eval_suite.py`** (3 seeded bugs in the bundled
calculator fixture, offline deterministic brain + LAYA judge):

| Metric | Value |
|:---|:---|
| Bugs resolved (target tests go green) | **3 / 3 (100%)** |
| Mean LAYA composite score | `0.714` |
| Mean self-correction retries | `0.0` |
| Mean end-to-end latency per bug | `10.4s` |

**SWE-bench Lite — `python tests/swebench_runner.py --limit 3`** (judge mode: LAYA
scores the golden patch against three injected negative controls; bundled 3-instance
sample of `princeton-nlp/SWE-bench_Lite`, no network or container images needed):

| Metric | Value |
|:---|:---|
| Golden patch approved | **67%** |
| Inverted (anti-fix) rejected | 33% |
| Unrelated-change patch rejected | **67%** |
| Dangerous patch (`eval` / `os.system`) flagged | **100%** |
| All four judgments correct | 33% |

> **Honest caveats, stated up front.** The full *generation* benchmark
> (`--mode full --repo-root …`) needs per-instance checkouts and valid LLM keys —
> both are unavailable in this environment, so those runs are recorded as skips in
> `results.json` rather than silently scored as failures. LAYA is a small typed-choice
> model: it is excellent at lexical danger detection (100%) and weaker on subtle
> numerical fixes in large third-party diffs (67% golden approval). Those numbers are
> reported as measured, not rounded up.

**Single run** (`python src/main.py`): plan → regression test → patch → sandbox →
LAYA verdict in ~10s per attempt, `~$0.00` per run on the free tiers / offline brain.

## Live Demo

```bash
# Terminal demo — full pipeline with rich output (no API keys needed)
python scripts/demo.py
python scripts/demo.py --bug divide
python scripts/demo.py --bug subtract --multi

# LAYA decision engine demo — scores 3 candidate patches
python scripts/laya_demo.py

# Streamlit dashboard — interactive UI with 4 tabs
streamlit run src/dashboard/app.py
```

Four dashboard tabs: **Run** (fire the graph, watch the transcript, approve flagged
diffs), **Diff** (plan, regression test, patch + guardrail scan), **Telemetry** (LAYA
score bars, attempt ledger, latency), **Approvals** (exportable audit trail).

## Architecture

```
Bug report ──► Guardrail scan ──► Investigation (baseline tests, grep, full files)
     ──► Decomposer (hierarchical sub-issues)
     ──► Plan (AST map + Dependency Graph blast radius)
     ──► Regression test written FIRST (must be RED)
     ──► Dispatch ──► [ attempt 1 │ attempt 2 │ attempt 3 ]   (3 git worktrees,
     │              │  coder → sandbox → self-correct → critic │  3 strategies)
     └──────────────► Arbitration (LAYA composite ranks the attempts)
                      ──► Approval gate (flagged diffs pause for a human)
                      ──► Cross-file consistency & full regression check
                      ──► Checkpoint session ledger ──► Merge winner → Commit ✅
```

### Advanced Repo-Level Engineering (v2 Capabilities)

1. **Dependency Graph & Impact Analysis (`src/tools/dependency_graph.py`)**:
   Constructs repo-level call graphs and import graphs from AST parsing. Computes blast radius, upstream callers, dependent modules, and impacted test suites for target bug entry points.
2. **Hierarchical Bug Decomposition (`src/agents/decomposer.py`)**:
   Decomposes complex multi-file bugs into an ordered sequence of atomic sub-issues. Solves each sub-issue sequentially, passing intermediate patches as context.
3. **Checkpointed & Resumable Sessions (`src/agents/session_manager.py`)**:
   Persists progress snapshots to `output/sessions/{session_id}.json`. Allows sessions to pause on human review or retry budget limits, and resume without losing state.
4. **Active Pre-Planning Investigation (`src/agents/investigation.py`)**:
   Runs baseline tests before touching any code, greps for error symbols, and inspects full suspect source files to give the planner diagnostic proof.
5. **Cross-File Consistency & Collateral Regression Checks (`src/tools/consistency_checker.py`)**:
   Validates changed function signatures across all external callers using the dependency graph. Runs the entire repository test suite to catch collateral regressions.

Full diagram: [`docs/flow-diagram.txt`](docs/flow-diagram.txt) ·
Component table: [`docs/components.md`](docs/components.md)

## Design Decisions

- **Git worktrees for multi-agent isolation** — N agents sharing one checkout silently
  overwrite each other. Each attempt gets its own worktree (plain directory copy for
  non-git targets), so parallel strategies can edit and test without contention.
- **Two-tier model split (Gemini planning, Groq patching)** — Gemini's long context
  digests the whole repo map into a plan; Groq's speed keeps the test-fail-retry loop
  responsive. Both are routed through `litellm` so swapping providers is one env var.
- **LAYA for calibrated judgment, not text heuristics** — every verdict (patch quality,
  danger, arbitration, final verification) is a typed `choice`/`score`/`noul` question
  answered with on-device probabilities, serialised behind one inference lock so
  parallel branches share a single model instance.
- **Regression test before patch** — the agent must first *prove* the bug exists in a
  scratch sandbox; success means that RED test goes GREEN while the rest of the suite
  stays honest, not merely that nothing new broke.

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-state%20machine-1C3C3C?style=flat-square)
![LiteLLM](https://img.shields.io/badge/LiteLLM-multi%20provider-FF6B4A?style=flat-square)
![LAYA](https://img.shields.io/badge/LAYA-judgment%20engine-7C3AED?style=flat-square)
![Qdrant](https://img.shields.io/badge/Qdrant-RAG-D5B60A?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?style=flat-square)
![MIT](https://img.shields.io/badge/license-MIT-green?style=flat-square)

`langgraph` · `litellm` · Gemini 3.1 Flash Lite · Groq Qwen 3.8 27B · **LAYA decision
engine** · Qdrant (hybrid retrieval) · `tree-sitter` · `pytest` · `pydantic` v2 ·
`nemoguardrails` config · Langfuse · Streamlit

## Quickstart

```bash
git clone <your-repo-url> && cd isha-agent
pip install -r requirements.txt
cp .env.example .env            # optional — every key is optional
python scripts/demo.py          # full live demo (no keys needed)
streamlit run src/dashboard/app.py
```

Other entry points:

```bash
python src/main.py              # single-agent CLI
python src/main.py --multi      # 3 strategies in parallel worktrees
python scripts/laya_demo.py     # standalone LAYA scoring demo
python tests/eval_suite.py      # 3 seeded bugs → output/eval_results.json
python tests/swebench_runner.py # SWE-bench Lite → output/results.json
```

## LAYA Integration

Every judgment point is a **typed question** answered by LAYA's calibrated decision
engine (single forward pass, no text generation, no parsing):

| Point | Questions | Type |
|:---|:---|:---|
| Patch scoring | `fix_quality` | `score` (0–2) |
| Patch scoring | `matches_issue`, `safe_to_apply` | `noul` (0–1) |
| Danger check | `secrets_or_danger`, `logic_drift` | `noul` |
| Arbitration | composite `0.5·quality + 0.25·match + 0.25·safety` | ranking |
| Final verification | `looks_correct` → P(correct) ≥ 0.60 | `noul` |

Guardrails run *alongside* the model: a regex scanner for secrets/`eval`/`os.system`
and prompt-injection patterns, a NeMo-rails config in `src/guardrails/rails.co`, and a
human gate that logs every decision to `output/approvals.jsonl`.

## Repo Layout

```
isha-agent/
├── src/                        # Core source code
│   ├── agents/                 #   State, nodes, graph, dispatch, attempt
│   ├── approval/               #   Human gate + JSONL audit trail
│   ├── guardrails/             #   Regex scanner + NeMo rails config
│   ├── ingestion/              #   Repo parser + chunker
│   ├── rag/                    #   Qdrant indexer + retriever (local fallback)
│   ├── review/                 #   LAYA judge, critic, arbitration
│   ├── tools/                  #   Patch engine, sandbox, worktrees, git, AST mapper
│   ├── dashboard/              #   Streamlit app (4 tabs)
│   ├── config.py               #   Model routing + API setup
│   └── main.py                 #   CLI entry point
├── scripts/                    # Runnable scripts & demos
│   ├── demo.py                 #   Full live demo (terminal)
│   ├── laya_demo.py            #   LAYA scoring demo
│   └── run_dashboard.py        #   Dashboard launcher
├── tests/                      # Tests & benchmarks
│   ├── dummy_repo/             #   Seeded calculator bugs for eval
│   ├── fixtures/               #   SWE-bench sample data
│   ├── eval_suite.py           #   3-bug evaluation harness
│   ├── swebench_runner.py      #   SWE-bench Lite benchmark
│   └── test_context_trimmer.py #   Unit tests
├── docs/                       # Documentation
│   ├── guide/                  #   6-chapter learning guide
│   ├── components.md           #   Component reference
│   └── flow-diagram.txt        #   Full pipeline diagram
├── output/                     # Runtime artifacts (gitignored)
│   ├── approvals.jsonl         #   Approval audit trail
│   ├── eval_results.json       #   Eval suite output
│   └── results.json            #   SWE-bench results
├── requirements.txt
├── docker-compose.yml          # Qdrant vector DB
├── .env.example
├── pytest.ini
└── LICENSE (MIT)
```

## Planned Next Steps

Scoped out deliberately — not built, not forgotten:

- Containerised SWE-bench evaluation (`--mode full` with per-instance checkouts and
  the official FAIL_TO_PASS runner) for a directly comparable resolution rate
- Multi-language support beyond Python
- Real Docker sandbox instead of directory-copy sandboxes
- CI covering the platform's own code, not just the target repo's tests
- Cost/latency dashboard backed by Langfuse traces

## License

MIT — see [`LICENSE`](LICENSE).
