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
