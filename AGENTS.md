# ISHA: Iterative Software Harness Arbitrator — Agent Architecture & Operational Directives

## 1. Core Mission & Philosophy
ISHA is an autonomous software engineering and benchmark harness arbitrator designed to achieve peak resolution on SWE-bench Lite (300 benchmark), SWE-bench Verified (500 instances), and SWE-bench Full.

**The Golden Rules**:
- **Ponytail Principle**: Shortest working diff wins. Never refactor, reformat, rename, or add unrequested scaffolding. Bug fix = root cause, not symptom.
- **Audited Ground Truth**: Generating a patch is not a score. Applying a patch is not a score. Only patches that pass official test suites inside Docker containers (`report.json`) count as **RESOLVED**.
- **Continuous Alignment**: Benchmark predictions and audited test results are continuously synced to GitHub `origin main`. Environment configurations (`.env`) and local working plans (`plan.md`) remain strictly local.

---

## 2. Non-Negotiable Operational Invariants: The 8 Container Invariants
When generating code patches for SWE-bench benchmarks or repository bugs:
1. **Class Anchoring**: Insert new methods/properties into the EXACT enclosing target class, NEVER an earlier class or helper.
2. **Guard Clause Completeness**: Always check `if val is None:` before accessing attributes or calling `len(val)`. Calling `len(None)` raises `TypeError`. Always guard against `None`, empty containers, or missing keys before slicing or querying.
3. **Hashability Contracts**: Never place mutable collections (`list`, `dict`, `set`) into sets, dictionary keys, or identity tuples without calling `make_hashable(...)` or converting to an immutable tuple.
4. **Decorator Preservation**: When wrapping callables or modifying decorators (`functools.partial`), always wrap with `functools.wraps(...)` to preserve function introspection (`__name__`, `__doc__`, `__wrapped__`).
5. **Execution Scope & Namespaces**: In dynamic code execution (`exec`, `eval`), always provide an explicit global namespace with `{'__name__': '__main__'}` so top-level imports and closures resolve properly.
6. **Accessibility & Widget Contracts**: In forms and widgets, `id_for_label` must return `''` or `None` if the widget has composite or multiple sub-widgets without a single focus target.
7. **Type & Return Invariants**: Strictly preserve exact return types and falsy distinctions (`None` vs `''` vs `0` vs `False`). Never coerce `None` to `''` or drop empty strings unless explicitly required.
8. **Qualname Hierarchy**: When serializing nested classes or methods, always use `__qualname__` to preserve full enclosing scope hierarchy.

---

## 3. Multi-Candidate Tournament & Verification Pipeline
Every task instance runs through an autonomous tournament:
1. **3 Diverse Candidate Strategies (`--candidates 3`)**:
   - `minimal_diff`: Surgical, low-temperature, AST-focused diffs.
   - `call_site_aware`: Call-site inspection, caller graph validation.
   - `root_cause_first`: Root-cause invariant enforcement.
2. **AST Static Compilation Gate**: Every candidate is compiled and linted in isolated worktrees before submission.
3. **Baseline Repro Gate (`baseline_red_gate_node`)**: Requires generated repro tests to fail before patching, discriminating actual test failures (`\b[1-9]\d* failed\b`) from collection errors.
4. **Targeted Repair Rounds**: If a candidate fails in-loop verification, the real pytest error traceback is fed back to the coder for up to 2 targeted repair rounds.
5. **Candidate Arbitrator**: The arbitrator scores surviving candidates and selects the cleanest winning patch.

---

## 4. Benchmark Session Map (SWE-bench Lite 300)
The 300 benchmark instances are partitioned into 10 sequential 30-instance sessions:
* **Sessions 1–4**: Completed and officially audited in Docker (**66 / 120 resolved — 55.0%**).
* **Sessions 5–7**: Completed and officially audited in Docker (**72 / 210 resolved — 34.3%** cumulative).
* **Sessions 8–10**: Slices pre-generated under `data/slices/` (90 instances across `sphinx-doc` and `sympy`).
* **Session 8 (`lite300-s8`)**: Currently executing in the background in local tournament mode.
* **Scoreboard Engine**: `python scripts/score.py` provides the single source of truth (SSOT) terminal scoreboard.
* **Orchestration Driver**: `python scripts/orchestrate_all.py` drives autonomous execution with multi-candidate tournaments and automatic rescue loops (`-r2`).

---

## 5. Architectural Map for External Agents & Models
If you are an external AI model (Claude, GPT, DeepSeek, etc.) or developer making changes to ISHA, here is how the system is structured:

```text
src/
├── agents/
│   ├── graph.py              # Main LangGraph cyclic state machine
│   ├── nodes.py              # Nodes: localizer, planner, tournament coder, red/green verifier, repair loops
│   ├── candidates.py         # Multi-candidate tournament (minimal_diff, call_site_aware, root_cause_first)
│   ├── state.py              # Pydantic v2 AgentState schema passed across all nodes
│   ├── dispatch.py           # Multi-worker parallel session runner
│   └── fix_history.py        # Vectorized memory of successful bug patterns
├── approval/
│   ├── gate.py               # LAYA Calibrated Decision Gate (ECE = 0.0010, temperature scaled)
│   ├── calibrator.py         # Platt & temperature scaling calibration
│   └── danger.py             # Safety & destructive pattern guards
└── bench/
    ├── harness_eval.py       # Official SWE-bench Docker testbed wrapper (report.json parser)
    ├── classify.py           # Post-eval failure taxonomy & error categorization
    ├── make_plots.py         # Matplotlib figure generator for benchmarks
    └── run_slice.py          # Runner for arbitrary benchmark slices
```

---

## 6. CLI Commands Reference for External Agents
- **View Single Source of Truth Scorecard**:
  ```bash
  python scripts/score.py
  ```
- **Run Unit Tests (Purely offline, safe)**:
  ```bash
  pytest tests/
  ```
- **Run Benchmark Tournament on a Session Slice**:
  ```bash
  python scripts/run_lite300.py --session 8 --candidates 3
  ```
- **Run Post-Evaluation Failure Classification**:
  ```bash
  python -m src.bench.classify --predictions results/lite300-s8/predictions.json
  ```
- **Run Official Docker Evaluation** (⚠️ *Only when user explicitly asks for Docker evaluation*):
  ```bash
  python -m src.bench.harness_eval --predictions results/lite300-s8/predictions.json --dataset-slice data/slices/lite300-s8.json
  ```

---

## 7. Container & Git Hygiene
- **LF Line Endings**: All files shipped into Docker (`eval.sh`, `patch.diff`, `test_output.txt`) must strictly use POSIX LF (`\n`) and UTF-8 encoding.
- **Offline Safety**: CI test suites run purely offline with `ISHA_FORCE_OFFLINE=1` (`pytest tests/`).
- **Secret & Plan Isolation**: API keys in `.env` and local working plans (`plan.md`) must never be committed or staged to Git.
- **Continuous GitHub Sync**: All code improvements, documentation, and predictions are committed and pushed to `origin main` on `https://github.com/Daseash/ISHA-Iterative-Software-Harness-Arbitrator-`.

