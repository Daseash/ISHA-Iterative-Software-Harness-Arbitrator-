# 🏛️ ISHA Architecture & Project Directory Structure

> **Purpose**: A clear, comprehensive guide for any developer to understand the codebase layout, module boundaries, and workflow without confusion or hallucination.

---

## 📂 Project Directory Map

```text
isha-agent/
├── src/                          # Core ISHA Agent Implementation
│   ├── agents/                   # Autonomous Agent Execution Engine
│   │   ├── graph.py              # Main LangGraph cyclic state machine
│   │   ├── nodes.py              # Graph nodes (Localizer, Planner, Coder, Verifier)
│   │   ├── candidates.py         # Multi-candidate generation & tournament arbitration
│   │   ├── state.py              # Strongly-typed AgentState schemas (Pydantic v2)
│   │   ├── dispatch.py           # Multi-worker parallel session runner
│   │   └── fix_history.py        # Vectorized memory of successful bug patterns
│   │
│   ├── approval/                 # LAYA Calibrated Decision Engine
│   │   ├── gate.py               # Temperature-scaled decision gate (ECE 0.0010)
│   │   ├── calibrator.py         # Empirical Platt & temperature scaling
│   │   └── danger.py             # Safety & dangerous pattern detectors
│   │
│   ├── bench/                    # SWE-bench Benchmark & Validation Harness
│   │   ├── harness_eval.py       # Official SWE-bench Docker testbed wrapper
│   │   ├── runner.py             # Batch session runner across benchmark slices
│   │   ├── gates.py              # Static compiler, syntax, and git-apply gates
│   │   ├── dataset.py            # Dataset loading and instance slice partitioning
│   │   ├── classify.py           # Diagnostic classification of container failures
│   │   └── report.py             # Markdown and JSON benchmark reporting
│   │
│   ├── tools/                    # Surgical Code Analysis & Modification Tools
│   │   ├── patch_engine.py       # Robust unified diff parser & fuzzy applier (LF normalized)
│   │   ├── localizer.py          # BM25 + semantic symbol localizer
│   │   ├── ast_mapper.py         # Tree-sitter AST syntax and symbol extractor
│   │   ├── dependency_graph.py   # Call-graph and blast-radius analyzer
│   │   ├── git_history.py        # Git commit history & regression prevention context
│   │   └── sandbox.py            # Ephemeral isolated worktree sandboxes
│   │
│   ├── ingestion/                # Codebase Ingestion & Structure Analysis
│   │   └── parser.py             # Tree-sitter & AST repository parser
│   │
│   ├── rag/                      # Code Search & Retrieval Engine
│   │   ├── indexer.py            # Qdrant hybrid vector indexer
│   │   └── retriever.py          # BM25 + dense semantic code retriever
│   │
│   ├── review/                   # Independent Code Critic & Verification
│   │   └── critic.py             # Multi-angle verification & sanity checker
│   │
│   ├── dashboard/                # Live Operations UI
│   │   └── app.py                # Streamlit multi-tab benchmark & trajectory monitor
│   │
│   ├── cli.py                    # Unified CLI (`isha solve`, `isha bench`, `isha report`)
│   ├── config.py                 # Multi-model gateway, fallback chains, API credentials
│   ├── main.py                   # Main program entry point
│   └── server.py                 # FastMCP / HTTP server for agent integrations
│
├── scripts/                      # Developer Tools, Automation & Benchmarking
│   ├── run_all_evals.py          # Multi-session Docker evaluation orchestrator
│   ├── score.py                  # Ground-truth Docker benchmark scorecard tally
│   ├── verify_golden.py          # Regression gate for permanently locked golden passes
│   ├── laya_demo.py              # Interactive demonstration of LAYA safety gate
│   └── docker_maintain.ps1       # Docker container & image maintenance script
│
├── tests/                        # Comprehensive Automated Test Suite
│   ├── test_candidates.py        # Multi-model candidate tournament tests
│   ├── test_bench_gates.py       # AST syntax & diff validation gate tests
│   ├── test_senior_features.py   # Prompt invariants, blast radius, history tests
│   └── dummy_repo/               # Sandboxed test fixtures
│
├── data/                         # Benchmark Slices & Offline Datasets
│   ├── slices/                   # SWE-bench Lite session partition slices (s1–s10)
│   └── feedback/                 # Container execution diagnostic feedback
│
├── results/                      # Official Evaluation Reports & Verified Predictions
│   ├── lite300-s1/               # Session 1 predictions, reports, logs (11 Resolved)
│   ├── lite300-s2/               # Session 2 predictions, reports, logs (13 Resolved)
│   ├── lite300-s3/               # Session 3 predictions, reports, logs (15 Resolved)
│   ├── lite300-s4/               # Session 4 predictions, reports, logs (17 Resolved)
│   └── candidates.json           # Aggregated tournament arbitration metadata
│
└── docs/                         # In-Depth Guides & Specifications
    ├── components.md             # This module directory guide
    ├── PIPELINE.md               # End-to-end agent graph workflow specification
    ├── BENCHMARK_RUNBOOK.md      # Docker benchmark reproduction guide
    └── WHAT_MAKES_ISHA_UNIQUE.md # Technical differentiators & architecture notes
```

---

## 🔄 End-to-End Execution Workflow

1. **Intake & Localize (`src/tools/localizer.py`)**:
   - Ingests issue description and builds file/symbol candidate rankings using BM25 and AST analysis.
2. **Reproduction Test Synthesis (`src/agents/nodes.py`)**:
   - Synthesizes an isolated reproduction test that triggers the bug (**RED** phase).
3. **Multi-Model Candidate Tournament (`src/agents/candidates.py`)**:
   - Races diverse candidate models (`minimal_diff`, `call_site_aware`, `root_cause_first`) in isolated Git worktrees.
   - Enforces strict invariants: Guard clauses, hashability contracts, qualname hierarchy, decorator preservation.
4. **Static & AST Validation Gate (`src/bench/gates.py`)**:
   - Rejects unparseable diffs, indentation errors, and syntax anomalies before any test execution.
5. **LAYA Calibrated Selection (`src/approval/gate.py`)**:
   - Scores candidate patches with temperature-scaled probabilities (ECE=0.0010) to pick the safest, most minimal fix.
6. **Official Docker Verification (`src/bench/harness_eval.py`)**:
   - Evaluates the selected patch inside the official isolated SWE-bench container against `FAIL_TO_PASS` and `PASS_TO_PASS` test suites (**GREEN** phase).

---

## 🛡️ Coding Invariants (Preventing Hallucinations & Drift)

1. **Minimal Diff Priority**: Bug fixes address the root cause, not symptoms. No refactors, no renames, no cosmetic edits.
2. **POSIX LF Line Endings**: All patch outputs strictly enforce Unix newlines (`\n`) to prevent Windows `\r\n` git-apply failures.
3. **UTF-8 Strict Encoding**: All harness I/O enforces UTF-8 to prevent cp1252 character decode faults.
4. **Strict Isolation**: Agents execute inside ephemeral worktrees (`.worktrees/`); no concurrent runs ever mutate the primary workspace.
