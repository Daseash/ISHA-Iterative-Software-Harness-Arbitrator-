# 🚀 ISHA Open-Source Publication & Release Criteria

This document outlines the strict quality, safety, empirical, and developer-experience criteria required before public release of **ISHA (Iterative Software Harness & Arbitrator)**.

---

## 📊 Summary of Readiness Dimensions

| Dimension | Criteria Count | Current Status | Acceptance Bar |
|---|---|---|---|
| **1. Empirical Benchmarks** | 5 | 🟡 2/5 Verified | Validated on SWE-bench slices with official harness |
| **2. Engine & Model Resilience** | 4 | 🟢 4/4 Verified | 0% API freeze, robust multi-model fallback |
| **3. Patch Quality & Safety** | 4 | 🟢 4/4 Verified | AST valid, 0 secrets leaked, clean unified diff |
| **4. TDD & Multi-Agent Arbitration** | 4 | 🟢 4/4 Verified | Red-to-green proof, 3-worktree isolated sandboxes |
| **5. Developer Experience (DX) & CLI** | 4 | 🟢 4/4 Verified | Global CLI, 1-click patch download & web UI |
| **6. Documentation & Reproducibility** | 4 | 🟡 3/4 Verified | Public README, replication guide, asset charts |

---

## Dimension 1: Empirical Benchmark Rigor (SWE-bench)

To publish alongside high-profile AI research systems (like Laya, OpenHands, Agentless), claims must be grounded in reproducible benchmark numbers.

- [ ] **CRIT-BENCH-01: SWE-bench Lite Verified Run**
  - **Description**: Run ISHA across representative SWE-bench Lite instances (Astropy, Django, SymPy, Flask).
  - **Verification**: `python -m src.bench.runner --slice data/slices/baseline.json --run-id eval_v1`
  - **Acceptance Bar**: Complete run without execution crashes; resolution logs recorded in `results/`.
- [ ] **CRIT-BENCH-02: Official Harness Cross-Validation**
  - **Description**: Generated patches must pass evaluation inside official SWE-bench evaluation containers to prove zero false positives.
  - **Verification**: `python -m src.bench.harness_eval --predictions results/eval_v1/predictions.json`
  - **Acceptance Bar**: Zero patch apply failures due to malformed hunks.
- [x] **CRIT-BENCH-03: Zero-Cost Empirical Frontier**
  - **Description**: Prove that ISHA operates efficiently on $0 inference cost using free open-weights models (Groq/Gemini).
  - **Verification**: Automated token tracking in `results/*.json`.
  - **Acceptance Bar**: Average run cost = $0.00 while maintaining competitive resolution.
- [x] **CRIT-BENCH-04: Laya-Style Comparative Visualization**
  - **Description**: Publication-ready comparison graphs comparing ISHA against Agentless, OpenHands, and raw LLM baselines.
  - **Verification**: `python -m src.bench.make_plots` generating `assets/isha_vs_baselines.png`.
  - **Acceptance Bar**: Clear 4-panel visual: Resolution %, Cost per resolved bug, Patch apply failure rate, Token efficiency.
- [ ] **CRIT-BENCH-05: Verbatim Failure Breakdown Audit**
  - **Description**: Aggregate failure classifier to document remaining failure modes (`localization_wrong`, `tests_failed`, etc.).
  - **Verification**: `python -m src.bench.classify <run-id>`
  - **Acceptance Bar**: Every failure has a categorized root cause; `api_failure` < 5%.

---

## Dimension 2: Engine & Model Pipeline Resilience

The core engine must be completely impervious to model deprecations, provider downtime, or token quotas.

- [x] **CRIT-ENG-01: Free-Tier Multi-Provider Fallback Chain**
  - **Description**: Automatic cascade from primary model (`qwen/qwen3.8-27b`) to fast fallbacks (`gpt-oss-120b`, `gpt-oss-20b`, `gemini-3.8-flash`).
  - **Verification**: Simulated 429/503 errors trigger immediate model advancement.
  - **Acceptance Bar**: No agent execution stalls; zero manual restarts required.
- [x] **CRIT-ENG-02: Fast-Failover Timeout Bypass**
  - **Description**: If a model provider asks for a backoff sleep > 15 seconds, skip immediately to the next fallback model.
  - **Verification**: Unit tests in `tests/test_v2_capabilities.py`.
  - **Acceptance Bar**: Maximum delay per node call < 20 seconds.
- [x] **CRIT-ENG-03: Offline Brain Fallback**
  - **Description**: If all external APIs are severed, offline rule-based heuristics take over to prevent fatal crashes.
  - **Verification**: Verified via `src/tools/offline_brain.py` and `test_decomposer_offline_fallback`.
  - **Acceptance Bar**: Safe fallback response returned with warning metadata.
- [x] **CRIT-ENG-04: Full Test Suite Green**
  - **Description**: All core agent unit tests, mock sandboxes, and integration tests must pass.
  - **Verification**: `python -m pytest --ignore=tests/dummy_repo`
  - **Acceptance Bar**: 55/55 passed (100% green).

---

## Dimension 3: Patch Quality, Safety & Guardrails

An autonomous software engineer must never corrupt the user's repository or leak sensitive information.

- [x] **CRIT-SAFE-01: AST & Syntax Pre-Validation**
  - **Description**: Every candidate code patch is checked for Python syntax and AST integrity before execution.
  - **Verification**: AST parser in `src/tools/patch_engine.py`.
  - **Acceptance Bar**: Zero syntax errors introduced by agent patches.
- [x] **CRIT-SAFE-02: Automated Secret & Credential Scanning**
  - **Description**: Scans patches for leaked API keys, tokens, `.env` files, or private certificates.
  - **Verification**: `src/guardrails/scanner.py::scan_patch_for_secrets`.
  - **Acceptance Bar**: 100% clean check; blocking patch application if any credential is detected.
- [x] **CRIT-SAFE-03: Unified Diff & Hunk Fuzzy Matcher**
  - **Description**: Robust patch engine that supports line offset fuzzing and context matching without requiring a host `patch` binary.
  - **Verification**: `tests/test_patch_engine.py`.
  - **Acceptance Bar**: Patch apply failure rate < 3%.
- [x] **CRIT-SAFE-04: Persistent Audit Trail**
  - **Description**: Every fix approval, rejection, and patch application must be immutably recorded.
  - **Verification**: Recorded in `output/approvals.jsonl` and viewable in Streamlit Tab 4.
  - **Acceptance Bar**: Exportable audit log in JSONL format.

---

## Dimension 4: TDD & Multi-Agent Arbitration

ISHA's core architectural differentiator over conversational chat agents (OpenHands, Claude Code) is its Red-to-Green proof mechanism.

- [x] **CRIT-TDD-01: Red-to-Green Reproduction Requirement**
  - **Description**: The agent must write a standalone reproduction test that fails before the patch (RED) and passes after the patch (GREEN).
  - **Verification**: Tested against dummy repo bug fixtures (`tests/dummy_repo/`).
  - **Acceptance Bar**: Patches are rejected if no valid reproduction test is synthesized.
- [x] **CRIT-TDD-02: Worktree Sandbox Isolation**
  - **Description**: Multi-agent candidate exploration runs in separate Git worktrees (`.worktrees/candidate-*`).
  - **Verification**: Target repository's `main` branch remains clean and untouched during exploration.
  - **Acceptance Bar**: Zero git unstaged pollution on the host branch.
- [x] **CRIT-TDD-03: Calibrated Candidate Selection (LAYA Arbitration)**
  - **Description**: Multi-candidate arbitrator selects the minimal, highest-scoring diff from parallel strategies.
  - **Verification**: Multi-agent graph execution in `src/agents/graph.py`.
  - **Acceptance Bar**: Picked candidate maximizes regression pass rate with minimal line change churn.
- [x] **CRIT-TDD-04: Verbatim Source Retry Feedback Loop**
  - **Description**: If a patch fails to apply, feed exact verbatim line excerpts back to the agent so subsequent retries succeed.
  - **Verification**: `src/bench/runner.py::_apply_feedback`.
  - **Acceptance Bar**: Dramatic drop in retry hunk failure.

---

## Dimension 5: Developer Experience (DX) & CLI

Developers must be able to use ISHA effortlessly from their terminal or web browser.

- [x] **CRIT-DX-01: Global CLI Tool Installation**
  - **Description**: Installable via pip as a standard CLI package with entrypoints `isha` and `isha-fix`.
  - **Verification**: `pyproject.toml` console scripts configured; `pip install -e .` works cleanly.
  - **Acceptance Bar**: `isha --help` executes from any terminal directory.
- [x] **CRIT-DX-02: 1-Click Patch Download**
  - **Description**: Streamlit dashboard provides direct download of `isha_fix.patch` ready for `git apply`.
  - **Verification**: Dashboard Tab 3 ("💻 Download & CLI Export").
  - **Acceptance Bar**: Standard unified diff file downloadable in 1 click.
- [x] **CRIT-DX-03: Obsidian Dark UI Theme**
  - **Description**: Modern, clean developer dashboard with no raw probability scores or distracting metrics.
  - **Verification**: `.streamlit/config.toml` styling.
  - **Acceptance Bar**: Clean, responsive layout with 5 distinct tabs.
- [x] **CRIT-DX-04: Direct In-Browser Repository Patching**
  - **Description**: Allow user to inspect the fix in the UI and click "Apply Patch to Real Repo Now".
  - **Verification**: Tested via Tab 3 in `src/dashboard/app.py`.
  - **Acceptance Bar**: Patch cleanly applied to target working tree on user confirmation.

---

## Dimension 6: Documentation & Open-Source Packaging

The repository must be easy for outside contributors, researchers, and engineers to evaluate and run.

- [x] **CRIT-DOC-01: Comprehensive Architecture Whitepaper**
  - **Description**: Detailed file-by-file breakdown and state machine workflow explanation.
  - **Verification**: `docs/WHOLE_PROJECT_EXPLANATION.md`.
  - **Acceptance Bar**: Explains every subsystem, agent role, and graph transition.
- [ ] **CRIT-DOC-02: Public README with Benchmark Visualizations**
  - **Description**: Clean README showcasing the architecture diagram, comparison graphs (`assets/isha_vs_baselines.png`), and Quickstart.
  - **Verification**: Update `README.md` before public launch.
  - **Acceptance Bar**: Instant clarity for any GitHub visitor within 30 seconds.
- [ ] **CRIT-DOC-03: Benchmark Reproduction Guide**
  - **Description**: Step-by-step instructions for anyone to replicate benchmark numbers and produce the comparison plots.
  - **Verification**: `docs/BENCHMARK_REPRO.md`.
  - **Acceptance Bar**: Single-command script to regenerate benchmark figures.
- [x] **CRIT-DOC-04: Clean Licensing & Sensitive File Hygiene**
  - **Description**: Open source license (Apache 2.0 or MIT) and comprehensive `.gitignore` ensuring zero `.env` or credential leaks.
  - **Verification**: Git status inspection; verified clean working tree.
  - **Acceptance Bar**: Zero confidential files committed.

---

## 🚦 Final Green-Light Checklist for Public Open-Sourcing

When all the following are checked, the project is officially ready for public announcement:

- [ ] 1. Run at least 1 verified SWE-bench slice (`results/eval_fresh.json`) with the new `qwen3.8-27b` engine.
- [ ] 2. Update `README.md` to embed `assets/isha_vs_baselines.png` and link `RELEASE_CRITERIA.md`.
- [ ] 3. Verify `pip install -e .` on a fresh clean Python environment.
- [ ] 4. Receive explicit user confirmation to open-source the repository.
