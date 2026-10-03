# ISHA Pipeline Specification

This document is the authoritative description of ISHA's internal process: every
stage, what it reads, what it writes, its budgets, and how to debug it when it
misbehaves. If code and this document disagree, the code wins — then fix the
document in the same change.

---

## 1. The two pipeline variants

| Variant | Entry | Graph | Used by |
|---|---|---|---|
| **Core loop** | `isha fix`, `isha --issue …`, dashboard, bench runner | `compiled_graph` (`src/agents/graph.py:154`) | Everything except `--multi` |
| **Multi-agent tournament** | `isha fix --multi` | `compiled_multi_graph` (`graph.py:302`) | Interactive use where 3 strategies race in 3 git worktrees |

Both share the first six stages; they diverge at fan-out.

---

## 2. Stage contracts (core loop)

```
investigation → decomposer → planner → confidence_gate →
regression_test → coder → candidates → sandbox →(fail, budget left)→ coder
                                              └────────(else)──────→
        critic → approval →(more sub-issues)→ planner
                        └────────(done)─────→ checkpoint → END
```

### 2.1 Investigation — `src/agents/investigation.py`
- **In:** `issue_text`, `repo_path`
- **Out:** `investigation_report` (baseline test run, keyword grep hits, suspect-file
  excerpts, blast-radius report). Prepends itself to `repo_context`.
- **Budget:** baseline pytest is skipped in bench mode (host has no SWE-bench env).
- **Failure behaviour:** every sub-step is try/except-wrapped; a dead step degrades
  to "skipped" text, never a crash.

### 2.2 Decomposer — `src/agents/decomposer.py`
- **In:** `issue_text`, `repo_context`, `investigation_report`
- **Out:** `sub_issues[]`, `current_sub_issue_index`
- **Behaviour:** splits a big issue into 1–3 atomic sub-issues. One LLM call
  (`call_planner`). In bench mode the call is short-circuited to a single
  sub-issue (byte-identical to a 1-item answer, zero quota cost); force the LLM
  with `ISHA_DECOMPOSE_IN_BENCH=1`.

### 2.3 Planner — `src/agents/nodes.py:planner_node`
- **In:** issue + plan-relevant context (clip `ISHA_PLANNER_CONTEXT_CHARS`)
- **Out:** `plan`, `planner_confidence` (0–1), `localization` (target file)
- **Budget:** one chain call; tool-call markup is stripped from model output.

### 2.4 Confidence gate — `nodes.py:confidence_gate_node`
- **In:** `planner_confidence`, `ISHA_CONFIDENCE_THRESHOLD`
- **Out:** either `escalation` (→ straight to approval/human) or proceed.
- **Bench mode:** threshold is forced to 0 (`runner.apply_bench_env`) because there
  is no human; low confidence is *recorded*, not fatal.

### 2.5 Regression test (RED) — `nodes.py:regression_test_node`
- **In:** issue + context (clip `ISHA_REGRESSION_CONTEXT_CHARS`)
- **Out:** `regression_test` — a pytest test that must **fail** on current code.
- This is the TDD anchor: no patch ships without a repro that went RED.

### 2.6 Coder — `nodes.py:coder_node`
- **In:** plan, regression test, target-file code (clip `ISHA_CODE_BLOCK_CHARS`),
  repo context (clip `ISHA_CODER_CONTEXT_CHARS`), verbatim apply-failure feedback
  from earlier attempts (`context_notes`, last 8 entries, clip `ISHA_HINT_CHARS`)
- **Out:** `patch` (unified diff), `retry_count` incremented on loop-back
- **Retry loop:** sandbox failure → back to coder, up to `MAX_RETRIES = 3`
  (`graph.py:28`).

### 2.7 Candidates — `nodes.py:candidate_node` / `src/agents/candidates.py`
- **In:** coder's patch
- **Out:** `candidates[]` (0–3 model answers) and the best one kept in `patch`
- **Behaviour:** when `ISHA_CANDIDATES ≥ 2`, N *different model families*
  re-derive the fix in parallel threads and the arbitration module ranks them by
  LAYA composite score + diff churn. Each candidate thread records its own model
  log entries (per-thread log — see §4).

### 2.8 Sandbox — `nodes.py:sandbox_node`
- **In:** `patch` applied to a scratch copy of the repo
- **Out:** `test_output` (pytest PASS/FAILED of the regression test + repo tests)
- **Budget:** `src/tools/sandbox.py:DEFAULT_TIMEOUT = 180 s`; bench mode uses
  static gates instead of local pytest (`ISHA_SANDBOX_MODE=local` default, the
  harness container is the authority in bench mode).

### 2.9 Critic — `src/review/critic.py`
- **In:** patch + repo + `repro_ok`/`gate_ok`/`regression_count` hard signals
- **Out:** `critic_verdict` ∈ {`approved`, `low_quality`, `flagged`},
  `critic_score`, `laya_scores`
- **Behaviour:** LAYA (`src/review/laya_judge.py`) scores patch quality and danger;
  guardrail secret scan and security checklist can force `flagged`.

### 2.10 Approval — `src/approval/gate.py`
- **In:** verdict + calibrated LAYA probability
- **Out:** `approved: bool`, an immutable line in `output/approvals.jsonl`
- **Behaviour:** auto-approve when calibrated probability ≥ threshold; CLI prompts;
  dashboard uses a LangGraph `interrupt()` so the button resumes the exact state.

### 2.11 Checkpoint — `graph.py:checkpoint_node`
- **Out:** session snapshot under `output/sessions/` + progress ledger.

### Multi-agent variant (fan-out)
`regression_test` → `dispatch_agents` (`src/agents/dispatch.py`) fans out via
LangGraph `Send` to `attempt1/2/3`, each a full coder→sandbox→retry chain inside
its **own git worktree** (`src/tools/worktree_manager.py`, `core.autocrlf=false`),
each with a **different strategy** (`minimal_diff`, `call_site_aware`,
`alt_test_phrasing`). `arbitration_node` ranks all passing attempts by LAYA
composite, then churn; `merger_node` applies the winner to the real repo and
deletes losing worktrees.

---

## 3. Benchmark run pipeline (`src/bench/runner.py`)

```
load slice (agent fields only) → prefilter → checkouts →
per instance: graph → canonical_patch (apply on clean tree, regenerate with git)
             → checkpoint meta.json → retry-with-verbatim-feedback on apply failure
write predictions.json → optional official Docker harness (harness_eval.py)
→ report.py (Wilson CIs, stage table, timing)
```

Invariants (these are what make the numbers publishable):
- The solver never sees `gold_patch` / `test_patch` (`dataset.agent_view`).
- Slices are seed-fixed and disjoint (`data/splits.json`, seed 42); the FINAL
  slice is off-limits for tuning.
- Prefiltered instances stay in the denominator.
- Every number in `results/*.json` is derived from per-instance `meta.json`
  (`report.py`) — nothing hand-entered.
- Checkpoints make every run resumable: same `--run-id` skips finished instances.

---

## 4. Threading model (v0.3.0)

- The model-usage log in `src/config.py` is **per-thread** (`threading.local`):
  parallel instances and parallel candidates never overwrite each other's audit
  trail. `clear_model_log()` resets only the calling thread.
- The bench driver solves instances with `--workers N` (default 1). With N > 1 the
  shared provider TPM window is split N ways — only raise N when you hold
  multiple provider accounts.
- Each worker uses its own scratch sandbox and its own per-instance checkout;
  `reset_checkout` is per-instance, so worktrees never collide.

---

## 5. Limits & budgets (v0.3.0 defaults, all env-tunable)

| Knob | Default | Env | Notes |
|---|---|---|---|
| Repo-context assembly cap | 40 000 chars | `ISHA_MAX_CONTEXT_CHARS` | sections dropped lowest-value-first |
| Planner context clip | 10 000 | `ISHA_PLANNER_CONTEXT_CHARS` | |
| Regression context clip | 6 000 | `ISHA_REGRESSION_CONTEXT_CHARS` | |
| Coder repo-context clip | 4 000 | `ISHA_CODER_CONTEXT_CHARS` | |
| Issue text in coder prompt | 6 000 | `ISHA_ISSUE_CHARS` | was 3 000 — long SWE-bench bodies lost their tracebacks |
| Code block in coder prompt | 8 000 | `ISHA_CODE_BLOCK_CHARS` | target file content |
| Apply-failure feedback | 8 000 | `ISHA_HINT_CHARS` | verbatim source around the failed hunk |
| Planner aux block | 5 000 | `ISHA_PLANNER_AUX_CHARS` | |
| Instance wall-clock | 1 800 s | `ISHA_BENCH_INSTANCE_TIMEOUT` | was 900 s (~30% of DEV died on it) |
| Parallel instances | 1 | `ISHA_BENCH_WORKERS` / `--workers` | |
| Coder retry rounds | 3 | `MAX_RETRIES` (graph.py:28) | |
| Candidate repair rounds | 2 | `MAX_REPAIR_ROUNDS` (candidates.py:31) | |
| Sandbox pytest timeout | 180 s | `sandbox.py:DEFAULT_TIMEOUT` | |
| Local verify timeout | 600 s | `verify.py:DEFAULT_TIMEOUT` | |
| LLM call budget | 300 s | `ISHA_CALL_BUDGET` | per chain call, then advance |
| Rate-limit backoff | 40 s ×2^n (cap 120) | `_BACKOFF_SECONDS` (config.py:201) | |
| Prefilter issue length | 40–40 000 chars | `prefilter.py:20-21` | |

**Low-bandwidth profile** (the pre-0.3.0 defaults that produced the DEV-slice
numbers; needed only for exact reproduction of historical runs):

```
ISHA_MAX_CONTEXT_CHARS=12000 ISHA_PLANNER_CONTEXT_CHARS=5000 \
ISHA_REGRESSION_CONTEXT_CHARS=3500 ISHA_CODER_CONTEXT_CHARS=900 \
ISHA_ISSUE_CHARS=3000 ISHA_PLAN_CHARS=2000 ISHA_CODE_BLOCK_CHARS=5100 \
ISHA_HINT_CHARS=4000 ISHA_PLANNER_AUX_CHARS=2500 \
ISHA_BENCH_INSTANCE_TIMEOUT=900
```

---

## 6. Debugging guide — symptom → where to look

| Symptom | First check | Evidence |
|---|---|---|
| Instance dies at the timeout | `meta.json → error`; count `[model]` lines with `position=fallback N` in `log.jsonl` — long chains mean rate limits ate the budget | `results/<run>/<instance>/log.jsonl` |
| `patch_apply_failed` | `results/apply_failures/<instance>_<c>_<round>.json` + `raw.patch`; the retry already fed verbatim source back — check whether `context_notes` grew | runner `_apply_feedback` (runner.py:248) |
| `tests_failed` (patch applied, assertions fail) | the fix is wrong, not broken: read `plan.md` + `test_output` in the instance dir; compare `localization` vs the gold file only *after* the run | `meta.json → localization`, `classify.py` |
| `localization_wrong` | localizer recall for that instance: `python -m src.bench.loc_eval --run-id <id>`; check `impact.affected_files` vs gold file | `results/loc_eval_*.json` |
| Planner low confidence / escalation | `meta.json → planner_confidence`, `escalation`; bench forces threshold 0 so this should not block | `confidence_gate_node` |
| RED test doesn't actually fail before the patch | run `regression_test` from `meta.json` against the pristine checkout manually | `regression_test_node` |
| Candidate threads attribute the wrong model | model log is per-thread now; verify `thread` field in `meta.json → model_log[]` | `config._log_model` |
| Parallel run shows interleaved model logs | `--workers` splits the shared TPM window — logs are correct, throughput just drops; lower N | runner §4 |
| CRLF / harness aborts | `install_lf_writes` is active for harness containers; check for `harness_no_output` in the stage table | `harness_eval.py:50` |
| LAYA gate looks suspicious | read `data/laya_combiner.json` provenance; labels in `data/laya_labels.jsonl` are synthetic (see §7) until the full run relabels them | `src/review/calibration.py` |

Re-run a single instance without touching the rest of a run:

```
python -m src.bench.runner --run-id <run-id> --instances <instance_id>
```

(its checkpoint dir must be deleted first: `rm -rf results/<run-id>/<instance_id>`).

---

## 7. Known provenance caveats (read before citing numbers)

1. **DEV-slice numbers** (30 instances) were produced with the low-bandwidth
   prompt profile and the 900 s timeout. The full-300 run uses the v0.3.0
   defaults above; the two runs are not directly comparable instance-for-instance.
2. **LAYA label set is synthetic** until `src/bench/relabel_laya.py` rebuilds it
   from real harness outcomes. The calibration metrics in
   `results/calibration.json` are valid *against that label set*, and the label
   set is documented as synthetic — do not cite them as measured on real data.
3. **LAYA itself is remote** (`laya.load("convaiinnovations/laya")` from the HF
   hub); a hub outage degrades the critic to the hard-signal-only path.
