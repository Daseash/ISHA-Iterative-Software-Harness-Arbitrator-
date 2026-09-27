# 📘 ISHA — Comprehensive Whole-Project Architecture & File-by-File Guide

> **ISHA**: **I**terative **S**oftware **H**arness **A**rbitrator  
> An autonomous AI software engineering agent that diagnoses bug reports, performs pre-planning investigation, writes regression tests *first* (TDD Red-to-Green), patches across isolated Git worktrees, checks cross-file consistency, self-corrects against test feedback, and evaluates fixes with calibrated on-device probabilities (LAYA) before seeking human approval.

---

## Table of Contents
1. [Core Philosophy & Problems ISHA Solves](#1-core-philosophy--problems-isha-solves)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [The Complete Pipeline Dataflow](#3-the-complete-pipeline-dataflow)
4. [File-by-File Catalog & Deep Dive](#4-file-by-file-catalog--deep-dive)
   - [Root Project & Configuration Files](#root-project--configuration-files)
   - [Entry Points & Scripts (`scripts/`, `src/main.py`)](#entry-points--scripts)
   - [Agent State & Orchestration (`src/agents/`)](#agent-state--orchestration-srcagents)
   - [Codebase Understanding & Tooling (`src/tools/`)](#codebase-understanding--tooling-srctools)
   - [LAYA Evaluation & Arbitration (`src/review/`)](#laya-evaluation--arbitration-srcreview)
   - [Guardrails & Human Gate (`src/guardrails/`, `src/approval/`)](#guardrails--human-gate)
   - [Code Ingestion & Vector Retrieval (`src/ingestion/`, `src/rag/`)](#code-ingestion--vector-retrieval)
   - [Streamlit Dashboard (`src/dashboard/`)](#streamlit-dashboard-srcdashboard)
   - [Testing & SWE-bench Harness (`tests/`)](#testing--swe-bench-harness-tests)
5. [Key Design Decisions & Innovations](#5-key-design-decisions--innovations)
6. [How to Run Everything](#6-how-to-run-everything)

---

## 1. Core Philosophy & Problems ISHA Solves

Most AI coding agents generate patches in a single happy path on a toy file and stop there. This leads to three fundamental problems:
1. **The "Silent Regression" Problem**: A fix might make one test pass while quietly breaking callers across other files or introducing syntax/runtime regressions.
2. **The "Hallucinated Success" Problem**: A model claims a bug is fixed simply because no errors were thrown, even when the bug was never reproduced or tested.
3. **The "Subjective LLM-as-a-Judge" Problem**: Using standard LLMs to judge patches yields inconsistent, uncalibrated praise rather than rigorous mathematical confidence.

### How ISHA Fixes This:
- **TDD (Red-First Verification)**: ISHA must write a regression test that fails on the unmodified repo first. If the test doesn't fail before the fix, the bug was not reproduced.
- **AST Dependency Graph & Impact Analysis**: Understands the entire codebase as a call graph and import graph. Identifies blast radius, external callers, and affected test files.
- **Hierarchical Bug Decomposition**: Breaks big multi-file issues into atomic, ordered sub-issues that are solved sequentially.
- **Cross-File Consistency Checks**: Verifies that any function signature change in file A has its callers updated in files B and C.
- **Git Worktree Isolation**: Multiple agents exploring different patch strategies operate in isolated git worktrees, preventing file lock contention.
- **Calibrated LAYA Judgment**: Evaluates patches using typed choice/score calibrated probabilities instead of subjective text tokens.
- **Checkpointed Resumable Sessions**: Persists progress ledgers to disk so multi-step debugging can pause for human review and resume seamlessly.

---

## 2. End-to-End System Architecture

```
                       ┌────────────────────────────────────────┐
                       │          Bug Report / Issue            │
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │      Input Guardrail Security Scan     │  (Detect prompt injections)
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │   Pre-Planning Active Investigation    │  (Baseline tests, grep symbols,
                       └───────────────────┬────────────────────┘   full-file deep inspection)
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │      Hierarchical Bug Decomposer       │  (Split big bugs into atomic
                       └───────────────────┬────────────────────┘   ordered sub-issues)
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │        Planner (Gemini 3.1 Flash)       │  (Repo AST map + RAG chunks +
                       └───────────────────┬────────────────────┘   Dependency Graph blast radius)
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │       TDD Regression Test Writer       │  (Writes test that FAILS right now)
                       └───────────────────┬────────────────────┘
                                           │
                      ┌────────────────────┴────────────────────┐
                      │                                         │
                      ▼                                         ▼
            [ Single-Agent Mode ]                     [ Multi-Agent Mode ]
                      │                                         │
                      ▼                                         ▼
         Coder (Groq Qwen 3.8 27B)                 Dispatch 3 Parallel Strategies:
                      │                            - Strategy 1: Minimal Diff
                      ▼                            - Strategy 2: Call-site Aware
         Isolated Sandbox / Docker                 - Strategy 3: Alt-test Phrasing
                      │                                         │
                      ▼                                         ▼
         Self-Correction Loop                     Arbitration (LAYA Calibrated Scoring)
      (Retry coder up to 3x on FAIL)                            │
                      │                                         ▼
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │     Cross-File Consistency Check       │  (Detect unpatched callers via AST)
                       │     & Full Repo Regression Run         │  (Verify zero collateral damage)
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │     LAYA Decision Engine Evaluation    │  (fix_quality, safe_to_apply,
                       └───────────────────┬────────────────────┘   secrets_or_danger, composite)
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │       Human Approval Gate & Audit      │  (Flagged patches pause for human;
                       └───────────────────┬────────────────────┘   approved patches advance)
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │   Session Checkpoint & Progress Ledger │  (Persist state; advance next sub-issue)
                       └───────────────────┬────────────────────┘
                                           │
                                           ▼
                       ┌────────────────────────────────────────┐
                       │       Git Commit & Clean Merge         │  (Write patch, git commit, clean worktrees)
                       └────────────────────────────────────────┘
```

---

## 3. The Complete Pipeline Dataflow

1. **Input**: A bug description and target repo path enter the system.
2. **Security Scan**: `guardrails/scanner.py` runs regex and semantic checks to prevent prompt injections.
3. **Investigation**: `investigation.py` runs baseline tests on the clean repo, greps for keywords/symbols, loads full suspect files, and creates an `InvestigationReport`.
4. **Decomposition**: `decomposer.py` checks if the bug is complex or multi-component, breaking it into an ordered list of `SubIssue` items.
5. **Context Assembly**: `context.py` builds the prompt context combining:
   - AST class & function signature hierarchy (`ast_mapper.py`)
   - Call graph & Import graph blast radius (`dependency_graph.py`)
   - Qdrant hybrid vector search chunks (`rag/retriever.py`)
   - Investigation diagnostic report
6. **Plan**: `planner_node` generates a precise 2-step root cause analysis and action plan.
7. **Red Regression Test**: `regression_test_node` writes a pytest test that reproduces the bug (must fail before patching).
8. **Patching**: `coder_node` generates unified diffs using strategy hints.
9. **Sandboxing**:
   - `sandbox_node` creates an isolated directory copy or git worktree.
   - `consistency_checker.py` analyzes the diff against the AST to ensure call sites across the entire repository remain valid.
   - `patch_engine.py` applies the diff (via 3-way git apply or fallback hunk applier).
   - Pytest executes the regression test.
   - If regression test passes, pytest runs the full repo test suite to ensure no collateral breakage.
10. **Self-Correction**: If tests fail, the output is trimmed via `context_trimmer.py`, and the coder retries up to 3 times with the exact failure traceback and consistency warnings.
11. **Arbitration & Review**: `laya_judge.py` evaluates candidate patches on probability buckets (fix quality, match issue, safety, danger).
12. **Approval**: Dangerous or flagged patches pause for human review via `approval/gate.py`.
13. **Checkpoint**: `session_manager.py` saves snapshot state to `output/sessions/{session_id}.json`. If more sub-issues remain, the loop advances to the next sub-issue.

---

## 4. File-by-File Catalog & Deep Dive

### Root Project & Configuration Files

| File | Purpose |
|:---|:---|
| [`README.md`](file:///c:/Users/Eashwar/ISHA/isha-agent/README.md) | High-level project documentation, benchmarks, architecture diagrams, and quickstart commands. |
| [`LICENSE`](file:///c:/Users/Eashwar/ISHA/isha-agent/LICENSE) | Official open-source MIT License granting full usage and attribution rights. |
| [`.gitignore`](file:///c:/Users/Eashwar/ISHA/isha-agent/.gitignore) | Protects sensitive files: ignores `.env`, virtualenvs, `.pytest_cache`, `output/*.json`, `output/sessions/`, `.worktrees/`, and `swebench_checkouts/`. |
| [`.env.example`](file:///c:/Users/Eashwar/ISHA/isha-agent/.env.example) | Template configuration file listing optional environment variables (Gemini, Groq, Langfuse, Qdrant, LAYA paths). |
| [`requirements.txt`](file:///c:/Users/Eashwar/ISHA/isha-agent/requirements.txt) | Core Python dependencies: `langgraph`, `litellm`, `pydantic`, `tree-sitter`, `qdrant-client`, `streamlit`, `pytest`. |
| [`pytest.ini`](file:///c:/Users/Eashwar/ISHA/isha-agent/pytest.ini) | Pytest configuration registering custom markers (`slow`, `integration`, `laya`). |
| [`docker-compose.yml`](file:///c:/Users/Eashwar/ISHA/isha-agent/docker-compose.yml) | Compose specification for local services (e.g. Qdrant vector database). |
| [`sandbox.Dockerfile`](file:///c:/Users/Eashwar/ISHA/isha-agent/sandbox.Dockerfile) | Hardened container environment for executing candidate patches with CPU, memory, and network constraints. |
| [`sandbox-requirements.txt`](file:///c:/Users/Eashwar/ISHA/isha-agent/sandbox-requirements.txt) | Minimal packages required inside the container sandbox. |
| [`.dockerignore`](file:///c:/Users/Eashwar/ISHA/isha-agent/.dockerignore) | Excludes local virtual environments and caches from container build contexts. |

---

### Entry Points & Scripts

| File | Purpose |
|:---|:---|
| [`src/main.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/main.py) | Main command-line interface for ISHA. Supports single-agent, multi-agent (`--multi`), custom repo targets (`--repo`), and custom issues. |
| [`src/config.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/config.py) | Central model routing and fallback configuration. Defines the two-tier split: Gemini 3.1 Flash Lite for planning, Groq Qwen 3.8 27B for coding, with graceful fallback to deterministic offline brain. |
| [`scripts/demo.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/scripts/demo.py) | Interactive live demonstration script displaying colored progress bars, banner, step-by-step TDD outputs, and LAYA scores. |
| [`scripts/laya_demo.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/scripts/laya_demo.py) | Standalone showcase of the LAYA decision engine scoring 3 competing patches and selecting the calibrated winner. |
| [`scripts/run_dashboard.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/scripts/run_dashboard.py) | Convenience launcher script for running the Streamlit dashboard (`streamlit run scripts/run_dashboard.py`). |

---

### Agent State & Orchestration (`src/agents/`)

| File | Purpose |
|:---|:---|
| [`src/agents/state.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/state.py) | Defines `AgentState` using Pydantic v2. Uses last-write-wins reducers (`_last`) so parallel multi-agent branches can write state keys without `InvalidUpdateError`. |
| [`src/agents/graph.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/graph.py) | LangGraph topology definitions. Compiles both `compiled_graph` (single-agent with sub-issue loop) and `compiled_multi_graph` (parallel worktrees + arbitration). |
| [`src/agents/nodes.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/nodes.py) | Core node implementations: `planner_node`, `regression_test_node`, `coder_node`, and `sandbox_node`. |
| [`src/agents/investigation.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/investigation.py) | Dedicated pre-planning exploration node. Runs baseline tests before code modifications, greps for error symbols, and loads full suspect files. |
| [`src/agents/decomposer.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/decomposer.py) | Hierarchical bug decomposer. Splits complex or multi-file issues into ordered atomic `SubIssue` objects. |
| [`src/agents/session_manager.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/session_manager.py) | Manages long-running sessions, checkpointing snapshots to `output/sessions/{session_id}.json` with full progress ledgers and pause/resume capabilities. |
| [`src/agents/context.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/context.py) | Assembles the prompt context for the planner by combining the AST map, dependency blast radius, and vector search chunks. |
| [`src/agents/attempt.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/attempt.py) | Executes a single strategy attempt in an isolated worktree through the coder -> sandbox -> self-correct loop. |
| [`src/agents/dispatch.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/agents/dispatch.py) | LangGraph fan-out router: dispatches the planner output into 3 parallel strategy attempts using `Send` API. |

---

### Codebase Understanding & Tooling (`src/tools/`)

| File | Purpose |
|:---|:---|
| [`src/tools/dependency_graph.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/dependency_graph.py) | Extracts repo-level call graphs, reverse call graphs, import graphs, and reverse import graphs using Python AST. Calculates blast radius and impacted test suites. |
| [`src/tools/consistency_checker.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/consistency_checker.py) | Cross-file consistency checker. Analyzes diffs for changed function signatures and traverses the call graph to verify all external callers are updated. |
| [`src/tools/ast_mapper.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/ast_mapper.py) | Uses Tree-sitter / AST parsing to produce a compact, token-efficient map of class and function signatures without bodies. |
| [`src/tools/patch_engine.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/patch_engine.py) | Robust patch engine. Attempts `git apply --3way` first and falls back to a custom manual hunk applier for non-git environments. |
| [`src/tools/sandbox.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/sandbox.py) | Local isolated workspace runner. Creates scratch directory copies and executes pytest safely with timeouts. |
| [`src/tools/docker_sandbox.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/docker_sandbox.py) | Containerized sandbox runner. Mounts workspaces read-only/read-write into Docker containers with CPU and memory limits. |
| [`src/tools/git_manager.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/git_manager.py) | Git helper routines for checking repository status and committing verified fixes. |
| [`src/tools/worktree_manager.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/worktree_manager.py) | Manages git worktrees under `.worktrees/`. Provides clean worktree creation, isolation, and teardown for parallel agent branches. |
| [`src/tools/context_trimmer.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/context_trimmer.py) | Trims verbose Python tracebacks and error messages so self-correction prompts fit comfortably within LLM context windows. |
| [`src/tools/offline_brain.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/tools/offline_brain.py) | Deterministic offline mock engine providing valid plans and patches for testing without live LLM API keys. |

---

### LAYA Evaluation & Arbitration (`src/review/`)

| File | Purpose |
|:---|:---|
| [`src/review/laya_judge.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/review/laya_judge.py) | Interfaces with the local LAYA model (`agent.py`). Evaluates patches on 6 calibrated probability metrics: `fix_quality`, `matches_issue`, `safe_to_apply`, `secrets_or_danger`, `logic_drift`, and `composite`. Thread-safe inference lock. |
| [`src/review/critic.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/review/critic.py) | The critic graph node. Takes the generated patch and test outputs, calls LAYA, and sets the critic verdict (`approved`, `flagged`, or `low_quality`). |
| [`src/review/arbitration.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/review/arbitration.py) | Collects results from the 3 parallel strategy attempts, scores them with LAYA, and crowns the winning patch. |

---

### Guardrails & Human Gate

| File | Purpose |
|:---|:---|
| [`src/guardrails/scanner.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/guardrails/scanner.py) | Two-phase security scanner. Checks input issues for prompt injection and checks candidate patch diffs for leaked API keys, tokens, or private secrets. |
| [`src/guardrails/rails.co`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/guardrails/rails.co) | NeMo Guardrails policy definitions and conversational safety rails. |
| [`src/approval/gate.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/approval/gate.py) | Human-in-the-loop approval gate. Flagged or dangerous diffs pause execution; records an immutable audit log to `output/approvals.jsonl`. |

---

### Code Ingestion & Vector Retrieval

| File | Purpose |
|:---|:---|
| [`src/ingestion/parser.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/ingestion/parser.py) | Walks codebases and chunks Python files into AST function/class snippets with file metadata and line ranges. |
| [`src/rag/indexer.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/rag/indexer.py) | Indexes code chunks into Qdrant vector storage (or local in-memory fallback) with dense embeddings and payload filters. |
| [`src/rag/retriever.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/rag/retriever.py) | Performs hybrid semantic + keyword search over indexed code chunks to retrieve the top relevant code snippets. |

---

### Streamlit Dashboard (`src/dashboard/`)

| File | Purpose |
|:---|:---|
| [`src/dashboard/app.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/src/dashboard/app.py) | Full-featured web dashboard with 4 tabs: **Run** (launch fixes & live graph execution), **Diff** (syntax-highlighted patch review), **Telemetry** (LAYA score bars & latency metrics), and **Approvals** (human review queue). |

---

### Testing & SWE-bench Harness (`tests/`)

| File | Purpose |
|:---|:---|
| [`tests/dummy_repo/calculator.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/dummy_repo/calculator.py) | Controlled benchmark repository containing seeded bugs: `subtract()` returns `a + b`, and `divide()` lacks a zero-division guard. |
| [`tests/dummy_repo/test_calculator.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/dummy_repo/test_calculator.py) | Test suite for the calculator module. |
| [`tests/eval_suite.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/eval_suite.py) | Automated eval suite running ISHA against all seeded bugs, outputting pass rates and LAYA score tables. |
| [`tests/swebench_runner.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/swebench_runner.py) | Evaluates LAYA and ISHA against SWE-bench Lite instances. Tests golden patches against 3 negative controls (inverted patch, unrelated patch, dangerous patch). |
| [`tests/prepare_swebench.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/prepare_swebench.py) | Clones and prepares SWE-bench repository checkouts for local evaluation. |
| [`tests/test_v2_capabilities.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/test_v2_capabilities.py) | Comprehensive test suite covering the 5 v2 capabilities (dependency graph, decomposition, session manager, investigation, consistency checker). |
| [`tests/test_docker_sandbox.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/test_docker_sandbox.py) | Unit tests verifying container isolation, volume mounts, resource limits, and fallbacks in the Docker sandbox. |
| [`tests/test_context_trimmer.py`](file:///c:/Users/Eashwar/ISHA/isha-agent/tests/test_context_trimmer.py) | Unit tests verifying traceback compaction and prompt token minimization. |

---

## 5. Key Design Decisions & Innovations

1. **Two-Tier LLM Architecture**:
   - High-reasoning model (Gemini 3.1 Flash Lite) is used for planning, AST digestion, and hierarchical decomposition where broad context is paramount.
   - High-throughput model (Groq Qwen 3.8 27B) is used for the coder self-correction loop where sub-second latency is critical for interactive iteration.
2. **True Git Worktree Isolation**:
   - Rather than mocking files or risking multi-agent file collisions, each agent branch operates in a dedicated, isolated Git worktree (`git worktree add`).
3. **Calibrated Decision Probabilities**:
   - Instead of asking an LLM "Does this patch look good? (Yes/No)", LAYA evaluates patches by projecting logits across calibrated probability buckets. A patch is only approved if confidence meets mathematical thresholds.
4. **AST-Driven Blast Radius vs Raw Chunks**:
   - Raw vector embeddings cannot see callers. ISHA's dependency graph traverses reverse call hierarchies to discover every function and test file that touches the bug site.
5. **Human Gate with Audit Trails**:
   - Safe patches with high LAYA confidence proceed autonomously; suspicious or dangerous patches trigger an approval interrupt and log immutable records to `output/approvals.jsonl`.

---

## 6. How to Run Everything

### Run the Live Demo:
```bash
python scripts/demo.py               # Single-agent autonomous fix with live output
python scripts/demo.py --multi       # Multi-agent (3 parallel worktree strategies)
```

### Run the LAYA Decision Showcase:
```bash
python scripts/laya_demo.py          # Standalone LAYA arbitration showcase
```

### Launch the Streamlit Dashboard:
```bash
streamlit run scripts/run_dashboard.py
```

### Run the Entire Test Suite:
```bash
python -m pytest tests/test_context_trimmer.py tests/test_docker_sandbox.py tests/test_v2_capabilities.py -v
```

### Run the Eval Suite:
```bash
python tests/eval_suite.py
```
