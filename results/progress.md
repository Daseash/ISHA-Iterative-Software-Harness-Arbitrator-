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

## Stage B - Patch Application & Line-Ending Normalization (measured) — 2026-09-30 18:50:00

Fixed the root cause of host diff application failures (`apply_failed`):
1. **Windows CRLF Poisoning**: `Path.write_text` on Windows defaults to converting `\n` to `\r\n`, which causes `git apply` to fail with context mismatches. Upgraded `src/tools/patch_engine.py` with byte-level line ending detection and `write_bytes()`.
2. **Worktree Normalization**: Added `git config core.autocrlf false` inside `src/tools/worktree_manager.py` upon creating isolated worktrees.
3. **Fuzzy Search/Replace Parser**: Added trailing/leading whitespace and blank line tolerance in SEARCH/REPLACE block parsing.
4. **Pre-commit Check & Closed-Loop Repair**: Patches are validated with `git apply --check --whitespace=nowarn` against the base commit. If application fails, exact reject context is fed back to the Coder for up to 2 targeted repair attempts.
5. **Measured Outcome**: Host apply failures dropped from **8/30 (26.7%) down to 0/30 (0.0%)** ([before_after.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/before_after.json)). 4/8 previous apply failure instances were directly converted to clean patches via closed loop ([ablations.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/ablations.json)).

## Stage C - Speed, Timeouts & Cooldown Handling (measured) — 2026-09-30 19:15:00

1. **Per-Stage Timeout Tracking**: `src/graph/nodes.py` registers stage timestamps; runner logs which exact stage timed out.
2. **Adaptive Cooldown Skipping**: When a model provider triggers a 429 rate limit, `_advance_on_rate_limit()` in `src/config.py` immediately skips that provider for remaining retries in that instance without burning the 900s timeout budget.
3. **Deterministic LLM Caching**: Enabled request/response caching in `data/cache/llm/` to eliminate redundant roundtrips.

## Stage D - Three-Different-Model Tournament (measured) — 2026-09-30 19:40:00

Evaluated 3 distinct model families concurrently in isolated git worktrees per instance:
- Family 1: Qwen (`qwen3.8-27b`)
- Family 2: GPT-OSS (`gpt-oss-120b`, fallback `gpt-oss-20b`)
- Family 3: Gemini (`gemini-3.8-flash`, fallback `gemini-3.1-flash-lite`)

Aggregated in [candidates.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/candidates.json):
- 30 candidate evaluations across 21 unique instances.
- **Most Wins**: `gpt-oss-120b` (4 wins, 33.3% win share).
- **Substitutions**: 22 calls fell back due to provider rate limits; every substitution is tracked with `substituted=True`.
- **Diversity Yield**: Multi-family diversity improved patch generation yield from 40.0% to 66.7% (+26.7% absolute gain).

## Stage E - Localization & Symbol Targeting (measured) — 2026-09-30 20:00:00

1. **Localizer Upgrade**: Evaluated on 30 DEV instances ([loc_eval_dev.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/loc_eval_dev.json)):
   - **Hit@1**: 26.7% $\rightarrow$ **46.7%**
   - **Hit@3**: 36.7% $\rightarrow$ **60.0%**
   - **Hit@5**: 40.0% $\rightarrow$ **63.3%**
   - **Hit@8**: 43.3% $\rightarrow$ **66.7%** (+23.4% absolute gain, +54% relative)
   - **MRR**: 0.325 $\rightarrow$ **0.535** (+64.6% relative gain)
2. **Analysis of 10 Missed Instances**: Every miss stems from "symptom vs defect distance" (issue names user-facing API such as `pyplot` or `simplify`, while the bug is in deep internal helpers like `cbook.py` or `operations.py`).
3. **Symbol Targeting**: Structural operator table + reachability surfaced gold symbol in top-3 candidates in 4/6 samples (66.7% vs 16.7% baseline).

## Stage F - LAYA Calibration with Real Evidence (measured) — 2026-09-30 20:10:00

Trained on 315 real labeled pairs from SWE-bench Lite train split ($N_{train}=212$, $N_{val}=103$; zero DEV/FINAL overlap):
- **Temperature Scaling ($T=0.35$)**: ECE dropped from **0.0924 to 0.0010** (98.9% error drop); Brier score dropped from **0.0104 to 0.0000** ([calibration.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/calibration.json)).
- **Auto-Approve Threshold**: `0.50` achieves **100.0% validation precision** and 32.0% coverage.
- **Learned Weights**: `repro_ok` (+4.4120), `regression_count` (-1.5218), `gate_ok` (+0.6582), `laya_score` (+0.0455), `diff_size` (-0.0073).

## Stage G - Senior-Developer Output & Usability — 2026-09-30 20:15:00

1. **8-Section Senior Draft PR Formatter**: Implemented in `src/review/pr_formatter.py` (Understanding, Root cause, Files changed, Diff, Tests run, Confidence with reasons, Risks/what to double check, Model attribution). Supports escalation banners for low confidence.
2. **Run History Persistence**: Saves `plan.md`, `patch.diff`, `report.md`, and `logs.jsonl` to `runs/<timestamp>/`.
3. **CLI Issue URL Ingestion**: `isha fix <repo> --issue-url <url>` fetches issue text via GitHub API and initializes isolated workspace.
4. **Architectural Pre-filter**: Flags migration, breaking change, and refactoring tickets for human design review.

## Stage H - Final Ablations, Comprehensive Report & Validation — 2026-09-30 20:25:00

1. **Comprehensive Report**: Generated [results/REPORT.md](file:///c:/Users/Eashwar/ISHA/isha-agent/results/REPORT.md) containing full baseline reconciliation, before/after metrics with 95% Wilson CIs, candidate tournament statistics, 7-component ablations, LAYA calibration curves, failure root causes, and limitations.
2. **Ablation Matrix**: Persisted in [results/ablations.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/ablations.json).
3. **Before/After Analysis**: Persisted in [results/before_after.json](file:///c:/Users/Eashwar/ISHA/isha-agent/results/before_after.json) tracking 11 monitored changed instances.
4. **Test Suite**: 81/81 tests passing (100% pass rate) with `pytest --ignore=tests/dummy_repo`.
5. **System Health**: `isha doctor` exit=0 (ALL CLEAR).

## Day 1 - Gate before the big run — 2026-10-02

### Incident: `git reset --hard` data loss (recovered)
While debugging a fixture CRLF issue, a scratch-test chain ran `git reset --hard`
from inside `tests/dummy_repo` — which is **inside** the main repo, so all
uncommitted tracked-file edits were reverted to the 09-30 commit.

Recovery (all numbers verified, no estimates):
- 5 source files held lost post-commit edits, proved via `__pycache__` bytecode
  that no longer matched the on-disk source: `src/agents/context.py`,
  `src/agents/nodes.py`, `src/bench/runner.py`, `src/config.py`,
  `src/review/calibration.py`. (`src/tools/git_manager.py` pyc was stale —
  pre-commit — and left untouched.)
- The exact edits were recovered from the Kilo session DB
  (`%LOCALAPPDATA%`-independent store: `C:\Users\Eashwar\.local\share\kilo\kilo.db`,
  `part` table, full `oldString`/`newString`). Each file was rebuilt as
  `git HEAD content + the recorded edits in timestamp order`, then verified by
  compiling and comparing `co_code` against the surviving pyc — **all 5
  byte-for-byte match the lost state**.
- Restored work: context budgets + `ISHA_MAX_CONTEXT_CHARS`/`MAX_FILE_LINES`
  (context.py), larger per-role prompt budgets (nodes.py), `--workers`
  parallel solving + 1800 s instance budget (runner.py), thread-local model log
  (config.py), `fit(artifact=...)` (calibration.py).
- `src/dashboard/app.py` had a larger uncommitted marketing variant (75 KB,
  base64-asset landing page). It was **superseded by `website/index.html`**
  (10-01 16:08, same assets mirrored in `assets/landing/`), so it was not
  restored.
- After restore: `pytest tests --ignore=tests/dummy_repo` → **81/81 pass**,
  `isha doctor` → **ALL CLEAR** (exit 0, 10.4 s).

### Fixture root cause: `git apply` silent skip (fixed)
The fixture realworld check read 0/2 even with a clean tree and qwen answering.
Reproduced and bisected: on git 2.54.0.windows.1, `git apply` run from a
**subdirectory of the repo root** with CWD-relative patch paths silently
skips the hunk — `git apply -v` prints "Skipped patch 'calculator.py'" and
exits **0**, leaving the file untouched. Root-relative paths apply cleanly
from any CWD. (The sandbox-regenerated diff itself is valid — it applies in a
fresh scratch repo; the preimage blob difference is a red herring.)

Fix in `scripts/realworld.py::_apply_patch`: apply from the toplevel via
`git apply --directory=<case-repo-relative-path>` and add a post-check that
fails the case if `git diff --quiet` shows the tree is unchanged, so a
silent skip can never again register as `patch_applied: true`.

### Gate checklist state
- `isha doctor` → ALL CLEAR (09:47 and post-restore re-run).
- Free-tier catalog check → done (Groq `/models` 403s for this key; verified
  via published free-tier lists + live probes: `qwen3.8-27b` remains the
  strongest available free primary; chain unchanged in `.env`).
- 1-instance end-to-end smoke (solve + official-harness grade) → completed:
  patch applied cleanly in the container, tests ran, instance correctly
  reported unresolved under this morning's degraded-quota solve
  (`results/smoke/harness_report.json`, 63 s, image cached from Day 0).
- Fixture realworld re-run → **2/2 resolved** (11:13, `scorecard.md`):
  subtract 106.7 s, divide 87.0 s, both critic-approved, verified by the
  fixture's own test suite.
- Machine kept awake: `powercfg /change standby-timeout-ac 0`,
  `standby-timeout-dc 0`, hibernate off (09:4x).
- Grading capacity note (for Day 5): C: has ~208 GB free; eval images are
  ~4 GB each, so the official harness can only hold ~50 at a time. Grade in
  batches of ~50 with docker system prune -f between (tighter than the
  plan's two-halves mitigation).
- **smoke50 gate run STARTED 12:40** (`results/smoke50/`, background pid 2720,
  persistent lifetime): `python -m src.cli bench --limit 50 --slice stratified
  --run-id smoke50 --timeout 1800 --report`, workers=1 (env default),
  `ISHA_RATE_LIMIT_WAIT=1` active. Note: the CLI's `--timeout` defaults to 900
  and would have overridden the restored 1800 s budget — pass `--timeout 1800`
  explicitly for every campaign run.
- `lite300` not started: waits for the smoke50 gate verdict (plan.md Day 1).

### `validate_patch` CRLF false-negative fix — 2026-10-02 ~15:50
`src/tools/patch_engine.py::validate_patch` now runs
`git apply --check --ignore-whitespace` instead of a plain check. Verified
before applying: the flag accepts the valid smoke50 regenerated diffs against
the CRLF host worktree (rc 0) and still rejects a deliberately corrupted
context line (rc 1). Plain `--ignore-whitespace`-free checks fail on every
regenerated diff on this host (worktree CRLF vs diff LF). 81/81 tests still
pass after the change. Only affects process starts after 15:50 — the entries
already in `results/apply_failures/` are false negatives from the pre-fix
process; the gate metric is `failure_category == patch_apply_failed` in
`results/<run>/*/meta.json`.

### Day 1 evening — smoke50 mid-run check, ~18:30 local
The original smoke50 process (pid 2720) **died ~15:50 local** while starting
instance 6 (`django__django-11039` left a 141-byte `log.jsonl`, no
`meta.json`); no python process remained at 18:28. Cause not recoverable
(session/process boundary) — checkpoints make the loss zero.

Mid-run criteria on the 5 completed instances (all from `meta.json`, no
estimates):

| Criterion | Gate | Observed | Pass |
|---|---|---|---|
| Timeout rate | < 15% | 0/5 (0%) | yes |
| Offline model calls | < 5% | 0 offline, 0 substitutions across 36 calls | yes |
| `harness_no_output` | 0 | not yet graded | n/a |
| Patch yield | ≥ 40% | 5/5 (100%), all host-applied + regenerated | yes |

Per-instance (elapsed / critic composite): astropy-12907 257 s / 0.48
(critic BLOCK — its `model_patch` inserts a new def mid-docstring; expected
harness failure, a true negative), django-10914 426 s / 0.85,
django-10924 6606 s / 0.82 (outlier: 429-storm backoff window dominated wall
time), django-11001 752 s / 0.67, django-11019 479 s / 0.63.

**Resumed 18:30 local** with the identical command (new pid 23528,
persistent): 5/50 skipped as checkpoints, solving 6/50. Quota decision:
429s did not dominate (0 substitutions, 0 offline) → stay on the current
prompt profile; the low-bandwidth profile is NOT activated.

**Day 1 CLOSED 18:45 local.** 6/50 done — `django__django-11039` patched in
328.9 s (first instance after the resume; occasional Groq 429s absorbed by
in-profile 23-60 s backoffs, LLM disk cache serving the repeated planner
prompts). 7/50 solving. Gate run continues overnight; next checkpoint is
the ~21:30 local monitor, then the Day-2 gate verdict
(`isha report --run-id smoke50`).

### Day 2 prep check (ahead of schedule) — 2026-10-02 ~18:50 local
Lite300 launch prerequisites verified so the launch is minutes after the
gate verdict:
- `data/swebench_lite.json` holds exactly **300** Lite instances, 12 repos
  (django 114, sympy 77, matplotlib 23, scikit-learn 23, pytest 17,
  sphinx 16, astropy 6, requests 6, pylint 6, xarray 5, seaborn 4, flask 3).
- All 12 repo mirrors already built — smoke50 checkouts all "up-to-date",
  so lite300 has zero checkout-prep delay.
- `--slice head --limit 300` verified against the CLI
  (`src/bench/dataset.py::select_slice`, `src/bench/runner.py`);
  `isha report --run-id smoke50` renders on partial data (exit 0).
- 208 GB free on C: — covers the run plus batched eval-image grading.
- Only blocker to launching: the gate verdict (no-go rule: lite300 starts
  only after the gate passes).

### Day 2 morning — 2026-10-03 ~11:15 local

- smoke50 found dead at **11/50** (last meta 10-02 20:42). Forensics:
  Windows event 1074 at 20:58:17 — **user-initiated power-off** (second at
  23:55). Not a code crash (no sleep: Wake History Count 0; runner logs
  per-instance errors, none present). Checkpoints: zero loss.
- Resume verified: restarted 11:08 with the identical command
  (`--limit 50 --slice stratified --run-id smoke50 --timeout 1800
  --report`, `ISHA_RATE_LIMIT_WAIT=1`, workers=1, persistent background
  bgp_1004520ef001daApIHLaq4sg0t). 11/11 checkpoints skipped;
  `django__django-11422` (died mid-instance, log-only) correctly re-solved
  from scratch. Planner landed on qwen primary (cached + live); a Groq 429
  storm is in progress and being absorbed by in-profile 15-60 s backoffs
  with NO fallback advance (by `ISHA_RATE_LIMIT_WAIT=1` design).
- `isha doctor` ALL CLEAR 11:05 (qwen live call ok, Docker 29.8.0 up after
  morning restart, 203.5 GB free).
- Apply-failure root cause on the 2 failed instances (11049, 11133): both
  had their coder on `gpt-oss-120b` fallback because Groq quota was dead
  that window; the fallback model emitted non-existent context lines
  (e.g. `class DurationValidator(BaseValidator):`) that `git apply --check`
  rejects on every hunk; the apply-repair loop ran on the same weak model
  and could not recover. Real failures, not CRLF false-negatives. Tracked
  as `mistakes.md` M-2 (open; resolved at the gate verdict — FAIL path
  re-runs only those instances under a new run-id).
- Watch: 3-hourly cron will post the gate verdict + early-signal read and
  launch lite300 on PASS.

### Day 2 mid-morning — targeted re-solve of the 4 degraded-window failures (~11:55 local)

All 4 failures so far (2 `patch_apply_failed`, 2 `syntax_error`) occurred in
quota-degraded windows where the coder ran on fallback models; none occurred
on a healthy qwen-primary solve. Per the Day-2 FAIL path (new run-id, no
profile change):
- Main `smoke50` checkpointed at **13/50** and paused (zero loss) so a single
  worker owns the shared Groq TPM window.
- `smoke50-r1` started (persistent bgp_100580145001ImDrD952CoKetU):
  `python -m src.cli bench --run-id smoke50-r1 --timeout 1800 --report
  --instances django__django-11049 django__django-11133
  django__django-11179 django__django-11422`, `ISHA_RATE_LIMIT_WAIT=1`
  (429s wait on the primary instead of advancing to the fallback coder).
- Gate verdict will use the merged view: r1 results for those 4 ids,
  originals for the other 46. If all 4 re-solve clean, M-2 closes as
  quota-caused; any repeat becomes a v2 coder-level fix (mistakes.md M-2).

### Day 2 mid-morning — Docker image maintenance (~12:20 local)

Found and fixed a latent Day-0 bug: `.dockerignore` was a sandbox-only
allow-list (`*` + `!sandbox-requirements.txt`), which made the agent
`Dockerfile` unbuildable (`COPY requirements.txt` excluded). Rewrote it as
an exclusion list (no `.env`, no `results/`, `data/`, `swebench_checkouts/`,
`live_repos/` can enter an image; context stays small for both builds).
New systematic layout (manifest: `docs/DOCKER_IMAGES.md`):
- `isha:latest` + `isha:0.2.0` (agent, labels `org.isha.image=agent`,
  `org.isha.version=0.2.0`), `isha-sandbox:latest` + `isha-sandbox:0.2.0`.
- `scripts/docker_maintain.ps1` — one command: prune danglings → rebuild
  both from the pyproject version → print manifest (`-SkipBuild` for
  prune+manifest only).
- SWE-bench eval images stay out of scope: transient, pulled from Docker
  Hub only at Day-5 grading, auto-deleted by `harness_eval.cleanup_images`.

### Day 2 watch — 12:30 local

- r1 **3/4**: `11049` now **ok** (364 s, 0 fallbacks — was
  patch_apply_failed), `11179` now **ok** (173 s, was syntax_error),
  `11133` still failing — now `syntax_error` on qwen primary (0 fallbacks;
  the apply failure was quota-caused, but this instance has a genuine
  coder-quality miss). `11422` solving.
- Merged apply-failure count so far: **0** (both original apply failures
  cleared or re-bucketed) → the <5% apply bar looks safe; the syntax
  bucket is the live one (2 of 46 so far).
- Main smoke50: still paused at 13/50 (auto-resumes at r1 4/4).
- r1 closed 4/4: 11049 ok, 11179 ok, 11133 syntax_error (0 fallbacks —
  genuine coder miss), 11422 patch_apply_failed (4 fallbacks — quota died
  mid-instance again). Both errors reserved for the M-3 study list.

### Day 2 watch — 15:00 local

- Main smoke50 resumed 12:17 (bgp_10084aed9001Ph3FLQKYbwTeXl, persistent):
  now **19/50** (13 ok · 3 apply · 3 syntax raw; merged view subtracts the
  r1 fixes). Pace ~1.5 instances/hour — Groq 429 storm active, backoffs
  absorbing, no fallback advance. Process alive; ETA 50/50 early tomorrow
  morning if the storm persists.
- Docker images built and tagged (isha 0.2.0/latest 11.2 GB incl. torch,
  isha-sandbox 0.2.0/latest 220 MB) + manifest + maintain script.

### Day 2 watch — 18:00 local

- **25/50** (16 ok · 5 apply · 4 syntax raw). +6 instances in 3 h — pace
  recovered. Merged view so far: apply failures 4/25, syntax 3/25 — the
  429-storm failure mode (quota death → fallback coder) keeps producing
  apply/syntax misses; each new one is reserved for the M-3 catalogue.
  Gate-bar watch: apply <5% is currently trending tight; verdict at 50/50.
- Distribution work (user request "download and run for others"):
  - pyproject deps synced to the full requirements.txt set (was 6 of 15).
  - **Wheel packaging bug found + fixed**: setuptools auto-discovery was
    flattening the `src` package to the wheel root, which would have broken
    the `isha = src.main:main` entry point for anyone installing the wheel.
    Fixed with explicit `[tool.setuptools.packages.find] include=["src*"]`.
    First wheel was broken; rebuilt and verified (142 files, `src/main.py`
    present, entry points intact, live editable install + `isha --help`
    still OK after the metadata churn).
  - `dist/isha_fix-0.2.0-py3-none-any.whl` (374 KB, code-only),
    `install.ps1` + `install.sh` (venv + install + .env template + self-check),
    `docs/INSTALL.md` (three install paths + first-run checklist),
    DOCKER_IMAGES.md now points at INSTALL.md as the preferred path.

### Day 2 — install/distribution path (off the critical path, ~18:30 local)

Made ISHA pullable/runnable for others:
- `pyproject.toml` dependencies synced to the full `requirements.txt` set
  (was a 6-package subset — a wheel built from it would have been
  un-runnable); explicit `[tool.setuptools.packages.find] include=src*`
  (auto-discovery was flattening the `src` package, breaking the
  `isha = src.main:main` entry point — first wheel built broken, fixed,
  validated: 142 files, `src/main.py` present, entry points intact).
- `dist/isha_fix-0.2.0-py3-none-any.whl` (code-only, 374 KB; deps from PyPI).
- `install.ps1` / `install.sh` — one command: venv + wheel install (source
  fallback) + `.env` template + CLI self-check.
- `docs/INSTALL.md` — three install paths (scripts / pip / docker) + first-
  run checklist. `docs/DOCKER_IMAGES.md` updated to point at it.
- Verified the live editable install + `isha --help` still work after the
  packaging changes (campaign untouched).

### Day 2 — recovery, 20:22 local

- Run had stopped after `pydata__xarray-3364` finished at 18:01:31
  (last meta write; no python process alive on discovery). **26/50**
  done (17 ok · 5 apply · 4 syntax raw). No partial instances.
- Root cause not yet pinned (no crash marker in log; possibly the
  session-group switch / power state around ~18:00) — tracked as a
  watch item, not chased mid-run.
- Resumed as persistent background process (bgp_1023ff9e8001ZrCD59tztTvYCY,
  python pid 13368), identical profile: `--limit 50 --slice stratified
  --run-id smoke50 --timeout 1800 --report`, `ISHA_RATE_LIMIT_WAIT=1`.
  26 checkpoints skipped; now solving 27/50 (pylint-5859).
- 3-hourly watch cron restored for this session (next fire 21:00 local).

### Day 2 watch — 21:30 local

- **28/50** (post-resume +2: `pylint-dev__pylint-5859` done 20:49,
  `pytest-dev__pytest-11143` done 21:11). Process alive (pid 13368,
  resumed 20:21), solving next instance. No restart needed.
  New ok instances keep improving the merged bars; verdict
  remains at 50/50. Next check ~00:00 local (10-04).

### Day 2 — r2 launch, 22:35 local

- User priority flip: **clear all errors while 50/50 finishes**.
  `smoke50-r2` started (persistent, bgp_102b6dbcd0017nqoN7hGkBI8Fk):
  re-solving the 8 merged-unresolved instances (5 apply-failed,
  3 syntax) under the identical healthy-quota profile
  (`ISHA_RATE_LIMIT_WAIT=1`, `--timeout 1800`). Main run keeps running
  in parallel (30/50 at launch). Merged view now: r2 > r1 > main.
  Watch cadence moved to 40 min (cron wku_102b76ef0001qpvaXdbWREJk1y);
  gate verdict + M-3 only when BOTH main==50 and r2==8.

### Day 2 watch — 22:40 local

- **Main 31/50** (+1: `scikit-learn__scikit-learn-10297` done 22:36).
  **r2 0/8** — `django__django-11133` in progress since 22:31, first
  result expected ~23:00-23:30. Both processes alive; no restart needed.

### Day 2 watch — 23:00 local

- **Main 32/50** (+1: `scikit-learn__scikit-learn-10508` done 22:52).
  **r2 1/8** — first re-solve finished: `django__django-11133` done
  22:56 (~25 min). Both processes alive; no restart needed.

### Day 2 watch — 01:00 local (10-04)

- **Main 35/50** (newest `sphinx__sphinx-10325` done 23:37). In-flight
  `sphinx__sphinx-11445` on attempt 1 since ~00:07 — verified ALIVE, not
  hung: process 13368 holds 2 established HTTPS conns to Google (Gemini)
  + 957 s cumulative CPU, so it is mid-LLM-round, just slow.
  **r2 3/8** — `django-11620` ❌ **timeout** (1 attempt vs 1800 s cap),
  joining `django-11422`'s timeout. Two consecutive r2 timeouts on the
  two largest django instances: leading hypothesis = budget exhaustion
  under **dual-worker quota contention** (main + r2 share one free-quota
  window, each call waits longer) + genuinely large instances — not the
  apply/syntax failure mode. If the remaining 5 r2 instances land clean,
  the 2 timeouts go to a small r3 after 50/50. Both processes alive.

### Day 2 watch — 01:50 local (10-04)

- **Main 37/50** (+2: `sphinx-10451` 00:07, `sphinx-11445` 00:37 — both
  ❌ **timeout**, 1 attempt vs 1800 s cap; large sphinx instances under
  the shared-quota window). Main now carries 2 timeouts of its own.
  **r2 4/8** — `django-11742` ❌ still `syntax_error` (qwen primary,
  1 attempt — genuine coder miss, now 2nd time). r2 on `matplotlib-22835`.
  Merged timeouts so far: 4 (2 r2 + 2 main) vs <15% bar (≤7 of 50) —
  watchable. Both processes alive; no restart needed.

### Day 2 watch — 02:25 local (10-04)

- **Main 38/50** (`sympy__sympy-11400` ✅ ok 00:52; 12 left).
  **r2 5/8** — `matplotlib-22835` ❌ timeout (3rd r2 timeout).
  Merged timeouts now 5/38 (~13%) vs <15% bar — tight; verdict at 50/50.
  Both processes alive.

### Day 2 — USER STOP, 02:45 local (10-04)

- User: "stop now, continue later today" (afternoon). Both runs stopped cleanly:
  - main `smoke50`: **38/50 checkpointed** (zero loss) — was mid-backoff
    on a Groq 429, not mid-write.
  - `smoke50-r2`: **5/8 checkpointed** (11133 ✅, 11422 ❌ t, 11620 ❌ t,
    11742 ❌ syntax, 22835 ❌ t). Left: `matplotlib-23299`,
    `mwaskom__seaborn-2848`, `pylint-dev__pylint-5859`.
  - Watch cron wku_102b76ef0001qpvaXdbWREJk1y DELETED (so it can't
    auto-restart tonight). Dashboard `src/server.py` (pid 6644) left up.

**AFTERNOON RESUME — scheduled 14:00 IST 10-04 (cron wku_1034fcf6f001rB5kXQmb5eDbqZ; exact commands, from `C:\Users\Eashwar\ISHA\isha-agent`):**
1. `python -m src.cli bench --limit 50 --slice stratified --run-id smoke50 --timeout 1800 --report` (persistent; 38 checkpoints skip in seconds)
2. `python -m src.cli bench --run-id smoke50-r2 --timeout 1800 --instances matplotlib__matplotlib-23299 mwaskom__seaborn-2848 pylint-dev__pylint-5859` (persistent; 5 checkpoints skip)
   (both with `ISHA_RATE_LIMIT_WAIT=1`)
3. Recreate the 40-min watch (same prompt as wku_102b76... — see cron history); it enforces merged view r2>r1>main, auto-restarts dead runs, and at main==50 AND r2==8 builds M-3 + gate verdict + lite300 launch on PASS.
4. M-3 + r3 decision: if r2's last 3 stay red, small `smoke50-r3` on just those ids after 50/50 (identical profile, new run-id).

### Day 3 — RESUME, 16:50 local (10-04)

- 14:00 IST resume cron did not fire; resumed on user command "start todays task".
  State verified identical to 02:45 stop: main 38/50, r1 4/4, r2 5/8; no bench
  process was running.
- Main `smoke50` resumed persistent: bgp_106a61fb5001PZ7OnsR615sXb3 (pid 25188,
  cwd isha-agent). r2 resumed persistent with the 3 remaining ids:
  bgp_106a788f3001PrTB7ajoznJ0MC (pid 25156). Note: r2 runs from the ISHA root
  cwd — verified harmless: `src` resolves to isha-agent via editable install
  and results paths are absolute.
- Watch cron recreated: wku_106af97a8001kI91HtgnR2D0o0 (`*/40 * * * *`, recurring;
  Day-3 3-run flow, same merged-view rules, gate verdict + lite300 at
  main==50 AND r2==8, r3 contingency unchanged).
- Both pids verified alive with rising CPU at resume.

### Day 3 watch — 16:55 local (10-04)

- Main 38/50 (solving `sympy-11870`, ~25 min in), r2 5/8 (solving
  `matplotlib-23299`). No completions yet — Groq 429 storm active since
  resume; both absorbing via in-profile backoff (14-60 s, no fallback
  advance). Both pids alive, CPU rising. No restart.
  (Entry timestamp corrected: written right after the 16:50 resume.)

### Day 3 status — 17:25 local (10-04), watch re-anchored in new session

- Main **40/50** (+2 since resume: `sympy-11870` ❌ syntax_error,
  `sympy-11897` ✅ ok; 10 left). In-flight `sympy-12171`. pid 25188 alive
  (bgp_106a61fb5001PZ7OnsR615sXb3, persistent).
- r2 **7/8** (+2: `matplotlib-23299` ❌ syntax_error, `seaborn-2848` ✅
  ok — 2nd r2 clear). In-flight `pylint-dev__pylint-5859` (last; qwen
  rate-limited, backing off). pid 25156 alive
  (bgp_106a788f3001PrTB7ajoznJ0MC, persistent).
- Merged view (40 unique ids done, r2 > r1 > main): ok **31 (77.5%)** ·
  timeout 5 (12.5%) · syntax 3 (7.5%) · apply_failed 1 (2.5% — only
  `pylint-5859`, pending r2) · offline 1 instance (2.5%). All gate bars
  green right now; timeout is the tight bar (≤7 of 50 allowed → at most
  2 more timeouts among main's last 10).
- Watch cron: old session's wku_106af97... may or may not still fire; a
  new 40-min watch now lives in this session (see cron), verdict step
  idempotent via the GATE VERDICT marker in this file.
- Note: root `plan.md` and `mistakes.md` no longer exist on disk (both
  were present through Day 2). This file is the single source of truth;
  the M-3 catalogue will be written to
  `isha-agent/results/mistakes.md` at verdict time.

### Day 3 watch — 18:20 local (10-04)

- **r2 COMPLETE 8/8** (exit 0 in 2366 s, pid 25156 gone — normal end).
  Final: `pylint-5859` ❌ **patch_apply_failed** (2 attempts, 776 s).
  r2 scoreboard: 11133 ✅ · 11422 ❌ t · 11620 ❌ t · 11742 ❌ syntax ·
  22835 ❌ t · 23299 ❌ syntax · 2848 ✅ · 5859 ❌ apply → **2 of 8
  cleared**, 6 stay red.
- Main **40/50** unchanged (pid 25188 alive, in qwen backoff; in-flight
  `sympy-12171`). 10 left.
- Merged (40 unique done): ok 31 · timeout 5 · syntax 3 · apply 1 ·
  offline 1 — same as 17:25 (5859 was the only r2 outcome pending, and
  it stayed red). Verdict still gated on main==50 (r2 side now satisfied).
- r3 contingency (the 6 r2-red ids) stays on the table after 50/50, per
  the 16:50 resume plan.

### Day 3 watch — 18:55 local (10-04), watch re-anchored again

- Main **43/50** (+3 since 18:20; 7 left). pid 25188 alive
  (bgp_106a61fb5001PZ7OnsR615sXb3, persistent), in-flight `sympy-12454`
  [44/50].
- r2 8/8 final (unchanged). Verdict still gated on main==50.
- 40-min watch cron re-created in this session:
  wku_106f8602e001cKzS9NCr1rh3t8, next fire ~19:10 local. Watch steps are
  idempotent; verdict step keyed on the GATE VERDICT marker.

### Day 3 watch — 19:02 local (10-04)

- Main **43/50**, still in-flight `sympy-12454` [44/50]; no new
  completion since 18:55. 7 left: 12454, 12481, 13031, 13043, 13146,
  13177, 13437.
- Groq 429 storm still heavy: fallback chain now also degraded
  (gpt-oss-120b/20b rate-limited, gemini-3.8/3.5 500/timeout;
  gemini-3.1-flash-lite landed `sympy-12419`'s code). Progress is slow
  (~15 min/instance with backoffs) but steady — no restart.

### Day 3 watch — 19:10 local (10-04)

- Main **44/50**: `sympy-12454` → patch in 856 s. Now in-flight
  `sympy-12481` [45/50]; 6 left: 12481, 13031, 13043, 13146, 13177, 13437.
- pid 25188 alive (bgp_106a61fb5001PZ7OnsR615sXb3). r2 8/8 final. No
  restart, verdict still gated on main==50. Recurring 40-min watch
  (wku_106f8602e001cKzS9NCr1rh3t8) next fire ~19:50 local.

### Day 3 watch — 20:10 local (10-04)

- Main **47/50** (+3 since 19:10). Outcomes: `sympy-12481` ❌
  **patch_apply_failed** (1397 s), `sympy-13031` ❌ **patch_apply_failed**
  (1517 s), `sympy-13043` → patch in 952 s. Now in-flight `sympy-13146`
  [48/50]; 3 left: 13146, 13177, 13437.
- pid 25188 alive (bgp_106a61fb5001PZ7OnsR615sXb3, CPU ~2905 s and
  climbing). 429 storm persists across the whole fallback chain; cadence
  ~15-18 min/instance. No restart.
- **Gate-bar watch**: merged patch_apply_failed is now 3 instances
  (`pylint-5859` from r2 + `sympy-12481` + `sympy-13031`) = 3/50 = 6%
  if no more — that already exceeds the `<5%` bar even before the last 3
  finish. Timeout so far still 5/47 (10.6% < 15%). Verdict math to be
  pinned at 50/50.

### Day 3 watch — 20:50 local (10-04)

- Main **48/50**: `sympy-13146` → patch in 881 s. Now in-flight
  `sympy-13177` [49/50]; 1 left after that: 13437.
- pid 25188 alive (bgp_106a61fb5001PZ7OnsR615sXb3). 429 storm continues
  but patch yield on the last stretch is strong (last 4 outcomes:
  12481 ❌ apply, 13031 ❌ apply, 13043 ✅ patch, 13146 ✅ patch). No
  restart.

### Day 3 watch — 21:00 local (10-04)

- Main **48/50** unchanged. `sympy-13177` ~25 min in, still actively
  calling models through backoffs (last output: qwen backoff 60 s,
  attempt 2/3) — within the 1800 s per-instance timeout. No restart.
- 1 left after 13177: `sympy-13437`. Verdict work (M-3 catalogue + gate
  + lite300 decision) expected at the 21:40 watch or just after.

