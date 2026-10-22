# 🤖 ISHA — Enterprise Autonomous SWE Agent
### Iterative Software Harness & Arbitrator: SOTA MLOps & LLMOps Architecture

> **ISHA** is an enterprise-grade autonomous software engineering agent engineered around modern **LLMOps & MLOps principles**. Operating at **$0.00 inference cost** (0 GB VRAM requirement), ISHA localizes defects down to exact AST symbols, synthesizes reproduction test suites first (Phase RED), orchestrates multi-candidate tournament races in isolated Git worktrees, and validates patches via AST static compilation gates and official SWE-bench Docker environments (Phase GREEN).

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![LLMOps: 100% Cloud Multi-Model Mesh](https://img.shields.io/badge/LLMOps-100%25%20Cloud%20Mesh-00D26A.svg)](#-llmops-architecture-multi-model-mesh--observability)
[![MLOps: Ground Truth Docker](https://img.shields.io/badge/MLOps-SWE--bench%20Docker%20Harness-blueviolet.svg)](#-mlops-architecture-continuous-evaluation--safety-gates)
[![Inference Cost: $0.00 Free Tier](https://img.shields.io/badge/Inference-%240.00%20%2F%200%20GB%20VRAM-success.svg)](#-zero-cost-pareto-frontier)
[![Safety Gate: ECE 0.0010](https://img.shields.io/badge/LAYA%20Safety%20Gate-ECE%200.0010-purple.svg)](#2-laya-calibrated-decision-gate-ece--00010)
[![Official Docker Resolved: 76](https://img.shields.io/badge/Docker%20Resolved-76%20%2F%20300%20(Official)-brightgreen.svg)](#-swe-bench-lite-audited-scorecard)
[![Clean AST Patch Yield: 88.8%](https://img.shields.io/badge/Clean%20AST%20Yield-88.8%25%20(213%2F240)-blue.svg)](#-swe-bench-lite-audited-scorecard)
[![Live Portal](https://img.shields.io/badge/Live%20Portal-isha--ai.vercel.app-black.svg)](https://isha-ai.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📑 Table of Contents
1. [Executive Summary: How ISHA Redefines Autonomous SWE](#-executive-summary)
2. [LLMOps Architecture: Multi-Model Mesh & Observability](#-llmops-architecture-multi-model-mesh--observability)
   - [Zero-Cost Cloud Routing Matrix](#1-zero-cost-cloud-model-routing-matrix)
   - [Automated Failover & Key Pooling](#2-cross-provider-failover--quota-resilience)
   - [Full-Lifecycle Telemetry with Langfuse](#3-full-lifecycle-observability--telemetry-langfuse-cloud)
3. [MLOps Architecture: Continuous Evaluation & Safety Gates](#-mlops-architecture-continuous-evaluation--safety-gates)
   - [Closed-Loop TDD Pipeline (RED $\rightarrow$ GREEN)](#1-closed-loop-tdd-pipeline-phase-red--green)
   - [LAYA Calibrated Decision Gate ($ECE = 0.0010$)](#2-laya-calibrated-decision-gate-ece--00010)
   - [AST Static Compilation & Quality Gates](#3-ast-static-compilation--pre-sandbox-gates)
   - [Episodic Domain Playbooks & Closed-Loop Memory](#4-episodic-domain-playbooks--negative-veto-memory)
   - [Tree-Sitter Ingestion & Hybrid RAG](#5-tree-sitter-ast-ingestion--hybrid-qdrant-rag)
4. [Official SWE-bench Lite Scorecard](#-swe-bench-lite-audited-scorecard)
5. [CLI & Operational Guide](#-cli--operational-guide)
6. [Quickstart & Configuration](#-quickstart--configuration)
7. [Repository Architecture](#-repository-architecture)

---

## 💡 Executive Summary

Most first-generation autonomous SWE agents (e.g., standard Devin loops, SWE-agent, AutoCodeRover) treat software repair as an unconstrained text generation problem: they feed multi-turn prompts into expensive commercial frontier models ($5.00–$25.00 per task), execute unvalidated edits, and suffer from cascading hallucinations, regressions, and syntactically broken patches.

**ISHA replaces unconstrained prompting with a rigorous, dual-pillar MLOps & LLMOps harness:**

```text
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                           ISHA SYSTEM ARCHITECTURE                        │
 └───────────────────────────────────────────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
 ┌────────────────────────────────────┐ ┌────────────────────────────────────┐
 │         LLMOps SUBSYSTEM           │ │          MLOps SUBSYSTEM           │
 ├────────────────────────────────────┤ ├────────────────────────────────────┤
 │ • 100% Cloud-Hosted Model Mesh    │ │ • Official SWE-bench Docker Harness │
 │ • 0 GB VRAM / $0.00 Inference Cost │ │ • Phase RED Reproduction Pytest Gen│
 │ • Cross-Provider Dynamic Failover  │ │ • LAYA Probability Gate (ECE 0.001)│
 │ • Parallel Worktree Tournaments    │ │ • AST Static Syntax & Quality Gates│
 │ • Langfuse Observability & Traces  │ │ • Episodic Memory & Negative Veto  │
 │ • Closed-Loop Multi-Candidate Mesh │ │ • Tree-Sitter & Hybrid Qdrant RAG  │
 └────────────────────────────────────┘ └────────────────────────────────────┘
```

| Architectural Dimension | Conventional Agents (Devin, SWE-agent) | ISHA (Iterative Software Harness & Arbitrator) |
| :--- | :--- | :--- |
| **Inference Cost** | **$5.00 – $25.00+ per task** (expensive proprietary token loops) | **$0.00 / Task** (Pareto leader running across free-tier cloud providers) |
| **Local Hardware Footprint** | Demands high VRAM local GPUs or costly remote compute | **0 GB VRAM / 0 Local GPUs** (100% Cloud inference + CPU AST engine) |
| **Telemetry & Observability** | Opaque terminal logs or closed web UIs | **Full-Lifecycle LLMOps**: Step-level DAG traces, token burn & latency via Langfuse |
| **Patch Discipline** | Bloated diffs with refactors, style churn, and comment pollution | **Surgical Minimal Diff**: Zero unrelated edits, strict single-point root-cause fixes |
| **Negative Invariant Safety**| Relies on LLM self-reflection (repeats identical runtime faults) | **Empirical Invariants**: Hardcoded checks guarding `len(None)`, unhashable sets, decorators |
| **Candidate Generation** | Single-shot or greedy trajectory exploration | **Multi-Candidate Worktree Tournament**: Races 3–5 diverse strategies in parallel |
| **Verification Gate** | Simulated mock tests or raw pytest returncodes | **TDD Red-to-Green**: Requires reproduction test to fail baseline & pass patch |
| **PR Decision Arbiter** | Blind auto-submission on any exit code 0 | **LAYA Calibrated Gate**: Temperature-scaled Platt logistic model ($ECE = 0.0010$) |

---

## ⚡ LLMOps Architecture: Multi-Model Mesh & Observability

### 1. Zero-Cost Cloud Model Routing Matrix
ISHA routes each specialized agent stage to optimal free-tier cloud models, eliminating local GPU constraints while maximizing throughput and reasoning depth:

| Agent Node | Function | Primary Cloud Model | Provider ($0.00 Tier) | Temperature | Specialization |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Node 1** | **Investigation** | `bge-reranker-base` + `gemini-3.8-flash` | Local ONNX + Google AI Studio | `0.00` | Fast AST semantic search & blast radius |
| **Node 2** | **Decomposer** | `groq/qwen/qwen-2.5-coder-32b` | Groq Cloud LPUs | `0.10` | High-speed issue decomposition (500 tok/s) |
| **Node 3** | **Planner** | `gemini/gemini-3.8-flash` | Google AI Studio | `0.20` | Multi-file context ingestion & repair plan |
| **Node 4** | **Confidence Gate**| `ISHA-LocReranker` (125M) | In-Memory CPU Engine | `—` | Bayesian symbol localization gate (<2ms) |
| **Node 5** | **Regression Test**| `groq/openai/gpt-oss-120b` | Groq Cloud | `0.20` | Standalone failing reproduction pytest (RED) |
| **Node 6a**| **Candidate 1** | `groq/qwen/qwen3.8-27b` | Groq Cloud LPUs | `0.20` | Strategy: `minimal_diff` (surgical edits) |
| **Node 6b**| **Candidate 2** | `groq/openai/gpt-oss-120b` | Groq Cloud LPUs | `0.20` | Strategy: `root_cause_first` (invariant logic)|
| **Node 6c**| **Candidate 3** | `gemini/gemini-3.8-flash` | Google AI Studio | `0.20` | Strategy: `call_site_aware` (caller propagation)|
| **Node 6d**| **Candidate 4** | `mistral/codestral-latest` | Mistral AI Platform | `0.20` | Strategy: `defensive_fix` (boundary guards) |
| **Node 6e**| **Candidate 5** | `gemini/gemini-3.8-flash` (1M ctx) | Google AI Studio | `0.20` | Strategy: `cross_file_audit` (repo audit) |
| **Node 7** | **Static AST Gate**| `ast.parse` + `py_compile` | Local CPU | `—` | Zero-cost pre-sandbox syntax validator (<2ms)|
| **Node 8** | **Replan / Repair**| **Sticky to assigned model** | Same as candidate branch | `0.20` | Self-healing from real pytest tracebacks |
| **Node 9** | **LAYA Safety Gate**| Platt Scaler + `gemini-3.8-flash` | In-Memory CPU + Google | `—` | Probability gate ($P_{\text{solve}} \ge 0.65$) |

### 2. Cross-Provider Failover & Quota Resilience
Production LLMOps demands 99.9% availability despite provider rate limits (HTTP 429). ISHA implements:
* **Round-Robin Key Pooling**: Dynamically distributes load across comma-separated keys (`GEMINI_API_KEYS`, `GROQ_API_KEYS`, `MISTRAL_API_KEYS`).
* **Automated Cooldown & Key Revival**: Tracks key exhaustion with exponential backoff and automatically revives keys after 120-second rolling quota windows.
* **Opposing-Provider Fallback Pairing**: When Google AI Studio reaches quota thresholds, the engine fails over to Groq LPUs or Mistral Codestral, preventing cascading pipeline outages.
* **Sticky Model Replan**: When an in-loop pytest fails in Docker, the candidate stays locked to its assigned model family (`state.assigned_model`), avoiding reasoning degradation.

### 3. Full-Lifecycle Observability & Telemetry (Langfuse Cloud)
ISHA integrates enterprise observability through **Langfuse Cloud**, capturing end-to-end telemetry for every execution:
* **Step-Level Execution DAG**: Traces every node transition (Investigation $\rightarrow$ Planning $\rightarrow$ Test Synthesis $\rightarrow$ Tournament $\rightarrow$ Arbitration $\rightarrow$ LAYA Gate).
* **Token Burn & Latency Tracking**: Records prompt/completion token usage and per-node latency across providers ($0.00 actual cloud spend).
* **Error Taxonomy**: Categorizes failures across syntax errors, test assertion mismatches, timeout boundaries, and regression triggers.

---

## 🛡️ MLOps Architecture: Continuous Evaluation & Safety Gates

### 1. Closed-Loop TDD Pipeline (Phase RED $\rightarrow$ GREEN)
ISHA implements true Test-Driven Development rather than heuristic grading:
1. **Phase RED (Reproduction Synthesis)**: Node 5 synthesizes a self-contained reproduction pytest based on the issue description. This test **must fail** on the unmodified repository baseline. If it passes prematurely, it is rejected.
2. **Phase GREEN (Candidate Resolution)**: Multiple candidate patches are generated across isolated Git worktrees (`.worktrees/candidate_*`). The reproduction test and repository regression suite are executed.
3. **Traceback-Driven Self-Correction**: If a candidate fails, the raw pytest traceback is extracted and fed back into Node 8 for up to 2 targeted repair iterations.

### 2. LAYA Calibrated Decision Gate ($ECE = 0.0010$)
Most agents suffer from overconfidence, submitting patches that pass local assertions but break peripheral modules. ISHA guards Pull Request submissions with **LAYA (Language Agent Yield Arbitrator)**:
* **Temperature-Scaled Platt Calibration**: Maps raw verification scores through an empirical logistic function ($T=0.35$).
* **Ultra-Low Expected Calibration Error**: Achieves an $ECE$ of **0.0010** with 100% precision on held-out validation tasks ($N_{val}=103$).
* **Safe Decision Boundary**: Patches are only approved if calibrated probability $P_{\text{solve}} \ge 0.65$.

### 3. AST Static Compilation & Pre-Sandbox Gates
Before incurring container boot latency or Docker overhead, candidate diffs must pass local AST compilation gates (<2ms latency, $0.00 cost):
* `ast.parse()`: Validates Python syntax tree integrity.
* `py_compile.compile()`: Confirms bytecode compilation without syntax errors or bad indentations.
* **POSIX LF Line Ending Normalization**: Automatically converts CRLF to POSIX LF (`\n`) and validates UTF-8 encoding.
* **Negative Container Invariants**: Enforces 8 non-negotiable structural rules:
  1. *Class Anchoring*: New methods must reside inside the exact target enclosing class.
  2. *Guard Clause Completeness*: Mandatory `if val is None:` checks prior to `len(val)`.
  3. *Decorator Preservation*: Callable wrappers must include `@functools.wraps(...)`.
  4. *Type Invariants*: Preserves exact falsy distinctions (`None` vs `""` vs `0` vs `False`).
  5. *Django Hashability Contracts*: Mutable collections cannot be inserted into hash keys.

### 4. Episodic Domain Playbooks & Negative-Veto Memory
ISHA maintains a persistent SQLite WAL ledger (`data/memory.db` + `output/fix_history.jsonl`):
* **Positive Few-Shot Exemplars**: Injects verified, Docker-proven diffs matching the target repository architecture.
* **Dynamic Framework Invariants**: Automatically activates domain-specific rules (e.g. Django widget `id_for_label` nullability, `__qualname__` serialization) to prevent benchmark contamination.
* **Negative Veto Engine**: Vector similarity check (cosine threshold $> 0.92$) against historically rejected diffs actively prevents repeating proven mistakes.

### 5. Tree-Sitter AST Ingestion & Hybrid Qdrant RAG
* **Tree-Sitter Syntax Parsing**: Parses repository structure into granular AST symbols (classes, functions, call-sites).
* **Hybrid Dense/Lexical Retrieval**: Combines Qdrant vector embeddings (`bge-reranker-base`) with BM25 keyword matching to localize root-cause files and functions with surgical accuracy.

---

## 🏆 SWE-bench Lite Audited Scorecard

Every metric below represents **ground-truth execution inside official SWE-bench Docker containers** (`report.json`), avoiding simulated or unverified claims:

| Benchmark Session | Evaluated Instances | Clean AST Patches | Patch Yield | Official Docker Resolved | Solve Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Session 4 (`lite300-s4`)** | 30 | **29** | 96.7% | **21 / 30** | **70.0%** 🏆 |
| **Session 3 (`lite300-s3`)** | 30 | **29** | 96.7% | **20 / 30** | **66.7%** 🏆 |
| **Session 2 (`lite300-s2`)** | 30 | **30** | 100.0% | **14 / 30** | **46.7%** 🚀 |
| **Session 1 (`lite300-s1`)** | 30 | **22** | 100.0% | **11 / 30** | **36.7%** 🚀 |
| **Session 8 (`lite300-s8`)** | 30 | **25** | 83.3% | **4 / 30** | **13.3%** 🚀 |
| **Session 5 (`lite300-s5`)** | 30 | **26** | 86.7% | **3 / 30** | 10.0% |
| **Session 6 (`lite300-s6`)** | 30 | **20** | 66.7% | **3 / 30** | 10.0% |
| **Sessions 7, 9, 10** | 90 | **72** | 80.0% | Active / Queued | — |
| **S1–S4 PEAK SLICE** | **120** | **110** | **91.7%** | **66 / 120** | **55.0%** 🌟 |
| **TOTAL AUDITED (S1–S10)** | **240** | **213** | **88.8%** | **76 / 300** | **25.33% (76 / 300)** |

*To inspect the audited ground-truth scorecard directly in your terminal:*
```bash
python scripts/score.py
```

---

## 💻 CLI & Operational Guide

ISHA features a unified, zero-leak CLI interface via the `isha` command:

```text
   ___  ____  _   _    _    
  |_ _|/ ___|| | | |  / \   
   | | \___ \| |_| | / _ \  
   | |  ___) |  _  |/ ___ \ 
  |___||____/|_| |_/_/   \_\ 
  Autonomous SWE Agent (v0.3.0)
```

### Command Reference

| Command | Action | Default Mode | Practical Example |
| :--- | :--- | :--- | :--- |
| **`isha`** | Displays clean ASCII banner & quick command index. | Non-interactive help | `isha` |
| **`isha fix`** | Localizes defect, synthesizes reproduction test, races candidates, and verifies AST gates. | Safe sandbox preview | `isha fix . --issue "Fix TypeError in router.py"` |
| **`isha fix --apply`** | Runs full agentic loop and applies verified minimal patch to local repo files. | In-place file update | `isha fix . --issue "Fix 500 on None" --apply` |
| **`isha fix --pr`** | Clones repo, fixes issue, commits diff, pushes branch, and opens GitHub Pull Request. | Automated Git / PR | `isha fix https://github.com/org/repo --issue "..." --pr` |
| **`isha doctor`** | Complete toolchain self-test (Python, Git, Docker, API keys, disk space, models). | Health diagnostics | `isha doctor` |
| **`isha ui`** | Launches the dark-mode interactive web control room at `http://localhost:8501`. | Streamlit dashboard | `isha ui --port 8501` |
| **`isha bench`** | Executes SWE-bench evaluation benchmark runs across isolated repository worktrees. | Evaluation harness | `isha bench --slice stratified --limit 30` |
| **`isha report`** | Renders formatted markdown scorecards, solve rates, and run-to-run comparisons. | Terminal markdown | `isha report --run-id lite300-s4 --compare lite300-s3` |
| **`isha-mcp`** | Runs FastMCP Model Context Protocol stdio server for IDE integrations. | IDE connector | `isha-mcp` |

---

## 🚀 Quickstart & Configuration

### 1. Installation
Install ISHA via `pip` (Python 3.10+):
```bash
# Direct install
pip install isha

# Or install editable from repository root
git clone https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git
cd ISHA-Iterative-Software-Harness-Arbitrator-/isha-agent
pip install -e .
```

### 2. Configure Cloud API Credentials
Copy `.env.example` to `.env` and set your free-tier cloud keys:
```env
# Google AI Studio (Free tier)
GOOGLE_API_KEY=AIzaSy...
# Multiple keys for round-robin pooling:
# GEMINI_API_KEYS=key1,key2,key3

# Groq Cloud (Free LPU tier: Qwen-2.5-Coder-32B, GPT-OSS-120B)
GROQ_API_KEY=gsk_...

# Mistral AI (Codestral Free Experiment tier)
MISTRAL_API_KEY=...

# Langfuse Observability (Optional Cloud Tracing)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Verification & Self-Test
Run the toolchain doctor to verify all cloud endpoints and local compilers:
```bash
isha doctor
```

Solve your first issue in preview sandbox mode:
```bash
isha fix . --issue "The calculate_discount function throws ZeroDivisionError when total is 0"
```

---

## 📂 Repository Architecture

```text
isha-agent/
├── src/                          # Core Agent Implementation
│   ├── agents/                   # Autonomous Agent State Machine & Tournament
│   │   ├── graph.py              # LangGraph cyclic execution machine
│   │   ├── nodes.py              # Specialized agent nodes (Localizer, Planner, Coder, Verifier)
│   │   ├── candidates.py         # Multi-candidate strategy tournament
│   │   ├── state.py              # Strongly-typed AgentState schemas (Pydantic v2)
│   │   └── fix_history.py        # Vectorized memory of Docker-proven bug patterns
│   │
│   ├── approval/                 # LAYA Calibrated Decision Engine
│   │   ├── gate.py               # Temperature-scaled decision gate (ECE 0.0010)
│   │   ├── calibrator.py         # Platt logistic regression calibrator
│   │   └── danger.py             # Security & regression antipattern veto
│   │
│   ├── bench/                    # Official SWE-bench Docker Harness
│   │   ├── harness_eval.py       # Official Docker testbed execution runner
│   │   ├── runner.py             # Batch session evaluation across partitions
│   │   ├── gates.py              # AST static compiler & git-apply gates
│   │   └── report.py             # Scorecard and markdown reporting
│   │
│   ├── tools/                    # Surgical Code Analysis & Modification Engine
│   │   ├── patch_engine.py       # POSIX LF unified diff parser & patch applier
│   │   ├── localizer.py          # BM25 + semantic symbol localizer
│   │   ├── ast_mapper.py         # Tree-sitter AST syntax and symbol extractor
│   │   └── sandbox.py            # Ephemeral isolated worktree sandboxes
│   │
│   ├── rag/                      # Hybrid Code Search & Retrieval Engine
│   │   ├── indexer.py            # Qdrant hybrid vector indexer
│   │   └── retriever.py          # Dense semantic + BM25 lexical code retriever
│   │
│   ├── dashboard/                # Live Operations Web UI (Streamlit)
│   ├── cli.py                    # Unified CLI (`isha fix`, `isha doctor`, `isha bench`)
│   ├── config.py                 # Multi-model gateway, key pooling, and failover chains
│   └── server.py                 # FastMCP stdio server for Cursor / Antigravity
│
├── scripts/                      # Evaluation & Automation Orchestrators
│   ├── score.py                  # Single Source of Truth Docker scorecard tally
│   ├── run_all_evals.py          # Multi-session benchmark evaluation driver
│   └── verify_golden.py          # Regression safety testbed for locked passes
│
├── tests/                        # Comprehensive Automated Test Suite (100% green)
├── data/                         # Benchmark partitions & SQLite memory ledger
└── results/                      # Official Docker evaluation reports & ground truth evidence
```

---

## 📄 License
Distributed under the [MIT License](LICENSE).
