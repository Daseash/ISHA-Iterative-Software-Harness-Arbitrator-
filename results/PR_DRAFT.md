# PR Draft — ISHA closed-loop fixes (ready to open; needs owner `gh` auth)

Repo: `Daseash/ISHA-Iterative-Software-Harness-Arbitrator-`
Base: `main` | Branch: `main` (single-branch repo — review before head)

## Title
`fix(pipeline): patch-gate false negatives + hunk-anchored repair feedback; bandit + per-org thresholds; 213-row submit bundle`

## Body

### Summary
- **Patch gate false-negative fixed** (`validate_patch`): was checking with `git apply --check --whitespace=nowarn` only — CRLF/whitespace drift on Windows hosts made KNOWN-GOOD patches fail validation (live-proofed: S8's officially resolved sphinx-8713 patch previously validated False / applied True). Now per its own docstring contract: `--ignore-whitespace`.
- **Coder hallucination fix** (`_hunk_excerpts`): repair-loop feedback now includes REAL file content at failed-hunk locations (parses `+++`/`@@` headers), for both apply-fail and static-gate-fail paths — stops context-line inventions that killed 100% of candidates in r4 (24/24 died at "Hunk failed … expected context").
- **AR-5 minimal bandit** (`store.strategy_order`): Laplace-smoothed (wins+1)/(graded+2) strategy ranking per org from graded outcomes (ignores NULL-graded rows); ε-reorder only. Wired into fan-out dispatch.
- **Per-org LAYA thresholds LIVE** (`calibration.per_org_threshold`): consumes `results/calibration_real.json → per_org_90_precision` (django 0.93, matplotlib 0.04) at the approval gate; opt-in `ISHA_PER_ORG_GATE=1` (default OFF — bench lanes unchanged mid-run). Approval-log path now resolves per-call.
- **Submit bundle refreshed**: `results/all_preds.jsonl` 207 → **213 rows** (dedup graded > resolved > longest preserved; all 213 rows carry model_patch).

### Tests
- `tests/test_p0_07.py` (5/5, incl. `test_hunk_excerpts_shows_real_file_lines`)
- `tests/test_ar_05.py` (4/4)
- `tests/test_per_org_gate.py` (4/4)
- Full offline suite: **168 passed, 0 failed** (`ISHA_FORCE_OFFLINE=1`)

### Score (Docker `report.json` ground truth only)
- Official audited: **76/300 (25.3%)** — S1-S4 66/120, S5-S7 +24, S8 4/30 (sphinx-8713/8721, sympy-13471/13647)
- Improving in flight (NOT yet counted): s8 rescue + S9/S10 lanes

### Submit
1. `gh auth login` (owner interactive)
2. `gh pr create --base main --head main --title "$(cat isha-agent/results/PR_DRAFT.md | sed -n '3p' | tr -d '`')" --body "$(isha/results/PR_DRAFT.md)"`
   - SWE-bench leaderboard bundle: `isha-agent/results/all_preds.jsonl` (213 unique instances) via princeton-nlp/SWE-bench per A-1 (gate ≥75 crossed)

### Checklist
- [x] No `.env`, no `plan.md`, no secrets in commit
- [x] LF/UTF-8 only, offline tests green
- [x] No score movement claimed without `report.json`
- [x] Website changes excluded (A-3 deferred)
