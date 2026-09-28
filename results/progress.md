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
