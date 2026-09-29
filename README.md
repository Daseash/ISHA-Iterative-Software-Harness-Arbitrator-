# 🤖 ISHA — Autonomous Software Engineering Agent

> **Iterative Software Harness & Arbitrator**: An autonomous SWE agent that localizes bugs, writes a reproduction test *first* (RED), tests 3 parallel fixes in isolated Git worktrees, and delivers a verified minimal patch (GREEN).

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Architecture: Multi-Agent](https://img.shields.io/badge/Architecture-3--Worktree%20Parallel-purple.svg)](#architecture)
[![Inference: Free Tier](https://img.shields.io/badge/Inference-%240.00%20Free%20Tier-success.svg)](#configuration)

---

## ⚡ Key Highlights

- 🧪 **TDD Red-to-Green**: Synthesizes a standalone reproduction test that must fail before the patch and pass after it.
- 🌿 **3-Worktree Parallel Tournament**: Tests direct, defensive, and alternative strategies in isolated Git worktrees (`.worktrees/`). Your working branch is never polluted.
- 🎯 **Minimal Churn Arbitrator**: Automatically selects the cleanest patch with zero collateral regressions.
- ⚡ **Zero-Cost Inference**: Uses fast open-weights models (`qwen3.8-27b`, `gpt-oss-120b/20b`, Gemini Flash) with automatic instant failover.
- 🛡️ **Built-in Guardrails**: Automated AST syntax checking and secret/credential leakage prevention.

---

## 🚀 Quickstart

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-.git
cd ISHA-Iterative-Software-Harness-Arbitrator-/isha-agent

# Install dependencies and global CLI
pip install -e .
```

### 2. Configuration

Copy the example environment file:
```bash
cp .env.example .env
```
Add your free Groq or Google Gemini API key to `.env`:
```env
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
```

---

## 💻 Usage

### Option A: Command Line Interface (CLI)

Run ISHA on any repository directly from your terminal:

```bash
# Preview the plan, test, and patch
isha --repo /path/to/project --issue "Cart checkout fails when price is float"

# Automatically apply the verified patch to your repo
isha --repo /path/to/project --issue "Cart checkout fails when price is float" --apply
```

### Option B: Interactive Web Dashboard

Launch the Streamlit dashboard:

```bash
streamlit run src/dashboard/app.py
```
- **🚀 Run & Overview**: Select issues, run fixes, and monitor live execution.
- **📄 Code Diff & Tests**: Inspect generated TDD reproduction tests and unified diffs.
- **💻 Download & CLI Export**: 1-click download of `isha_fix.patch` or apply directly to your repository.
- **🛡️ Guardrails & Audit**: Review secret scans and persistent decision audit trails (`output/approvals.jsonl`).
- **📊 Benchmark Runs**: Inspect evaluation checkpoints and comparative metrics.

---

## 🏗️ Architecture

```
Issue Text + Target Repo
         │
         ▼
[1. Ingestion & AST Map]  ──► Locates suspect files & extracts verbatim lines
         │
         ▼
[2. TDD Test Synthesis]   ──► Writes reproduction test (MUST FAIL on current code)
         │
         ▼
[3. Parallel Tournament]  ──► 3 Isolated Git Worktrees (.worktrees/candidate-*)
         │                     ├── Candidate 1: Direct surgical fix
         │                     ├── Candidate 2: Defensive boundary check
         │                     └── Candidate 3: Alternative caller fix
         │
         ▼
[4. State Arbitrator]     ──► Executes tests in sandboxes; picks minimal passing diff
         │
         ▼
[5. Security & Apply]     ──► Scans for secrets/syntax errors → Generates `isha_fix.patch`
```

---

## 🧪 Running Tests

Verify the agent test suite:

```bash
python -m pytest --ignore=tests/dummy_repo
```

---

## 📄 License

Distributed under the [MIT License](LICENSE).
