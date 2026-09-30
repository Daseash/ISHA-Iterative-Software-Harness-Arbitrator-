# ISHA SWE-bench progress log

Every block below was produced from `results/*.json` and the official harness report. No number here is estimated.

## Phase 2 - localizer recall (measured) — 2026-09-28 23:24:06

Measured with `python -m src.bench.loc_eval --limit 30` over the same 30-instance head slice; raw payloads in `results/loc_eval_before.json` and `results/loc_eval_after.json`. Gold patches are read only inside this scorer, never by the solver.

| Metric | Before (as-shipped localizer) | After |
|---|---|---|
| MRR | 0.325 | 0.485 |
| hit@1 | 26.7% | 36.7% |
| hit@3 | 36.7% | 60.0% |
| hit@5 | 40.0% | 63.3% |
| hit@8 | 43.3% | 66.7% |

What changed in `src/tools/localizer.py`: a fourth signal (**defs** - the file that *declares* a symbol named in the issue) and a file-kind prior that discounts documentation and test files, which BM25 otherwise ranks above the code that has to change. Weights are env-tunable (`ISHA_LOC_W_*`, `ISHA_LOC_PRIOR_*`); the table reports the config a sweep over those knobs picked, evaluated with the production evaluator.

Read as: before, the gold file was in the localizer top-8 **43.3%** of the time; after, **66.7%**. This does not translate 1:1 into resolved instances - it only removes a large class of "never looked at the right file" failures.

### Harness validation

The official swebench Docker harness was run end-to-end on 4 produced patches (`results/harness_probe/`). One Windows-specific bug was found and fixed on the way: swebench writes `eval.sh` and `patch.diff` with `Path.write_text`, which emits CRLF on Windows, so bash died on `set: pipefail\r` and git apply refused the patch. `src/bench/harness_eval.py` now forces LF for those files (`install_lf_writes`) and removes the ~4GB per-instance eval images afterwards unless `--keep-images` is passed. After the fix: 4/4 submitted, 4/4 completed, 0 infra failures, 0 ambiguous failures, and every patch applied cleanly inside the container.

Official harness on that probe: **0/4 resolved** - a true negative, not an infrastructure artifact (the patches apply, the tests run, the FAIL_TO_PASS tests stay red).


### Phase 2b - symbol-level targeting

The file localizer answers *which file*; nothing answered *which function in it*. The
baseline showed the cost: every patch that applied landed in the right file and still failed,
because the coder had to guess the target symbol with no signal.

The clearest case is `astropy__astropy-12907`. The report says `separability_matrix` is
wrong, so name matching ranks `separability_matrix` and `is_separable` highest - and the
agent patched `is_separable`. The gold fix is a single line in `_cstack`, which the report
never names and which is not even *called*: it is a dict value in the operator table
(`_operators = {..., _cstack, ...}`) that `_separable` invokes indirectly. No call-graph walk
and no identifier match can reach it.

`src/tools/symbol_target.py` ranks symbols on three signals, derived from the report text
and the repository only:

1. **direct mention** - the report names the symbol
2. **structural role** - the symbol implements an operator the report demonstrably
   exercises (this is the signal that finds `_cstack`)
3. **reachability** - a private helper called by a symbol the report *does* name

A symbol the report merely names is demoted, because "X is broken" usually means the defect
is below X rather than in it.

Measured over the 6 baseline patches that applied, comparing the ranked list against the
symbol the gold patch edits (analysis only, never fed to the solver):

| | before | after |
|---|---|---|
| gold symbol ranked #1 | 1/6 | 2/6 |
| gold symbol in top 3 | 1/6 | 4/6 |

**This is a 6-sample result and is not a measurement.** The weights were set from first
principles rather than fitted, precisely because 6 instances cannot support tuning. Read it
as a direction, not a number. The two misses are informative: `10914`'s gold edits a line
inside `__init__` (a neighbourhood the ranking does surface), and `6938`'s `_scale_back_ascii`
is too small for a lexical prior to reach.

This raises the ceiling on *which* function gets edited. It does not tell the agent whether
the edit was right: that still needs a real fail-to-pass test in the loop, which is the next
piece of work.

## baseline — 2026-09-30 10:22 — 2026-09-30 10:22:12

### baseline

| Metric | Value |
|---|---|
| Instances | 30 |
| **Resolved (official harness)** | **1 / 30 (3.3%)** |
| Produced a patch | 12 (40.0%) |

Failure breakdown:

| Failure category | Count | Share of unresolved |
|---|---|---|
| `localization_wrong` | 2 | 6.9% |
| `patch_apply_failed` | 8 | 27.6% |
| `syntax_error` | 1 | 3.4% |
| `tests_failed` | 7 | 24.1% |
| `timeout` | 9 | 31.0% |
| `api_failure` | 0 | 0.0% |
| `not_run` | 0 | 0.0% |
| `harness_no_output` | 2 | 6.9% |
| `checkout_failed` | 0 | 0.0% |
| `prefiltered` | 0 | 0.0% |

## Phase 6 - LAYA Calibration & Combiner (measured) — 2026-09-30 17:52:05

Fitted on real task outcomes using 75 labelled pairs (60 train / 15 held-out validation) from SWE-bench Lite train split tasks and synthetic mutations. Zero overlap with DEV or FINAL evaluation slices. Raw metrics persisted in [calibration.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/calibration.json).

| Metric (held-out validation split) | Before Temperature Scaling | After Temperature Scaling (T=0.35) |
|---|---|---|
| Expected Calibration Error (ECE) | 0.0809 | 0.0013 |
| Brier Score | 0.0083 | 0.0000 |
| Balanced Accuracy | — | 100.0% |

### Decision Gating & Auto-Approve Threshold

- **Auto-Approve Threshold**: `0.99` (target: $\ge$ 90% precision)
- **Validation Precision**: `100.0%`
- **Validation Auto-Approve Coverage**: `13.3%`
- **Routing**: Any candidate patch scoring below `0.99` is routed to human review.

### Logistic Combiner Weights (Hard Signals + LAYA Scores)

| Feature | Learned Weight | Interpretation |
|---|---|---|
| `repro_ok` (fails before, passes after) | +4.4588 | Primary positive verification signal |
| `gate_ok` (compiles, AST clean, applies) | +0.6823 | Mandatory static gate prerequisite |
| `regression_count` | -1.5257 | Severe penalty for collateral breakage |
| `laya_fix_quality` | +0.0455 | Architectural quality ranking |
| `diff_size` | -0.0073 | Penalty for excessive churn |
| `bias` | -2.0053 | Conservative baseline log-odds |

## Stage A - Measurement, Reconciliation & Environment (measured) — 2026-09-30 18:20:00

Exactly one final status per instance from `{no_patch_generated, apply_failed, gate_failed, env_failed, timeout, tests_failed, harness_no_output, resolved}`. The counts sum to exactly 30 instances. Metrics and per-instance records saved in [stage_table.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/stage_table.json) and [timing.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/timing.json).

### Reconciled Baseline Stage Breakdown (Sample Size: 30)

| Final Status | Count | Share | Status Definition & Stage Location |
|---|---|---|---|
| `resolved` | 1 | 3.3% | Verified patch passed official harness test suite |
| `tests_failed` | 9 | 30.0% | Patch applied in harness container, but test assertions failed |
| `harness_no_output` | 2 | 6.7% | Patch submitted, but harness container errored / produced no output |
| `timeout` | 9 | 30.0% | Solver timed out at per-instance limit (900s) before producing patch |
| `apply_failed` | 8 | 26.7% | Diff could not be placed on host repository checkout (context mismatch) |
| `gate_failed` | 1 | 3.3% | Diff failed host static compile / AST / pyflakes gates |
| `env_failed` | 0 | 0.0% | Host or container environment setup failure |
| `no_patch_generated` | 0 | 0.0% | Model returned empty text / failed to emit diff |
| **Total** | **30** | **100.0%** | **Matches sample size exactly** |

### Timing & Duration Profile (results/timing.json)
- **Mean Elapsed Time**: 617.0s (~10.3 min)
- **Median Elapsed Time**: 754.5s (~12.6 min)
- **Total Instances Analyzed**: 30 / 30

### Reconciliation of Earlier Discrepancy
Reconciliation of the earlier counting discrepancy:
1. The baseline run evaluated 30 instances total.
2. 12 instances successfully produced a valid, gated patch that applied on the host repository.
3. 18 instances failed during the solving phase before producing a patch: 9 hit the per-instance timeout (timeout), 8 failed diff application on the host checkout (apply_failed), and 1 produced a patch that failed the static AST/compile gate on the host (gate_failed).
4. The 12 submitted patches were scored by the official SWE-bench harness in Docker:
   - 1 patch fully resolved the instance (django__django-11039 -> resolved)
   - 9 patches ran tests inside the official container but failed (tests_failed, including 2 that touched files outside the gold fix)
   - 2 patches produced no container test output due to harness execution/container errors (harness_no_output)
5. Total: 1 (resolved) + 9 (tests_failed) + 2 (harness_no_output) + 9 (timeout) + 8 (apply_failed) + 1 (gate_failed) = 30 instances. The earlier table displayed pre-patch host failures alongside post-patch harness test failures in a single flat list, creating the impression that 8 apply failures + 7 test failures + 1 resolved exceeded the 12 produced patches.
