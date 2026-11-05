# ISHA Subsystem Review (revised)

*Revised 2026-10-20. Replaces `isha_subsystems_sota_assessment.md`.*

## Status of this document

This is a **backlog of hypotheses**, not a grade against other systems.

- Measured results live in `results/*.json`. This file contains **no projected percentages and no "SOTA tier" ratings**, because none of those were measured.
- Code-level observations come from reading the code and have not all been confirmed. Items marked **[VERIFY]** need a check before anyone acts on them.
- "Tests" below means ISHA's own reproduction test plus the repo's existing tests. The official SWE-bench tests are not visible while solving.

## Measured baseline (fill in from saved files)

| Run | Resolved | 95% Wilson interval | Source |
|---|---|---|---|
| DEV-30 baseline | 1/30 (3.3%) | 0.6% to 16.7% | `results/stage_table.json` / `before_after.json` |
| smoke50 | 0/50 (0.0%) | 0.0% to 7.1% | `results/smoke50.json` (official harness) |
| Lite-300 | not run | | |

Also record for each run: the final status counts (must sum to the sample size), the share of coder calls answered by a fallback model, and quota used. Never merge runs into one headline number.

## Rules for any change

1. **One change at a time**, with a stated hypothesis and a before/after on a dev set.
2. **Tune only on dev data from the SWE-bench train split.** Smoke50 and Lite-300 are test sets: analyze them, but do not tune on them before the frozen run.
3. **One profile, one run.** Save the full config (models, prompts, env vars, workers, candidates, timeouts) with every run.
4. **Generic fixes only.** A change needs 3 or more failing instances sharing the same cause. No instance-specific code.
5. **No memory or learning from test outcomes** in any scored run (see Memory section).
6. Every number in the README is generated from a saved results file.

## Summary

| Subsystem | Observed strength | Main risk or gap | What would show it matters |
|---|---|---|---|
| 1. Orchestration (LangGraph) | Cyclic retry, confidence gate, lock-guarded merge | Possible full waits on all candidates; overhead unmeasured | Calls per instance, seconds per node |
| 2. Tournament and patch engine | Worktree isolation, diverse models and strategies, compile gate | Fuzzy apply may land on the wrong block | Fallback-apply rate, wrong-symbol edits |
| 3. Sandbox | Network off, resource limits, targeted tests | Repro test may not be a valid RED; time sinks unprofiled | `repro_valid` rate, per-stage time |
| 4. Critic, Laya, arbitration | Multi-factor score, fallback penalty | A critic opinion can discard a test-passing patch | Patches discarded despite passing tests |
| 5. Structural analysis | Qualified symbols, blast-radius escalation | Static AST misses dynamic dispatch | Function-level localization recall |
| 6. Memory store | Separates belief from ground truth | Not yet used; high leakage risk if injected carelessly | Held-out dev results only |
| 7. Guardrails | Secret scan, merger veto, approval log | False alarms on test fixtures | False-positive count |

---

## 1. Orchestration (`src/agents/graph.py`, `nodes.py`, `state.py`, `dispatch.py`)

Flow: investigation, decomposer, planner, confidence gate, regression test, fan-out to attempts in isolated worktrees, arbitration, merger, checkpoint.

**Strengths**
- `_route_after_sandbox` retries up to `MAX_RETRIES`, so a failure is not final.
- The confidence gate escalates low-confidence plans before costly patch generation.
- `merger_node` uses a lock-guarded, de-duplicated merge registry for parallel branches.

**Gaps**
- **State handling.** Mutations made inside a conditional-edge function are not persisted by LangGraph. Make sure routers are pure and state changes happen inside nodes. **[VERIFY]**
- **Framework overhead is unmeasured.** The earlier "1.2 to 3.5 s per transition" figure had no source and is likely too high. Log per-node time and compare it with LLM and test time before blaming the framework.
- **No early exit.** All attempts run to arbitration even when one is clearly sufficient. Free-tier quota makes this worth fixing.
  - Trigger: repro passes, zero regressions, static gate passes, and no escalation. Do **not** use a critic or Laya score as the trigger.
  - Parallel branches are hard to cancel, so prefer sequential fast-first ordering that launches the second and third candidates only if the first fails.
  - Measure calls per instance and resolved count. Resolved must not drop.

## 2. Tournament and patch engine (`candidates.py`, `patch_engine.py`, `worktree_manager.py`)

**Strengths**
- Each candidate runs in its own git worktree and cannot touch another's files or the main branch.
- Strategy variants use different prompts and temperatures, and candidates use different model families.
- `compile_gate` runs `ast.parse` and `py_compile` before any container starts.
- `AGENTS.md` lists the documented rules that guard against common LLM mistakes.

**Gaps**
- **Wrong-block risk.** When `git apply` rejects a diff, `_apply_manual` falls back to fuzzy matching. In files with repeated boilerplate it can edit the wrong method.
  - Require a unique anchor match and reject ambiguous matches.
  - After applying, check with the AST that only the intended symbols changed.
  - Log how often the fuzzy path is used.
- Count each candidate by the model that actually answered, and mark any fallback substitution, so a substituted run is not counted as diversity.

## 3. Execution sandbox (`docker_sandbox.py`, `sandbox.py`, `improvement_loop.py`)

**Strengths**
- `--network none`, memory and CPU limits, and `--rm`.
- Targeted tests (`pytest -k`) keep runs short.
- The real traceback is trimmed and fed back for repair.

**Gaps**
- **Reproduction test validity (high priority).** The test must **fail on the unpatched code for the reason the issue describes** (an assertion or expected-behavior failure, not an import or collection error) and **pass after the patch**. Discard repro tests that do not fail. Record `repro_valid` for every instance. Candidate selection depends on this test, so everything downstream is only as good as it is. The README says RED is verified; confirm the code does it every time. **[VERIFY]**
- **Cold-start overhead.** Each run starts a new container. The 3 to 8 s figure is reported but not measured. Profile first; timeouts at 900 s are probably dominated by LLM waits, image pulls, and test time. Move to a warm `docker exec` container only if cold start is a meaningful share of per-instance time.
- **Memory cap.** A 1 GB limit may be too low for some repos. Check whether any `harness_no_output` cases are out-of-memory. **[VERIFY]**

## 4. Critic, Laya, arbitration (`critic.py`, `laya_judge.py`, `calibration.py`, `arbitration.py`)

**Strengths**
- The composite considers fix quality, issue match, and safety.
- Fallback-model candidates receive a penalty.
- The safety checklist can veto risky changes.

**Gaps**
- **Test truth inversion.** If the composite falls below the threshold, `critic_node` can flag or reject a patch even when tests pass. Use a strict order instead of a weighted formula:
  1. Hard gates: repro passes, zero regressions, static gate passes, secret scan clean.
  2. Rank the survivors by fewest changed lines, then Laya composite.
  3. A critic "flagged" result routes the patch to human review, not to deletion.
  4. Only security-scanner findings are automatic vetoes.
- **Calibration scope.** The calibration data (about 100 validation examples from train-split and synthetic tasks) does not show calibration on real SWE-bench instances. Report auto-approve precision on a real held-out slice before claiming calibrated confidence.

## 5. Structural analysis (`dependency_graph.py`, `ast_mapper.py`, `symbol_target.py`)

**Strengths**
- Fully qualified symbols (`module.py::Class.method`) avoid ambiguous edits.
- Blast-radius escalation flags changes to widely used functions.
- Symbol skeletons save prompt tokens.

**Gaps**
- Static AST cannot see dynamic dispatch (`getattr`, metaclasses, ORM calls such as `objects.filter()`).
- Options: 2-hop caller traversal and heuristic token matching across imported namespaces.
- Evaluate by function-level localization recall on dev data (not file recall alone).

## 6. Memory store (`src/memory/store.py`, `fix_history.py`)

**Strengths**
- Write-A records the attempt, and Write-B records ground truth after official grading, so belief and truth stay separate.
- SQLite WAL lets parallel workers write safely.

**Rule: do not inject memory into scored runs.** The store records which patches resolved after official grading. If Lite outcomes feed later Lite prompts, the result is contaminated, and any gain from "similar past fixes" would be leakage. Also, `org_critic_threshold` must not be tuned from outcomes that are later reported.
- Disable memory for smoke50 and Lite-300.
- Fill it only from train-split dev tasks and non-benchmark use.
- Never store gold patches.
- Evaluate retrieval only on a held-out dev set, and only after the frozen benchmark.

## 7. Guardrails (`scanner.py`, `gate.py`, `checklist.py`)

**Strengths**
- Secret detection (keys, tokens, private keys, connection strings) runs before apply.
- The merger refuses any patch the scanner flags.
- High-risk changes go to the approval log.

**Refinement**
- Lower severity for obvious placeholders in `tests/` and `fixtures/`, but keep scanning those paths for real key patterns. Do not exclude them completely.

---

## Roadmap (ordered by evidence, not effort)

Effort is not estimated here, because earlier estimates were unreliable.

| Priority | Item | Measure by |
|---|---|---|
| **P0** | 1. Failure analysis of smoke50 (a post-mortem per unresolved instance, fixed category list) | Counts per category; hand-check 10 against logs |
| **P0** | 2. Execution-first selection order (critic flags go to review) | Test-passing patches discarded (target 0) |
| **P0** | 3. Repro-test RED validity check and `repro_valid` logging | `repro_valid` rate; resolved on dev |
| **P0** | 4. Ambiguity guard in fuzzy apply | Wrong-symbol edits; fallback-apply rate |
| **P1** | 5. Lazy candidate launch / early exit | Calls per instance; resolved unchanged or higher |
| **P1** | 6. Per-stage timing, then warm container only if justified | Seconds per stage; timeout count |
| **P1** | 7. Localization upgrades (LLM-guided, 2-hop graph, embedder weighting) | File and function recall on train-split dev |
| **P2** | 8. Memory retrieval, after the frozen benchmark, with leakage controls | Held-out dev only |
| **P2** | 9. Scanner placeholder handling | False-positive count |
| **P2** | 10. Heuristics for dynamic Python | Function-level recall |

## Items to verify in the code

1. Is the repro test always checked to fail before the patch, and for the right reason?
2. Does any path let the critic discard a patch that passed its tests?
3. How often does the fuzzy apply path run, and does it ever edit a different symbol than intended?
4. What share of coder calls used a fallback model, and how did those instances do compared with primary-model instances?
5. How much of each instance's time goes to LLM waits, image pulls, environment setup, and tests?

## Changes from the earlier version

- Removed the "SWE-bench tier" and "potential with fixes" columns and all projected percentages.
- Removed claims that ISHA is "ahead of 80% of agents" or "enterprise SOTA."
- Removed descriptions of how other systems (Aider, Agentless, Moatless, Voyager, ExpeL) work. Re-add only with citations.
- Removed the unsourced LangGraph latency figure and the "90% of syntax errors" claim.
- Replaced the weighted 0.70/0.30 score with a strict gate-then-rank order.
- Moved repro-test validity from P2 to P0.
- Added the memory-contamination rule and dev/test discipline.
- Replaced `file:///C:/Users/...` links with plain file names.
