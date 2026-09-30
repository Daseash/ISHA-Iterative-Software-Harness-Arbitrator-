<USER_REQUEST>
Make ISHA a reliable, measurable senior-developer assistant: it takes a bug report and
a repo, and hands back a tested, reviewed, explained draft fix for human approval.
Do NOT change model names or fallback chains in config.py. Inspect the current code
first and build on what works; do not rewrite working parts. Work in stages. After
each stage: run the DEV slice, save results, record before/after in results/progress.md,
fix or revert anything that regressed, then STOP and report before the next stage.

## GROUND RULES
- Every number in README/docs must come from a saved file in results/*.json. Generate
  tables from those files; never type numbers by hand.
- Never read gold patches, test patches, or FAIL_TO_PASS/PASS_TO_PASS during solving.
- Use the same 30-instance DEV slice for before/after (data/splits.json, fixed seed).
  Never tune on the FINAL slice. Run FINAL once, at the very end.
- Print sample size, resolved count, and a 95% Wilson interval with every rate.
- Log the model that ACTUALLY answered every call, and whether a fallback replaced it.
- Remove any doc claims that were not measured.

## STAGE A: MEASUREMENT AND RECONCILIATION
- Write results/stage_table.json: exactly one final status per instance from
  {no_patch_generated, apply_failed, gate_failed, env_failed, timeout, tests_failed,
  harness_no_output, resolved}. Counts must sum to the sample size. Explain why the
  earlier counts did not add up (12 patches vs 8 apply + 7 test failures + 1 resolved).
- Record per-stage timing for every instance (results/timing.json).
- Environment: run everything in WSL2 + Docker on the Linux filesystem, not /mnt/c.
  Use SWE-bench per-instance images for candidate testing. Pre-pull and cache them.
- `isha doctor`: checks keys, model reachability, WSL/Docker, Qdrant, git, disk.

## STAGE B: PATCH APPLICATION (baseline: 8 apply failures)
- Do not submit raw model-written diffs. Apply edits inside each git worktree with
  SEARCH/REPLACE plus fuzzy whitespace matching, then generate the final patch with
  `git diff`.
- Validate every patch with `git apply --check` on a clean checkout of the base
  commit. On failure, feed the exact error back to the Coder (max 2 retries).
- Preserve original line endings; set core.autocrlf=false in worktrees.
- Save each failing patch and error to results/apply_failures/, classify the cause
  (context mismatch, whitespace, wrong path, line endings, malformed hunk), and fix
  the largest cause first.

## STAGE C: SPEED AND TIMEOUTS (baseline: 9 timeouts, 2 harness no-output)
- Profile where time goes: image pull, env build, LLM calls, 429 cooldown waits, tests.
- For candidate testing, run only the repro test and the touched modules' tests.
  Reserve the full official harness for final scoring.
- Per-stage timeouts with a clear "timeout in <stage>" status.
- Never count 429 cooldown waits against the test timeout; skip cooled-down providers
  and move to a healthy fallback immediately.
- Capture harness stdout/stderr and container exit code for "no output" cases and
  classify them (crash, OOM, empty patch, bad path).
- Limited parallelism (configurable workers, default 2). Cache identical LLM calls.
- Add per-instance token/time budgets and a global daily request budget with a clear
  "budget exhausted" stop. Make runs resumable.

STOP after Stage C. Rerun the 30 DEV instances with the official harness and write
results/before_after.json (resolved, patch generated, apply success, timeouts, tests
failed, with counts and Wilson intervals for baseline vs now) plus the list of
instances that changed status.

## STAGE D: THREE-DIFFERENT-MODEL TOURNAMENT
Use three candidates from three DIFFERENT model families (the ones already configured;
previously three candidates came from the same model).
- All three get identical input: same issue text, same localized context, same prompt.
- Each candidate runs in its own git worktree.
- If a fallback substitutes for a requested model, mark that candidate "substituted"
  and report how many were substituted per run. Do not silently count it as diversity.
- Optional cost saver (configurable): start with the fastest model, launch the other
  two only if it fails the repro test.
- Per-candidate log in results/candidates.json: model actually used, substituted,
  patch_applied, gate_passed, repro_passed, regression_count, won_selection.
- Report which model wins most often and which never wins.
- Ablation configs on the same DEV slice: (a) 1 model x 1 candidate, (b) best model x
  3 samples at different temperatures, (c) 3 different models. Report whether (c)
  beats (b) enough to justify the extra quota.

## STAGE E: LOCALIZATION, CONTEXT, VERIFICATION, SELECTION
Verify these still work and did not regress; improve only where measured failures point:
- Localization: seeds from stack traces, paths, identifiers, error text; hierarchical
  file -> function -> lines using BM25 + embeddings + tree-sitter/call graph + LLM
  re-rank. Report file recall@1/@3/@5 and function-level recall. Inspect the ~40% of
  DEV instances where the gold file is never found and record why.
- Context: full enclosing function/class, direct callers, and the test exercising it,
  plus local style conventions. Minimal diffs only.
- Static gates: ast.parse/py_compile, pyflakes, reject empty or whitespace-only diffs.
- Reproduction test generated from the issue text only; it must FAIL before the patch
  (otherwise discard it) and PASS after.
- Regression check on the touched modules' existing tests.
- Closed loop: feed the trimmed real pytest traceback back (max 2 rounds, stop early if
  the same failure repeats).
- Selection order: (1) repro passes, (2) zero regressions, (3) calibrated Laya score,
  (4) smallest diff. Laya ranks survivors; it never overrides hard signals.
- If none survive, do one repair round, then output "no confident fix".

## STAGE F: LAYA WITH REAL EVIDENCE
- Log every candidate + real outcome to data/laya_labels.jsonl, excluding DEV and FINAL
  instances. Refit temperature scaling and the combiner once there are at least 300
  labelled examples, with a validation split of at least 100.
- Report ECE and Brier with the validation size beside them. Do not present the
  earlier 15-example numbers as evidence of calibration.
- Report which signals dominate the combiner weights.
- Choose the auto-approve threshold on validation data for a target precision;
  everything below it goes to human review.
- If Laya is unavailable, fall back to hard signals only and say so in the output.

## STAGE G: SENIOR-DEV OUTPUT AND USABILITY
Output should look like a draft PR from a careful engineer:
- Sections: Understanding of the bug, Root cause, Files/functions changed and why,
  Diff, Tests run (repro + regression results), Confidence with reasons, Risks/
  what to double check, Which model produced this patch.
- Show "LOW CONFIDENCE, review carefully" when below threshold, and "no confident fix"
  with the reasoning and best partial findings instead of forcing a patch.
- Pre-filter: flag architecture/migration/breaking-change/unclear tickets as unsuitable
  for autonomous fixing and recommend human review.
- Streamlit UI: paste a GitHub repo URL (optionally an issue URL that auto-fetches the
  text, plus branch/commit), live step tracker with model and elapsed time, side-by-side
  diff, candidate comparison table, Approve/Reject, Download .diff.
- CLI: `isha fix <repo_url> --issue-url <url>`, `isha bench --limit N`, `isha doctor`.
- Run history in runs/<timestamp>/ (plan, patch.diff, logs.jsonl, report).
- Friendly error messages; no raw tracebacks in the UI.
- Compatibility: works on Windows via WSL2 and on Linux/macOS; pinned dependencies;
  never modifies the user's branch (worktrees only).

## STAGE H: ABLATIONS, FINAL RUN, REPORT
- Ablate on DEV, one at a time: localization upgrade, symbol scope clipping, static
  gates, closed loop, tournament size, repro-test selection, Laya reranking. If a
  component has no measurable effect, say so. Use a 10-15 instance subset if quota is
  short and label the results as directional.
- Run the FINAL slice once with the final configuration.
- Write results/REPORT.md: stage table, before/after table, per-candidate table,
  ablations, Laya metrics with validation size, remaining failure causes, and a
  Limitations section (free-tier models, possible benchmark contamination in model
  training data, small sample and wide confidence intervals, Python-only, scoped to
  small/medium well-defined bugs). Do not claim an improvement unless the intervals
  and the changed-instance list support it.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-30T18:14:45+05:30.

The user's current state is as follows:
Active Document: c:\Users\Eashwar\ISHA\isha-agent\src\agents\candidates.py (LANGUAGE_PYTHON)
Cursor is on line: 1
Other open documents:
- c:\Users\Eashwar\ISHA\isha-agent\src\agents\candidates.py (LANGUAGE_PYTHON)
- c:\Users\Eashwar\ISHA\isha-agent\src\tools\symbol_target.py (LANGUAGE_PYTHON)
</ADDITIONAL_METADATA>