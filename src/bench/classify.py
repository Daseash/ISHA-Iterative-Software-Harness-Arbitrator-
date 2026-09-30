"""
ISHA Failure Categorisation — why did each instance not resolve?

Buckets, assigned in this order (first match wins):

    not_run              the instance has no record at all — the runner never
                         reached it (aborted run, stale slice). Counting
                         these as api_failure would make an incomplete run
                         look like a provider outage.
    api_failure          a live model was called and none of the chain
                         answered
    harness_no_output    a patch exists but the official harness produced no
                         test output at all (image/container problem), which
                         is an infrastructure failure, not a model one
    timeout              the per-instance time budget ran out
    patch_apply_failed   the generated diff would not apply in the container
    syntax_error         the changed files do not compile / raise on import
    localization_wrong   tests failed *and* the patch touched no file the
                         gold fix touches (i.e. the bug was found in the
                         wrong place)
    tests_failed         everything else: patch landed, tests still red

Two pre-solve buckets can also appear when the runner short-circuits an
instance: ``checkout_failed`` (the mirror would not materialise) and
``prefiltered`` (record dropped before solving, still counted in the
denominator).

``api_failure`` is reserved for real provider failures because the release
criteria gate on it (must stay under 5%): a category that silently absorbs
"never ran" and "harness broke" cannot be used for that check.

Gold patches are read **only** here, after the run has finished, and only to
tell ``localization_wrong`` from ``tests_failed``.  They are never available
to the solver.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

CATEGORIES = [
    "localization_wrong",
    "patch_apply_failed",
    "syntax_error",
    "tests_failed",
    "timeout",
    "api_failure",
    "no_confident_fix",
    "not_run",
    "harness_no_output",
    "checkout_failed",
    "prefiltered",
]

APPLY_PATCH_FAIL = ">>>>> Patch Apply Failed"
TESTS_TIMEOUT = ">>>>> Tests Timed Out"
TESTS_ERROR = ">>>>> Tests Errored"

_SYNTAX_RE = re.compile(
    r"(SyntaxError|IndentationError|TabError|Error compiling|invalid syntax|"
    r"cannot import name|ModuleNotFoundError)",
    re.I,
)


def gold_files(record: dict) -> set[str]:
    """Files touched by the official gold patch (analysis only)."""
    return set(
        re.findall(r"^\+\+\+ b/(.+)$", record.get("patch", "") or "", re.M)
    )


def gold_symbols(record: dict) -> set[str]:
    """Symbols touched by the official gold patch (analysis only)."""
    patch = record.get("patch", "") or ""
    symbols = set()
    for match in re.finditer(r"^@@\s+-[0-9,]+\s+\+[0-9,]+\s+@@\s*(?:def|class|async def)?\s*([A-Za-z_][A-Za-z0-9_]*)", patch, re.M):
        sym = match.group(1).strip()
        if sym and sym not in ("def", "class", "async"):
            symbols.add(sym)
    return symbols


def patch_files(patch: str) -> set[str]:
    from src.bench.gates import changed_files

    return set(changed_files(patch))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _has_record(meta: dict) -> bool:
    """Did the runner actually get far enough to say anything about this?

    ``build_breakdown`` passes an empty dict when ``meta.json`` is missing
    entirely, which is the normal state for an instance in a run that was cut
    short. Any key the runner always writes counts as a record.
    """
    return any(
        key in meta
        for key in ("status", "instance_id", "elapsed_s", "model_log", "attempts")
    )


def classify_instance(
    meta: dict,
    harness_log_dir: Path | None,
    gold: dict | None,
    resolved: bool,
) -> str:
    """Return the failure bucket for one instance (``""`` when resolved)."""
    if resolved:
        return ""

    # 0. The runner never got to this instance at all.
    if not _has_record(meta):
        return "not_run"

    patch = meta.get("model_patch", "") or ""

    # 1. Never even produced a patch.
    if not patch.strip():
        return meta.get("failure_category") or "api_failure"

    if not harness_log_dir or not harness_log_dir.is_dir():
        # The harness never ran it — agent-side categories still apply.
        return meta.get("failure_category") or "tests_failed"

    output = _read(harness_log_dir / "test_output.txt")
    run_log = _read(harness_log_dir / "run_instance.log")
    blob = output + "\n" + run_log

    # 2. Patch did not land inside the container.
    if APPLY_PATCH_FAIL in blob:
        return "patch_apply_failed"

    # 3. Harness never even started the tests (image/container problems) —
    #    an infrastructure failure, so it must not pollute api_failure.
    if not output.strip():
        return meta.get("failure_category") or "harness_no_output"

    # 4. Timed out.
    if TESTS_TIMEOUT in blob or "timed out" in blob.lower():
        return "timeout"

    # 5. Syntax / import failures — the patch does not even load.
    head = "\n".join(output.splitlines()[:120])
    if _SYNTAX_RE.search(head) and "passed" not in head.lower():
        return "syntax_error"

    # 6. Tests ran and failed: wrong place, or right place, wrong fix?
    if gold:
        touched = patch_files(patch)
        expected = gold_files(gold)
        if touched and expected and not (touched & expected):
            return "localization_wrong"
        # Overlap exists but nothing in the overlap changed meaningfully.
        if not touched:
            return "localization_wrong"
    return "tests_failed"


STAGE_NAMES = [
    "localization_hit_file",
    "localization_hit_func",
    "patch_applied",
    "static_gate_passed",
    "env_ok",
    "repro_fails_before",
    "repro_passes_after",
    "zero_regressions",
    "resolved",
]


def build_breakdown(
    run_dir: Path,
    records: list[dict],
    report: dict,
    eval_id: str | None = None,
) -> dict:
    """Classify every instance of a run and aggregate the buckets and stage outcomes."""
    resolved_ids = set(report.get("resolved_ids", []) or [])
    log_root = run_dir / "logs" / "run_evaluation"

    def _log_dir(iid: str) -> Path | None:
        if not log_root.is_dir():
            return None
        for run in sorted(log_root.iterdir()):
            if eval_id and run.name != eval_id:
                continue
            cand = run / "isha" / iid
            if cand.is_dir():
                return cand
        return None

    rows = []
    counts = Counter({c: 0 for c in CATEGORIES})
    stage_counts = Counter({s: 0 for s in STAGE_NAMES})

    for record in records:
        iid = record["instance_id"]
        meta_path = run_dir / iid.replace("/", "__") / "meta.json"
        meta = {}
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        resolved = iid in resolved_ids
        category = classify_instance(meta, _log_dir(iid), record, resolved)

        gold_f = gold_files(record)
        gold_s = gold_symbols(record)

        loc_entries = meta.get("localization") or []
        loc_files = set()
        loc_symbols = set()
        for le in loc_entries:
            if isinstance(le, dict):
                f = le.get("file")
                if f:
                    loc_files.add(f)
                s = le.get("symbol", "")
                if s:
                    loc_symbols.add(s.split("::")[-1])
        if not loc_files:
            loc_files = patch_files(meta.get("model_patch", ""))

        loc_hit_file = bool(loc_files & gold_f) if gold_f else False
        loc_hit_func = bool(loc_symbols & gold_s) if gold_s else loc_hit_file

        patch_applied = bool(meta.get("patch_info", {}).get("applied", False)) or (
            bool((meta.get("model_patch") or "").strip()) and category != "patch_apply_failed"
        )
        static_gate_passed = bool(meta.get("patch_info", {}).get("gates", {}).get("ok", False)) or (
            patch_applied and category not in ("syntax_error", "patch_apply_failed")
        )
        selected_cand = meta.get("selected_candidate") or {}
        ver = selected_cand.get("verification") or {}
        env_ok = bool(ver.get("available", False)) or (category not in ("harness_no_output", "checkout_failed"))
        repro_fails_before = bool(ver.get("before_ok", False))
        repro_passes_after = bool(ver.get("after_ok", False))
        zero_regressions = (ver.get("regressions", 0) == 0) if "regressions" in ver else (category != "tests_failed")

        stage_outcomes = {
            "localization_hit_file": loc_hit_file,
            "localization_hit_func": loc_hit_func,
            "patch_applied": patch_applied,
            "static_gate_passed": static_gate_passed,
            "env_ok": env_ok,
            "repro_fails_before": repro_fails_before,
            "repro_passes_after": repro_passes_after,
            "zero_regressions": zero_regressions,
            "resolved": resolved,
        }
        for s_name, passed in stage_outcomes.items():
            if passed:
                stage_counts[s_name] += 1

        rows.append({
            "instance_id": iid,
            "resolved": resolved,
            "category": category or ("resolved" if resolved else "tests_failed"),
            "has_patch": bool((meta.get("model_patch") or "").strip()),
            "attempts": meta.get("attempts", 0),
            "elapsed_s": meta.get("elapsed_s"),
            "critic_score": meta.get("critic_score"),
            "offline_calls": meta.get("offline_calls", 0),
            "primary_model": _primary_model(meta),
            "stage_outcomes": stage_outcomes,
        })
        if category:
            counts[category] += 1

    return {"rows": rows, "counts": counts, "stage_counts": stage_counts}


def _primary_model(meta: dict) -> str:
    """Model that actually answered the coder role, plus its chain position."""
    entries = meta.get("model_log") or []
    coder = [e for e in entries if e.get("role") == "coder"]
    if not coder:
        return "n/a"
    last = coder[-1]
    return f"{last.get('model')} [{last.get('position')}]"
