# ISHA — Mistakes & Error Catalogue

**Priority rule (standing):** each entry gets deleted/adjusted the moment its
close condition is verified — this file only ever holds live, unresolved
problems plus the final study catalogue (M-3).

**Location note (Day 3, 21:40+):** the root `C:\Users\Eashwar\ISHA\mistakes.md`
and root `plan.md` were found missing from disk on Day 3 (~17:25 local).
This file is the relocated catalogue under `results/`, built from the
meta.json / log evidence on disk. `results/progress.md` remains the single
source of truth for run state.

---

## GATE VERDICT — smoke50 campaign, written 2026-10-05 ~16:40 IST

**Merged view (r2 > r1 > main), 50 unique instances, all done:**
ok **39 (78%)** · timeout **5 (10%)** · syntax_error **3 (6%)** ·
patch_apply_failed **3 (6%)** · offline < 5% (offline_calls = 0 in every
meta.json checked).

| Bar | Value | Result |
|---|---|---|
| patch yield ≥ 40% | 78% | ✅ PASS |
| timeout < 15% | 10% (≤7 allowed) | ✅ PASS |
| patch_apply_failed < 5% | 6% (3/50; needs ≤2) | ❌ **FAIL** |
| offline < 5% | <5% | ✅ PASS |

**VERDICT: FAIL** — the apply-failure bar is the only failing gate.
Per the sanctioned FAIL path: **lite300 NOT started**.
Leading unresolved bucket: **timeout (5 of 11)** — see M-3.
Early-signal vs 8% line: far above (78% static-gate patch yield); the
number is not the blocker, the apply/timeout buckets are.

**Next sanctioned steps (Day 4, no mid-campaign profile changes):**
1. `smoke50-r3` on the 11 M-3 ids under a healthy-quota window (same profile,
   new run-id) — targets both the timeout bucket (re-run the 3 large django/
   matplotlib instances solo, no dual-worker contention) and the 3
   apply-failures + 2 coder-miss syntaxes.
2. Or fix the coder-level root cause (M-2) first, then r3 once.
3. Re-verdict on the merged view; PASS → lite300.

---

## M-1 — Overnight run killed by user power-off
Status: **CLOSED 2026-10-05** (verdict day)
- Symptom: Day-1 overnight bench died; initially suspected crash.
- Cause: user power-off 20:58 / 23:55 (Windows event 1074) — not a code bug
  (verified in event log, Day-2 morning).
- Fix: resume-from-checkpoint is lossless; no-sleep config + persistent
  process lifetime for subsequent runs.
- Close condition: smoke50 hits 50/50 with no unexplained stop.
- Closure: met — main ran 38→50 on Day 3 with no unexplained stop; 50/50
  reached 2026-10-04 ~21:40 IST.

## M-2 — Quota-death → fallback coder hallucinates file context → apply/syntax failures
Status: **OPEN** (converted to v2 coder-level fix)
- Symptom: when the Groq primary (qwen3.8-27b) is 429-dead, the coder role
  gets answered by fallback models (gpt-oss-120b/20b, gemini-flash-lite),
  which then emit patches against *imagined* file content → hunk context
  mismatch (apply-fail) or invalid Python (syntax-fail).
- Evidence (Day 2-3): r1 cleared 2/4 on healthy quota; r2 cleared
  django-11133 + seaborn-2848; but pylint-5859 r2 had **all 4 coder calls on
  gpt-oss-120b fallback** and apply-failed again (2nd time); sympy-12481/
  13031 apply-failed with coder calls entirely on gpt-oss/gemini-lite
  fallbacks; sympy-11870 syntax on 1 fallback call.
- Root cause confirmed, but the fallback-coder weakness is coder-level:
  even one fallback answer contaminates the patch.
- Fix (v2, targeted): (a) pre-apply hunk validation against the real checkout
  before accepting a patch (cheap static check, catches context drift early);
  (b) on fallback-coder answer, re-ground: force the patch to be regenerated
  with the exact file lines in context (re-fetch on the retry path);
  (c) optionally gate fallback coder answers behind a stricter LAYA
  safe_to_apply floor.
- Close condition: r3 (or fixed pipeline) clears the 3 apply-failures without
  fallback-coder contamination; then delete this entry.

## M-4 — Unexplained main-run stop ~18:02 Day 2
Status: **CLOSED 2026-10-05** (verdict day)
- Symptom: main smoke50 stopped at 26/50 with no crash marker; zero loss.
- Cause: unpinned at the time; leading hypothesis = session-boundary event
  (same class as M-1).
- Close condition: no further unexplained stop before 50/50.
- Closure: met — the Day-3 resume (38→50) ran to completion with no
  unexplained stop; both runs ended normally (r2 exit 0 in 2366 s; main
  completed its last instance). If a stop ever recurs, escalate to
  scheduled-task/VM hosting.

---

## M-3 — Smoke50 unresolved instances (study list, final merged view)

Built at main==50/50 AND r2==8/8 from meta.json evidence (gate/apply-reject
messages quoted verbatim; model_log positions = which models answered).
All 11 below have `status: done` with a failure_category or no usable patch.
Status: **open** — feed for `smoke50-r3` / Day-4 improvement loop.

### Bucket: timeout (5) — LEADING BUCKET
Common pattern: the 3 r2 instances ran **in parallel with the main run**
(dual-worker shared-quota contention) and all three are the largest repos in
the slice (django ×2, matplotlib); both sphinx timeouts show
`model_log: []` — the instance never completed even its first planner call
inside the 1800 s budget (process-level stall under backoff, not a code
path).

1. **django__django-11422** (merged = smoke50-r2) — timeout, 1 attempt,
   1800 s cap. Prior: main apply-failed with 4 gpt-oss-120b answers mid-
   instance; r1 apply-failed. Hypothesis: repo size + 429 backoff eats the
   whole 30-min budget; solver never reaches coder rounds. Fix: r3 solo on
   healthy quota; if it still times out, raise the per-instance timeout for
   >50k-LOC repos only.
2. **django__django-11620** (r2) — timeout, 1 attempt, cap. Prior: main
   apply-failed (6 gpt-oss-120b answers). Same hypothesis/fix as 11422.
3. **matplotlib__matplotlib-22835** (r2) — timeout, 3rd cross-run timeout
   (main + r2 + earlier re-solve all timed out under storm windows).
   Hypothesis: same contention/budget issue. Fix: same as 11422.
4. **sphinx-doc__sphinx-10451** (main) — timeout, 1 attempt, cap;
   `model_log: []`, last event `error: instance exceeded 1800s`. Hypothesis:
   stalled at the very first LLM round (checkout+backoff loop) — the
   1800 s clock starts at instance start, so a long checkout/backoff window
   can burn the entire budget before any model call. Fix: check whether the
   per-instance timer should exclude checkout/prep time; re-run in r3 solo.
5. **sphinx-doc__sphinx-11445** (main) — timeout, identical signature to
   10451 (`model_log: []`, exceeded 1800s). Fix: same as 10451.

### Bucket: syntax_error (3)
6. **django__django-11742** (r2) — syntax_error, 2nd consecutive occurrence
   (main + r2). Models: qwen primary + gemini-lite + gpt-oss-20b mix.
   Hypothesis: genuine coder miss — the same code produced invalid Python
   twice across different model mixes; likely a genuinely hard issue.
   Fix: r3 with the M-2 (b) re-grounding fix active; if it fails again,
   accept as out-of-reach for the free tier and label it in the study list.
7. **sympy__sympy-11870** (main) — syntax_error, 1 attempt, 782 s,
   retry_count 3. Gate message: `static gate failed: .../trigsimp.py:
   redefinition of unused 'symbols' from line 5`. Models: qwen primary
   (planner + coder) + 1 gpt-oss-120b fallback coder call; LAYA PASSed the
   diff (checklist said the import was "standard practice") — the pyflakes
   gate caught what LAYA missed. Hypothesis: patch duplicated an existing
   import; LAYA's checklist has no "unused/redundant import" check.
   Fix: (a) this is a clean one-shot retry candidate for r3; (b) add a
   pyflakes pre-check to the LAYA checklist so redundant-import patches get
   blocked with a reason.
8. **matplotlib__matplotlib-23299** (r2) — syntax_error, 1 attempt, 872 s.
   Gate message: `no-op patch: the diff only reformats the lines it touches
   (identical code on both sides ...)`. Models: planner qwen primary (+
   gpt-oss-120b fallback planner), coders gpt-oss-120b + qwen; critic
   flagged, LAYA checklist BLOCK ("no-op regarding behavior"). The gate
   correctly rejected it, but the instance is still red: after 3 re-solves
   the coder keeps landing on whitespace-only diffs for this one.
   Hypothesis: planner plan does not actually describe the code change
   needed, so the coder fills the diff with comment/whitespace edits.
   Fix: r3 with plan-quality check — if planner output shares no code tokens
   with the target file, force a plan retry before coding.

### Bucket: patch_apply_failed (3)
9. **pylint-dev__pylint-5859** (r2, 2nd time — main also apply-failed) —
   2 attempts, 775.8 s. Reject message: `Hunk failed in pylint/lint/
   pylinter.py: @@ — expected context not found in file: '        self._
   notes_regexp = re.compile(r"^(?:%s):" % "|".join(self.notes))' (git: No
   valid patches in input; sr: No SEARCH/REPLACE blocks found)`. Models:
   planner qwen primary ×4; **all 4 coder calls answered by gpt-oss-120b
   fallback 1** — textbook M-2 signature (quota-dead window, fallback coder
   hallucinated the file context). Fix: M-2 (a)+(b); r3 candidate only after
   the re-grounding fix is in.
10. **sympy__sympy-12481** (main) — patch_apply_failed, 2 attempts,
    1397.8 s. Reject message: `Hunk failed in sympy/combinatorics/
    permutations.py: @@ — expected context not found in file: '        if
    args:'`. Models: planner qwen primary + gemini-3.1-flash-lite (fb5);
    coders gemini-lite ×2, gpt-oss-20b (fb2), gpt-oss-120b (fb1) — zero
    qwen coder answers (primary 429-dead for the whole coding phase).
    Same M-2 root cause. Fix: M-2 (a)+(b); r3 candidate.
11. **sympy__sympy-13031** (main) — patch_apply_failed, 2 attempts,
    1516.97 s. Reject message: `Hunk failed in sympy/matrices/dense.py:
    @@ — expected context not found in file: '        args = [m for m in
    args if m.cols > 0]'`. Models: planner qwen primary + gemini-lite;
    coders gpt-oss-20b, gemini-lite ×2, gpt-oss-120b — again no qwen coder
    answer. Same M-2 root cause. Fix: M-2 (a)+(b); r3 candidate.

### Cross-cutting summary for Day 4
- 6 of 11 (all 3 apply-failures + 23299 + 11742, and the fallback-heavy
  r2 timeouts) trace to **fallback-coder contamination under 429 storms**
  (M-2).
- 5 of 11 are timeouts, 2 of which never made a single model call — a
  **timer-vs-checkout bug candidate** worth a one-line code audit.
- 3 of 11 (11870, 10451, 11445) are cheap r3 retry candidates as-is;
  5859/12481/13031 need the M-2 fix first; 11742/23299 may be genuinely
  out of reach for the free tier (mark after r3).
