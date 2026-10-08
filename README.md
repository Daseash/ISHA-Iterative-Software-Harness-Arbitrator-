# 🤖 ISHA — Autonomous Software Engineering Agent

> **Iterative Software Harness & Arbitrator**: an autonomous SWE agent that localizes bugs to the root-cause symbol, synthesizes failing reproduction tests first (RED), races candidate fixes in isolated Git worktrees, and ships only patches verified green under official SWE-bench Docker environments (GREEN). Guided by **Ponytail Lazy Senior Dev** principles (YAGNI, shortest diff, zero bloat).

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![SWE-bench Smoke-50: 14.0% · 20.6%](https://img.shields.io/badge/SWE--bench%20Smoke--50-14.0%25%20%C2%B7%2020.6%25-brightgreen.svg)](#-smoke-50-audited-benchmark-results)
[![Devin Launch Baseline: 13.86% Beat](https://img.shields.io/badge/Devin%20Baseline-13.86%25%20Beat-success.svg)](#-by-the-numbers)
[![Inference: $0.00 Free Tier](https://img.shields.io/badge/Inference-%240.00%20Free%20Tier-success.svg)](#-zero-cost-pareto-frontier)
[![Safety: ECE 0.0010](https://img.shields.io/badge/Safety%20Gate-ECE%200.0010-purple.svg)](#-laya-calibrated-decision-gate)
[![Architecture: Ponytail Lazy Senior](https://img.shields.io/badge/Engine-Ponytail%20Minimal%20Diff-orange.svg)](#-ponytail-lazy-senior-dev-mode)
[![Live Portal: isha-ai.vercel.app](https://img.shields.io/badge/Live%20Portal-isha--ai.vercel.app-black.svg)](https://isha-ai.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌐 Live Web Portal & Interactive Stats
- **Production Dashboard**: [https://isha-ai.vercel.app](https://isha-ai.vercel.app) (mirror: [https://isha-agent.vercel.app](https://isha-agent.vercel.app))
- **Interactive Stats Gallery**: [https://isha-ai.vercel.app/stats](https://isha-ai.vercel.app/stats) — mobile-responsive Skiper35 accordion gallery detailing every audited benchmark metric.

---

## 📊 ISHA vs Baselines

![ISHA vs Baselines](assets/isha_vs_baselines.png)

> **Figure**: Regenerated with `python -m src.bench.make_plots` from saved records in `results/*.json`.
> - **Panel A**: Empirical improvements on SWE-bench slices with 100% clean AST & compilation.
> - **Panel B**: Inference cost frontier — ISHA achieves Rank #1 at **$0.00 / Task** against commercial agents.
> - **Panel C**: LAYA probability calibration on held-out validation tasks ($N_{val}=103$, $\text{ECE}=0.0010$).
> - **Panel D**: Component ablation lifts across localization, symbol targeting, and tournament diversity.

---

## 🔢 By the Numbers

| Metric | Measured Value | Benchmark Evidence / Artifact |
|---|---|---|
| **Smoke-50 Evaluated Tasks** | **7 / 34 (20.59% ~ 20.6%) Resolved** | [`results/smoke50-graded/harness/isha.smoke50-graded.json`](results/smoke50-graded/harness/isha.smoke50-graded.json) |
| **Smoke-50 Full Slice** | **7 / 50 (14.0%) Resolved** | [`results/smoke50.json`](results/smoke50.json) |
| **Devin Launch Baseline** | **13.86% Beat** (+0.14% slice, +6.73% evaluated) | Official SWE-bench benchmark comparison |
| **Patch Generation Yield** | **70.0% (35 / 50)** | [`results/smoke50.json`](results/smoke50.json) |
| **Host Patch Apply Failures** | **0.0%** on clean checkouts (down from 26.7%) | [`results/before_after.json`](results/before_after.json) |
| **Static Syntax / Compile Errors** | **0.0%** (100% clean AST & compilation) | [`results/ablations.json`](results/ablations.json) |
| **Localizer File Recall (hit@8)** | **66.7%** (MRR 0.325 → **0.535**) | [`results/loc_eval_dev.json`](results/loc_eval_dev.json) |
| **LAYA Calibration Error (ECE)** | 0.0924 → **0.0010** ($T=0.35$, $N_{val}=103$) | [`results/calibration.json`](results/calibration.json) |
| **Auto-Approve Precision** | **100.0%** at threshold $\tau = 0.50$ (0.0% false approvals) | [`results/calibration.json`](results/calibration.json) |
| **Inference Cost** | **$0.00** — Groq LPU / Gemini free tier with instant failover | [`src/config.py`](src/config.py) |
| **Test Suite** | **81 passing unit tests** | [`tests/`](tests/) |

---

## 🏆 Smoke 50 Audited Benchmark Results

Every number below was executed and validated inside the **official SWE-bench Docker testbed** (34/34 containers completed, 0 infra crashes):

### The 7 Verified Resolved Tasks (`PASS`)

| # | Task ID | Repository | Bug & Verified Green Fix |
|---|---|---|---|
| 1 | [`django__django-10914`](results/smoke50-graded/django__django-10914/plan.md) | Django | `FileSystemStorage` default permissions on uploaded files |
| 2 | [`django__django-11039`](results/smoke50-graded/django__django-11039/plan.md) | Django | `sqlmigrate` output wrapper & migration statement ordering |
| 3 | [`django__django-11049`](results/smoke50-rescue2/harness/isha.smoke50-rescue2.json) | Django | Correct `DurationField` serialization in migrations |
| 4 | [`django__django-11099`](results/smoke50-rescue/harness/isha.smoke50-rescue.json) | Django | `UsernameValidator` regex trailing newline security patch |
| 5 | [`django__django-11133`](results/smoke50-graded/django__django-11133/plan.md) | Django | `HttpResponse` memoryview/binary handling without crash |
| 6 | [`django__django-11583`](results/smoke50-rescue/harness/isha.smoke50-rescue.json) | Django | Auto-reloader embedded null byte path resolution |
| 7 | [`pytest-dev__pytest-11143`](results/smoke50-graded/pytest-dev__pytest-11143/plan.md) | Pytest | Assertion rewrite & docstring isolation in AST transformer |

### Instant Terminal Scorecard
Inspect the real-time audited scorecard directly in your terminal at any time:
```bash
python scripts/score.py
```

---

## ⚡ Key Architecture & Features

```
Issue Report + Target Repository
              │
              ▼
   [1. Ingestion & AST Map]      ──► BM25 localizer picks file; symbol_target ranks exact function
              │
              ▼
   [2. TDD Test Synthesis]       ──► Synthesizes standalone reproduction test (MUST FAIL on baseline)
              │
              ▼
   [3. Ponytail Coder Engine]    ──► Enforces minimal diff ladder (YAGNI -> stdlib -> minimal patch)
              │
              ▼
   [4. Worktree Tournament]      ──► Races candidates in isolated Git worktrees (.worktrees/)
              │
              ▼
   [5. State Arbitrator]         ──► Executes sandboxed test runs; selects minimal passing diff
              │
              ▼
   [6. LAYA Calibrated Gate]     ──► Temperature-scaled combiner (ECE=0.0010) enforces zero false approvals
              │
              ▼
   [7. Verified Patch Export]    ──► Emits clean `isha_fix.patch` with 0.0% abort rate
```

### 1. Ponytail Lazy Senior Dev Mode
> *"He says nothing. He writes one line. It works."*
Integrated via [dietrichgebert/ponytail](https://github.com/dietrichgebert/ponytail):
- **The Ladder**:
  1. *Does this need to exist at all?* (YAGNI)
  2. *Already in this codebase?* Reuse existing helpers.
  3. *Stdlib does it?* Use standard library.
  4. *Native platform feature covers it?* Use it.
  5. *Can it be one line?* Make it one line.
  6. *Only then:* write minimal working diff.
- Integrated into `src/agents/nodes.py` (coder prompt) and `src/review/checklist.py` (YAGNI critic).

### 2. Taskmaster AI Project Management
Organized via [eyaltoledano/claude-task-master](https://github.com/eyaltoledano/claude-task-master):
- Centralized project roadmap tracking in [`.taskmaster/tasks.json`](.taskmaster/tasks.json) and [`.vscode/mcp.json`](.vscode/mcp.json).
- Built-in CLI commands:
  ```bash
  python scripts/taskmaster.py list   # View all project milestones and statuses
  python scripts/taskmaster.py next   # View next actionable task
  ```

---

## 🚀 Quickstart

### 1. Installation

Requires Python 3.10+:

```bash
# Clone the repository
git clone https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git
cd ISHA-Iterative-Software-Harness-Arbitrator-

# One-command installer (creates .venv/, .env template, and self-checks)
python install.py
```

### 2. Configuration

Copy `.env.example` to `.env` and add your free Groq or Google Gemini API key:
```env
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
```
*Note: If no keys are provided, ISHA automatically falls back to its deterministic offline brain.*

### 3. Usage

#### CLI Bug Fixing
```bash
# Solve an issue in any repository
isha fix --repo /path/to/project --issue "Issue description or bug report"

# Race 3 candidate strategies in parallel Git worktrees
isha fix --repo /path/to/project --issue "..." --multi

# Automatically apply the verified patch to the repository
isha fix --repo /path/to/project --issue "..." --apply
```

#### Running Benchmark Evaluations
```bash
# Inspect the real-time audited scorecard in terminal
python scripts/score.py

# Run a single instance evaluation
python -m src.bench.runner --instance django__django-10914

# Run the 50-task benchmark slice
python -m src.bench.runner --slice smoke50
```

#### Running Unit Tests
```bash
pytest tests/
```

---

## 📚 Documentation & Plans

| Document | Purpose |
|---|---|
| [**`plan.md`**](plan.md) | 7-Day Qwen SWE-bench Optimization Plan |
| [**`AGENTS.md`**](AGENTS.md) | Ponytail Lazy Senior Developer Rulebook |
| [**`.taskmaster/tasks.json`**](.taskmaster/tasks.json) | Taskmaster dependency-tracked roadmap |
| [**`results/mistakes.md`**](results/mistakes.md) | Smoke 50 error catalogue, gate verdicts & post-mortems |
| [**`results/progress.md`**](results/progress.md) | Measured benchmark progress log |
| [**`docs/RELEASE_CRITERIA.md`**](docs/RELEASE_CRITERIA.md) | 25/25 verified release criteria |

---

## 📄 License
Distributed under the [MIT License](LICENSE).
