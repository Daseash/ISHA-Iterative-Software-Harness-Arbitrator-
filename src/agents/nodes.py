"""
ISHA Agent Nodes — Individual steps in the agentic loop.

Each function takes AgentState in and returns an updated AgentState.
All LLM calls are wrapped so API failures degrade into readable state
messages instead of crashing the graph.
"""

import os
import re
import sys
from pathlib import Path

from src.agents.state import AgentState, coerce_state
from src.config import call_coder, call_planner, call_repro, get_model_log
from src.tools.context_trimmer import trim_traceback
from src.tools.patch_engine import apply_patch
from src.tools.sandbox import make_sandbox, run_tests, cleanup_sandbox

from src.agents.prompts import (
    _FENCE_RE,
    _TOOL_MARKUP_RE,
    _strip_fences,
    _unfence,
    _extract_diff,
    _strip_tool_markup,
    _clip,
    _clip_issue,
    _prompt_stats,
    _bench_mode,
    localization_section,
    code_context_section,
    build_coder_prompt,
    _ISSUE_CHARS,
    _PLAN_CHARS,
    _REGRESSION_CONTEXT_CHARS,
    _PLANNER_CONTEXT_CHARS,
    _CODER_CONTEXT_CHARS,
    _PLANNER_AUX_CHARS,
    _TARGETING_FILES,
    _TARGETING_SYMBOLS,
)


def planner_node(state: AgentState) -> AgentState:
    """Generate a structured fix plan from the issue and repo context."""
    state = coerce_state(state)

    # Phase 2 — seeds parsed out of the issue text drive file -> symbol ->
    # line localization; the ranked list is stored so the Coder builds its
    # full-body context from exactly the same places the plan referenced.
    loc_section, candidates = localization_section(state)
    if candidates:
        state.localization = [c.as_dict() for c in candidates]

    # Learn from this repo's own fix history (retrieved from the fix ledger).
    history_section = ""
    try:
        from src.agents.fix_history import render_hits, retrieve_fixes

        hits = retrieve_fixes(state.issue_text, state.repo_path)
        if hits:
            history_section = (
                "\nSIMILAR PAST FIXES IN THIS REPO (reuse what worked, "
                "don't repeat what failed):\n" + render_hits(hits) + "\n"
            )
    except Exception:
        pass

    # Blast-radius caution (caller fan-out computed during investigation).
    br = state.blast_radius or {}
    blast_line = ""
    if br.get("callers") or br.get("score"):
        blast_line = (
            f"\nBLAST RADIUS: ~{br.get('callers', 0)} callers across "
            f"{br.get('files', 0)} files (score {br.get('score', 0):.2f}). "
            "If fan-out is high, prefer the smallest change that fixes the "
            "bug; do not change public signatures unless unavoidable.\n"
        )

    # Test file summaries — so the plan accounts for existing test expectations.
    test_section = ""
    try:
        from src.tools.dependency_graph import DependencyGraph

        dep_graph = DependencyGraph(state.repo_path)
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", state.issue_text))
        entry_pts = [s.name for s in dep_graph.definitions if s.name in tokens][:10]
        if not entry_pts:
            entry_pts = [t for t in tokens if len(t) > 3][:5]
        impact = dep_graph.analyze_impact(entry_pts)
        test_contents = []
        for tf in impact.impacted_test_files[:2]:
            tpath = Path(state.repo_path) / tf
            if tpath.is_file():
                try:
                    content = tpath.read_text(encoding="utf-8", errors="replace")
                    test_contents.append(f"# {tf}\n{content[:1200]}")
                except Exception:
                    pass
        if test_contents:
            test_section = (
                "\nEXISTING TEST FILES (account for these test expectations):\n"
                + "\n\n".join(test_contents) + "\n"
            )
    except Exception:
        pass

    feedback_section = ""
    if state.context_notes:
        notes_str = "\n".join(str(n) for n in state.context_notes[-4:])
        feedback_section = f"\nCRITICAL DOCKER TEST EXECUTION FAILURE FEEDBACK:\n{notes_str}\n"

    prompt = f"""You are an expert software engineer. Given this bug report and
repository context, produce a structured 2-step fix plan:
Step 1: What is the root cause
Step 2: What exact changes to make (file, function, what to change)

You have NO tools: do not emit <function_calls> or <invoke> markup, do not
ask to read files. Everything you need is already in this prompt - answer
directly in prose.

IMPORTANT: If the bug spans multiple files (e.g. a function signature
mismatch between a definition and its callers), list ALL files that must
be changed.  The patch must be atomic — fixing only one file and leaving
its callers broken is not acceptable.

BUG REPORT:
{_clip_issue(state.issue_text, _ISSUE_CHARS)}
{feedback_section}
REPOSITORY CONTEXT:
{_clip(state.repo_context, _PLANNER_CONTEXT_CHARS)}
{_clip(loc_section + history_section + test_section, _PLANNER_AUX_CHARS)}{blast_line}
REPO PATH: {state.repo_path}
Output the plan only, then finish with exactly one final line in this format:
CONFIDENCE: <0.00-1.00>
Score how completely you understand the root cause from the information
given. Use the full range: report below 0.40 only when the report lacks
reproduction details or the relevant code is not visible in the context."""
    _prompt_stats("planner", prompt=prompt)
    try:
        plan_raw = call_planner(prompt, temperature=0.20)
        # P1-01: prose plan needs _unfence (keep all), not _strip_fences (largest block).
        plan = _strip_tool_markup(_unfence(plan_raw)) or "[PLANNER ERROR] empty response"
        # P1-01: case-insensitive CONFIDENCE (models emit Confidence:/confidence:).
        conf = re.search(r"CONFIDENCE:\s*([0-9]*\.?[0-9]+)", plan, re.I)
        if conf:
            try:
                state.planner_confidence = max(0.0, min(1.0, float(conf.group(1))))
            except ValueError:
                state.planner_confidence = -1.0
            plan = re.sub(r"^\s*CONFIDENCE:.*$", "", plan, flags=re.M | re.I).strip()
        else:
            state.planner_confidence = -1.0
        state.plan = plan
    except Exception as exc:
        state.plan = f"[PLANNER ERROR] {exc}"
        state.planner_confidence = -1.0
    state.model_log = get_model_log()
    return state


def confidence_gate_node(state: AgentState) -> AgentState:
    """Escalate to a human when the planner doesn't understand the bug well enough.

    A senior dev says "this ticket needs more info" instead of guessing;
    this node is that instinct. Sets `escalation`, which routes the run to
    the approval/checkpoint path before any patch is attempted.
    """
    state = coerce_state(state)
    try:
        threshold = float(os.getenv("ISHA_CONFIDENCE_THRESHOLD", "0.4"))
    except ValueError:
        threshold = 0.4
    confidence = state.planner_confidence
    if 0.0 <= confidence < threshold:
        state.escalation = (
            f"low planner confidence {confidence:.2f} < {threshold:.2f}: "
            "the bug is not understood well enough to patch safely"
        )
    return state


def regression_test_node(state: AgentState) -> AgentState:
    """Write failing tests that reproduce the bug, plus edge cases (red -> green)."""
    state = coerce_state(state)
    prompt = f"""Given this bug report and fix plan, write a pytest test module that
REPRODUCES the bug. The first test must FAIL right now (red) and PASS after
the fix is applied (green).

Beyond the minimal reproduction, add 2-3 edge-case tests a senior engineer
would write: boundary values, empty/zero/None input, invalid input raising
the documented error, or the numeric edge of the reported bug (negatives,
overflow, duplicates, case sensitivity). Only include edge cases the fix
plan guarantees will pass after the fix — no speculative behavior changes.

Output ONLY the test code (multiple test functions allowed).

BUG REPORT:
{_clip_issue(state.issue_text, _ISSUE_CHARS)}

FIX PLAN:
{_clip(state.plan, _PLAN_CHARS)}

REPOSITORY CONTEXT:
{_clip(state.repo_context, _REGRESSION_CONTEXT_CHARS)}

REPO PATH: {state.repo_path}"""
    _prompt_stats("regression", prompt=prompt)
    try:
        test_code = call_repro(prompt, temperature=0.20)
        state.regression_test = _strip_tool_markup(_strip_fences(test_code))
    except Exception as exc:
        state.regression_test = f"# [REGRESSION TEST ERROR] {exc}"

    state.model_log = get_model_log()
    return baseline_red_gate_node(state)


def baseline_red_gate_node(state: AgentState) -> AgentState:
    """Require the generated repro test to fail (RED) before patching."""
    state = coerce_state(state)
    if not state.regression_test or not state.repo_path:
        state.repro_ok = None
        state.baseline_repro_failed = None
        return state

    clean_test_code = _strip_fences(state.regression_test)
    if clean_test_code.startswith("#"):
        state.repro_ok = None
        state.baseline_repro_failed = None
        return state

    sandbox = make_sandbox(state.repo_path)
    try:
        test_path = Path(sandbox) / "tests" / "test_isha_generated_repro.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(clean_test_code, encoding="utf-8")

        output = run_tests(
            sandbox,
            test_file="tests/test_isha_generated_repro.py",
        )
        state.repro_output = output or ""
        state.baseline_repro_output = state.repro_output

        # A real test failure is RED; collection/setup errors are not.
        has_test_failure = re.search(r"\b[1-9]\d* failed\b", state.repro_output) is not None
        has_collection_error = (
            "error collecting" in state.repro_output.lower()
            or re.search(r"\b[1-9]\d* errors?\b", state.repro_output) is not None
        )

        state.repro_ok = has_test_failure and not has_collection_error
        state.baseline_repro_failed = state.repro_ok
        state.repro_valid = state.repro_ok

        if not state.repro_ok:
            warning_msg = (
                "Baseline repro gate notice: Generated repro did not produce a clean failing assertion. "
                "Output might be passing, or failed with collection/import errors."
            )
            state.context_notes = list(state.context_notes) + [warning_msg]
            # Strict baseline check: when enabled, discard repro tests that do not fail cleanly (RED)
            if os.getenv("ISHA_STRICT_BASELINE", "0").strip().lower() in {"1", "true", "yes"}:
                # Discard repro tests that do not fail (per specification)
                state.regression_test = ""
                state.escalation = (
                    "Generated repro did not produce a clean failing test (RED). "
                    "Cannot verify bug reproduction on unpatched baseline."
                )
                state.context_notes.append(f"Baseline repro output:\n{state.repro_output[-3000:]}")
        return state
    except Exception as exc:
        state.repro_output = f"[baseline gate error] {exc}"
        state.baseline_repro_output = state.repro_output
        state.repro_ok = False
        state.baseline_repro_failed = False
        state.repro_valid = False
        if os.getenv("ISHA_STRICT_BASELINE", "0").strip().lower() in {"1", "true", "yes"}:
            state.regression_test = ""
        return state
    finally:
        cleanup_sandbox(sandbox)


def classify_failure(test_output: str, gate_errors: list[str] | None = None) -> str:
    """Classify failure mode into actionable diagnostic categories."""
    out = (test_output or "") + "\n" + "\n".join(gate_errors or [])
    out_lower = out.lower()

    if any(h in out_lower for h in ("syntaxerror", "indentationerror", "pyflakes", "ast.parse", "compile_gate")):
        return "SYNTAX_INDENTATION"
    if any(h in out_lower for h in ("signature", "takes ", "positional argument", "missing required argument")):
        return "SIGNATURE_MISMATCH"
    if any(h in out_lower for h in ("nonetype", "none is not", "none != ''", "object has no attribute '", "cannot be none")):
        return "TYPE_ERROR_NONE"
    if any(h in out_lower for h in ("unhashable type", "__hash__")):
        return "HASHABILITY_CONTRACT"
    if any(h in out_lower for h in ("assertionerror", "assert ", "failed requirement")):
        return "ASSERTION_MISMATCH"
    if any(h in out_lower for h in ("modulenotfounderror", "importerror", "no module named")):
        return "IMPORT_ERROR"
    if any(h in out_lower for h in ("timeout", "timed out")):
        return "TIMEOUT_REGRESSION"
    return "BEHAVIORAL_FAIL"


def replan_node(state: AgentState) -> AgentState:
    """Retry with new evidence: classify failure and update fix plan before calling coder."""
    state = coerce_state(state)
    failure_cat = classify_failure(state.test_output)
    state.failure_classification = failure_cat
    state.retry_count += 1

    directive_map = {
        "SYNTAX_INDENTATION": "FIX SYNTAX: Match exact 4-space indentation; ensure all code blocks and parenthesised expressions are closed.",
        "SIGNATURE_MISMATCH": "ALIGN SIGNATURE: Parameter or argument count mismatch between definition and caller sites. Support *args, **kwargs or update all call sites.",
        "TYPE_ERROR_NONE": "GUARD CLAUSE: Attribute or length called on None. Insert `if val is None:` guard before accessing attributes or slicing.",
        "HASHABILITY_CONTRACT": "HASH CONTRACT: Mutable collection placed in set/dict. Implement __hash__ or convert to immutable tuple.",
        "ASSERTION_MISMATCH": "ASSERTION REPAIR: The return value did not match test expectation. Check exact return types, empty string vs None, and boundary cases.",
        "IMPORT_ERROR": "CHECK IMPORTS: Ensure imported module exists in repo site-packages or top-level project root.",
        "TIMEOUT_REGRESSION": "MINIMAL SCOPE: Previous diff introduced infinite loop or heavy computation. Reduce diff to surgical one-block fix.",
        "BEHAVIORAL_FAIL": "ROOT CAUSE RE-EVALUATION: The previous fix did not satisfy the requirement. Address the root cause directly.",
    }
    directive = directive_map.get(failure_cat, directive_map["BEHAVIORAL_FAIL"])

    evidence = f"""

[EVIDENCE-BASED RE-PLANNING — ATTEMPT {state.retry_count}]
- Classified Failure Mode: {failure_cat}
- Actionable Diagnostic Directive: {directive}
- Test Traceback & Failure Excerpt:
{trim_traceback(state.test_output)}
"""
    state.plan = (state.plan or "") + evidence
    state.context_notes = list(state.context_notes) + [f"replan: classified {failure_cat}; updated plan with evidence"]
    return state


def coder_node(state: AgentState) -> AgentState:
    """Generate a unified-diff patch to fix the bug."""
    state = coerce_state(state)
    # Retry budget is owned SOLELY by replan_node (+1 per failed cycle):
    # coder only observes retry_count for prompts, never increments it.
    # (Incrementing here double-counted — budget burned ~2x per cycle.)

    from src.agents.candidates import strategy_models

    assigned = getattr(state, "assigned_model", "") or strategy_models().get(state.strategy, None)
    prompt = build_coder_prompt(state)
    try:
        raw = call_coder(prompt, temperature=0.20, model=assigned)
        patch = _extract_diff(raw)
        state.patch = patch or f"[CODER ERROR] no diff produced: {raw[:300]}"
        if assigned:
            state.assigned_model = assigned
            state.model_name = assigned
    except Exception as exc:
        state.patch = f"[CODER ERROR] {exc}"
    state.model_log = get_model_log()
    return state


def candidate_node(state: AgentState) -> AgentState:
    """Phase 4/5/6 — N candidates, verified, then one selected.

    Bench-mode only.  With ``ISHA_CANDIDATES > 1`` it generates N diverse
    candidates.  With N = 1 the node is a no-op — UNLESS
    ``ISHA_SINGLE_VERIFY=1``, which runs the closed loop on the single seed
    patch: the generated repro test runs inside the official image and, when
    the patch demonstrably fails it (after the up-to-2 in-loop repair
    rounds), the patch is dropped instead of submitted.  A patch that
    cannot pass its own FAIL_TO_PASS test cannot resolve the instance, so
    dropping it costs nothing and keeps the record honest.
    """
    state = coerce_state(state)
    if not state.patch or state.patch.startswith("["):
        return state
    try:
        from src.config import DEFAULT_CANDIDATES
        n = int(os.getenv("ISHA_CANDIDATES", str(DEFAULT_CANDIDATES)))
    except Exception:
        n = 3
    if n <= 1 and os.getenv("ISHA_SINGLE_VERIFY", "0") != "1":
        return state

    from src.agents.candidates import (
        cleanup_candidates,
        generate_candidates,
        rank_candidates,
    )

    instance_id = state.instance_id or Path(state.repo_path).name

    def _log(payload: dict) -> None:
        """Surface repair attempts as coder-visible notes for a later retry."""
        detail = payload.get("error") or "; ".join(payload.get("errors") or [])
        note = f"candidate {payload.get('candidate')}: {payload.get('event')} {detail}"
        state.context_notes = list(state.context_notes) + [note.strip()[:300]]

    candidates = generate_candidates(
        state,
        n=n,
        instance_id=instance_id,
        seed_patch=state.patch,
        log=_log,
    )
    if not candidates:
        return state

    # ── LAYA scoring (local, cheap) ─────────────────────────────────────
    judge = None
    try:
        from src.review.laya_judge import get_judge

        judge = get_judge()
    except Exception:
        judge = None

    for cand in candidates:
        if not cand.patch:
            continue
        if judge is None:
            continue
        try:
            scores = judge.score_patch(state.issue_text, state.plan, cand.patch)
            dangers = judge.check_dangers(cand.patch)
            cand.laya = {**scores, **dangers}
            cand.laya_combined = float(scores.get("composite", 0.0))
        except Exception as exc:
            cand.laya = {"error": str(exc)[:200]}

    # ── Repro verification in the official image (Phase 5) ──────────────
    verify_on = os.getenv("ISHA_VERIFY", "1") != "0"
    if verify_on:
        try:
            _verify_candidates(state, candidates)
        except Exception as exc:
            for cand in candidates:
                cand.repro = {"available": False, "reason": f"verifier error: {exc}"}

    # ── Score, rank, select ─────────────────────────────────────────────
    from src.review import calibration

    model = calibration.load()
    for cand in candidates:
        feats = calibration.features_for(
            cand.laya, cand.gate_ok, cand.repro, cand.diff_size, len(cand.changed)
        )
        outcome = calibration.combine(feats, model)
        cand.combined_score = float(outcome["score"])
        cand.rank_reason = outcome["mode"]

    ordered = rank_candidates(candidates)
    from src.agents.candidates import is_survivor
    survivors = [c for c in ordered if is_survivor(c)]

    if not survivors and ordered:
        best = ordered[0]
        # Run one repair round on the best candidate
        print(f"[arbitrator] no candidate survived; running 1 repair round on candidate #{best.index}...", file=sys.stderr)
        try:
            from src.agents.candidates import _apply, _reset
            from src.bench.gates import changed_files, compile_gate, diff_stats

            err_hint = ""
            if best.repro.get("after_output"):
                err_hint = "TRIMMED TEST TRACEBACK:\n" + trim_traceback(best.repro["after_output"])
            elif best.gate_errors:
                from src.bench.gates import format_gate_errors_with_context
                gate_ctx = format_gate_errors_with_context(best.worktree, best.gate_errors) if best.worktree else ""
                err_hint = "STATIC GATE ERRORS:\n" + (gate_ctx or "\n".join(best.gate_errors))
            elif best.apply_message:
                err_hint = "APPLY ERROR:\n" + best.apply_message
            else:
                err_hint = "Previous patch failed verification."

            repair_prompt = f"\n\nNO CANDIDATE SURVIVED. Final repair attempt on best candidate:\n{err_hint}\nProduce a corrected minimal diff."
            raw = call_coder(
                build_coder_prompt(state, strategy=best.strategy, extra_hint=repair_prompt),
                temperature=best.temperature,
                model=best.model or None,
            )
            repaired_patch = _extract_diff(raw)
            if repaired_patch and best.worktree and Path(best.worktree).exists():
                _reset(best.worktree)
                ok, msg = _apply(best.worktree, repaired_patch)
                if ok:
                    gate = compile_gate(best.worktree, repaired_patch, baseline_repo=state.repo_path)
                    if gate.ok:
                        best.patch = repaired_patch
                        best.apply_ok = True
                        best.gate_ok = True
                        best.changed = changed_files(repaired_patch)
                        best.added, best.removed = diff_stats(repaired_patch)
                        best.rounds += 1
                        # If repro was previously run and available, re-verify
                        if best.repro.get("available") and verify_on:
                            try:
                                from src.bench import verify as vfy
                                from src.bench.dataset import load_records

                                wanted = state.instance_id
                                record = next((r for r in load_records() if r["instance_id"] == wanted), None)
                                if record and record.get("image"):
                                    touched = vfy.touched_targets(record, best.changed, state.repo_path)
                                    best.repro = vfy.verify_instance(
                                        record,
                                        state.regression_test,
                                        best.patch,
                                        touched_targets=touched,
                                    )
                                    best.regression_count = best.repro.get("regressions", 0)
                            except Exception:
                                pass
                        if is_survivor(best):
                            survivors = [best]
                            ordered = [best] + [c for c in ordered if c is not best]
        except Exception as exc:
            print(f"[arbitrator] repair round on best candidate #{best.index} failed: {exc}", file=sys.stderr)

    state.candidates = [c.as_dict() for c in ordered]
    winner = None
    if survivors:
        # P2-05: red-team BLOCK — drop guardrail-blocked winners fail-closed.
        try:
            from src.guardrails.scanner import scan as _scan

            clean = [c for c in survivors
                     if not _scan(c.patch, state.issue_text).get("blocked")]
            if len(clean) < len(survivors):
                state.context_notes = list(state.context_notes) + [
                    f"candidate_node: {len(survivors)-len(clean)} survivor(s) BLOCKED by guardrails"
                ]
            survivors = clean
        except Exception:
            pass
        winner = survivors[0] if survivors else None
    if winner:
        state.patch = winner.patch
        state.strategy = winner.strategy
        state.laya_scores = {**winner.laya, "combined": winner.combined_score,
                             "mode": winner.rank_reason}
        state.selected_candidate = {
            **winner.as_dict(),
            "beat": len([c for c in ordered if c is not winner]),
        }
        print(f"[arbitrator] winning candidate #{winner.index} "
              f"model='{winner.model or getattr(state, 'model_name', 'coder')}' "
              f"strategy='{winner.strategy}' score={winner.combined_score:.3f}",
              file=sys.stderr)
    else:
        state.patch = ""
        state.escalation = "no confident fix"
        state.selected_candidate = ordered[0].as_dict() if ordered else {}
        state.context_notes = list(state.context_notes) + [
            "candidate_node: no candidate survived verification; reported 'no confident fix'"
        ]
        print("[arbitrator] no candidate survived verification; reported 'no confident fix'", file=sys.stderr)

    try:
        from src.agents.candidates import record_candidates_log
        record_candidates_log(instance_id, candidates, winner.index if winner is not None else None)
    except Exception:
        pass

    cleanup_candidates(candidates, state.repo_path)
    state.model_log = get_model_log()
    return state


def _verify_candidates(state: AgentState, candidates) -> None:
    """Run the repro test inside the instance image for each valid candidate."""
    from src.bench import verify as vfy

    valid = [c for c in candidates if c.valid and c.patch]
    if not valid:
        return

    record = None
    try:
        from src.bench.dataset import load_records

        wanted = state.instance_id
        record = next((r for r in load_records() if r["instance_id"] == wanted), None)
    except Exception:
        record = None
    if not record or not record.get("image"):
        for cand in candidates:
            cand.repro = {"available": False, "reason": "instance record has no image"}
        return

    ready, why = vfy.docker_ready()
    if not ready:
        for cand in candidates:
            cand.repro = {"available": False, "reason": f"docker unavailable: {why}"}
        return

    meta = vfy.instance_meta(record)
    # Remember whether the image was already on disk: only an image this run
    # pulled may be dropped again, otherwise verification would delete a
    # pre-warmed image that the next instance would have to re-download.
    prewarmed = vfy.image_available(meta["image"])
    if not prewarmed:
        vfy.pull_image(meta["image"])
    if not vfy.image_available(meta["image"]):
        for cand in candidates:
            cand.repro = {"available": False,
                          "reason": f"image unavailable: {meta['image']}"}
        return

    try:
        touched = vfy.touched_targets(record, valid[0].changed, state.repo_path)
    except Exception:
        touched = []

    max_verify = int(os.getenv("ISHA_VERIFY_MAX", "3"))
    try:
        from src.agents.candidates import _apply, _reset
        from src.bench.gates import changed_files, compile_gate, diff_stats

        for cand in valid[:max(1, max_verify)]:
            cand.repro = vfy.verify_instance(
                record,
                state.regression_test,
                cand.patch,
                touched_targets=touched,
            )
            cand.regression_count = cand.repro.get("regressions", 0)

            # Closed loop: on failure, feed the trimmed real pytest traceback back
            # to the Coder (max 2 rounds, stop early if the same failure repeats).
            prev_tb = ""
            for repair_round in range(1, 3):
                failed_repro = cand.repro.get("available") and cand.repro.get("before_ok") and not cand.repro.get("after_ok")
                has_regressions = cand.regression_count > 0
                if not (failed_repro or has_regressions):
                    break

                raw_output = cand.repro.get("after_output", "")
                trimmed_tb = trim_traceback(raw_output)
                if trimmed_tb and trimmed_tb == prev_tb:
                    print(f"[verifier] candidate #{cand.index} repair round {repair_round}: identical failure repeated, stopping early", file=sys.stderr)
                    break
                prev_tb = trimmed_tb

                fail_reason = "reproduction test failed" if failed_repro else f"{cand.regression_count} regression(s) in touched modules"
                repair_prompt = (
                    f"\n\nCONTAINER TEST RUN FAILED ({fail_reason}).\n"
                    "TRIMMED REAL PYTEST TRACEBACK / FAILURE OUTPUT:\n"
                    f"{trimmed_tb}\n\n"
                    "Diagnose the failure from the traceback and emit a corrected unified diff patch."
                )
                try:
                    preferred = cand.model or None
                    raw = call_coder(
                        build_coder_prompt(state, strategy=cand.strategy, extra_hint=repair_prompt),
                        temperature=cand.temperature,
                        model=preferred,
                    )
                    new_patch = _extract_diff(raw)
                    if not new_patch:
                        break

                    _reset(cand.worktree)
                    ok, msg = _apply(cand.worktree, new_patch)
                    if not ok:
                        break
                    gate = compile_gate(cand.worktree, new_patch, baseline_repo=state.repo_path)
                    if not gate.ok:
                        break

                    new_repro = vfy.verify_instance(
                        record,
                        state.regression_test,
                        new_patch,
                        touched_targets=touched,
                    )
                    cand.patch = new_patch
                    cand.apply_ok = True
                    cand.gate_ok = True
                    cand.repro = new_repro
                    cand.regression_count = new_repro.get("regressions", 0)
                    cand.changed = changed_files(new_patch)
                    cand.added, cand.removed = diff_stats(new_patch)
                    cand.rounds += 1

                    if new_repro.get("after_ok") and cand.regression_count == 0:
                        print(f"[verifier] candidate #{cand.index} closed-loop repaired on round {repair_round}", file=sys.stderr)
                        break
                except Exception as exc:
                    print(f"[verifier] candidate #{cand.index} repair error: {exc}", file=sys.stderr)
                    break
    finally:
        # Eval images are ~4GB each and a 30-instance run would need ~125GB.
        # Drop anything this instance pulled so the run stays bounded by one
        # image, not by the size of the slice.
        if not prewarmed and os.getenv("ISHA_VERIFY_KEEP_IMAGES", "0") != "1":
            from src.bench.harness_eval import cleanup_images

            try:
                cleanup_images()
            except Exception:
                pass


def sandbox_node(state: AgentState) -> AgentState:
    """Run tests against the candidate patch in an isolated copy."""
    state = coerce_state(state)
    if state.escalation == "no confident fix":
        state.test_output = "NO CONFIDENT FIX: all candidates rejected by gates/verification"
        state.local_sandbox_status = "no_fix"
        return state
    if not state.repo_path:
        state.test_output = "FAILED: no repo_path set"
        state.local_sandbox_status = "infra"
        return state
    if not state.patch or state.patch.startswith("[CODER ERROR]"):
        state.test_output = "FAILED: no patch to apply"
        state.local_sandbox_status = "infra"
        return state

    repo = Path(state.repo_path)
    if not repo.exists():
        state.test_output = f"FAILED: repo path missing: {state.repo_path}"
        state.local_sandbox_status = "infra"
        return state

    # Each attempt works on its own isolated directory: a git worktree
    # or a fresh scratch copy.
    if state.worktree:
        target = Path(state.worktree)
        if not target.exists():
            state.test_output = f"FAILED: worktree missing: {state.worktree}"
            state.local_sandbox_status = "infra"
            return state
        if (target / ".git").exists():
            import subprocess

            subprocess.run(
                ["git", "checkout", "--", "."],
                cwd=str(target),
                capture_output=True,
            )
        else:
            from src.tools.sandbox import copy_repo

            copy_repo(str(repo), str(target))
    else:
        state.worktree = make_sandbox(str(repo))
        target = Path(state.worktree)

    # 1. Cross-file consistency checks
    from src.tools.consistency_checker import check_patch_consistency

    warnings = check_patch_consistency(str(target), state.patch)
    state.consistency_warnings = warnings

    # 2. Apply patch
    ok, message = apply_patch(str(target), state.patch)
    if not ok:
        state.context_notes = list(state.context_notes) + [
            f"patch apply failed: {message[:300]}"
        ]
        state.test_output = f"FAILED: patch could not be applied — {message}"
        state.local_sandbox_status = "failed"
        return state

    # 2b. Static compile & syntax gate with verbatim surrounding context:
    # Fails fast on SyntaxError, IndentationError, ast.parse failure before running dynamic tests
    from src.bench.gates import compile_gate, format_gate_errors_with_context

    gate = compile_gate(str(target), state.patch, baseline_repo=state.repo_path)
    if not gate.ok:
        gate_ctx = format_gate_errors_with_context(str(target), gate.errors)
        state.context_notes = list(state.context_notes) + [
            f"static gate rejected the patch: {e}" for e in gate.errors[:5]
        ]
        state.test_output = (
            "FAILED: STATIC GATE (COMPILER/SYNTAX ERROR):\n"
            + (gate_ctx or "; ".join(gate.errors[:6]))
        )
        state.local_sandbox_status = "failed"
        return state

    if _bench_mode():

        # GAP 1 & GAP 6: Dynamic verification inside the agent loop.
        # When dynamic feedback is enabled or docker sandbox is available, run the
        # regression test so wrong patches fail and trigger the coder self-correction retry loop!
        from src.tools import docker_sandbox
        if os.getenv("ISHA_BENCH_TEST_FEEDBACK", "0") == "1" or docker_sandbox.enabled():
            test_file = None
            if state.regression_test and not state.regression_test.startswith("#"):
                try:
                    (target / "test_regression_isha.py").write_text(
                        _strip_fences(state.regression_test), encoding="utf-8"
                    )
                    test_file = "test_regression_isha.py"
                except OSError:
                    pass
            if test_file:
                dyn_output = run_tests(str(target), test_file=test_file)
                if dyn_output and ("FAILED" in dyn_output or "Traceback" in dyn_output or "Error" in dyn_output):
                    state.context_notes = list(state.context_notes) + [
                        "dynamic regression test failed"
                    ]
                    state.test_output = f"FAILED: DYNAMIC REGRESSION TEST — \n{dyn_output}"
                    state.local_sandbox_status = "failed"
                    return state

        state.test_output = (
            "PASSED\n[bench mode] patch applies and passes ast/py_compile/"
            "pyflakes gates; dynamic tests are executed by the official "
            "SWE-bench harness."
        )
        state.full_test_output = ""
        state.local_sandbox_status = "passed"
        return state

    # 3. Write and run regression test
    test_file = None
    if state.regression_test and not state.regression_test.startswith("#"):
        try:
            (target / "test_regression_isha.py").write_text(
                _strip_fences(state.regression_test), encoding="utf-8"
            )
            test_file = "test_regression_isha.py"
        except OSError:
            pass

    output = run_tests(str(target), test_file=test_file)
    if not output:
        output = "sandbox produced no output"

    verdict = _verdict(output)

    # 4. If regression test passes, run full repo test suite to catch collateral breakage.
    # Only flag as regression if NEW failures are introduced that were NOT already failing in baseline.
    if verdict == "PASSED":
        full_output = run_tests(str(target), test_file=None)
        state.full_test_output = full_output
        baseline = state.investigation_report or ""

        # Extract failed test identifiers
        curr_failed = set(re.findall(r"FAILED\s+([^\s]+)", full_output))
        base_failed = set(re.findall(r"FAILED\s+([^\s]+)", baseline))

        # True regressions are tests that failed now but were NOT failing at baseline
        new_regressions = curr_failed - base_failed
        if new_regressions:
            reg_list = "\n".join(f"- {f}" for f in sorted(new_regressions))
            state.test_output = (
                f"FAILED: Collateral regression detected! New test passed, but previously working tests broke:\n"
                f"{reg_list}\n\nFull pytest output:\n{full_output}"
            )
            state.local_sandbox_status = "failed"
            return state

    state.test_output = f"{verdict}\n{output}"
    state.local_sandbox_status = verdict.lower()
    return state


def _verdict(output: str) -> str:
    """Turn raw pytest output into a PASSED/FAILED marker for the graph."""
    # NOTE: "0 failed" must NOT read as FAILED ([1-9] requires a real failure;
    # mirrors baseline_red_gate_node's r"\b[1-9]\d* failed\b").
    if re.search(r"\b[1-9]\d*\s+failed\b", output):
        return "FAILED"
    if re.search(r"\b\d+\s+passed\b", output):
        return "PASSED"
    if output.startswith("FAILED") or "Traceback" in output or "error" in output.lower():
        return "FAILED"
    return "FAILED"
