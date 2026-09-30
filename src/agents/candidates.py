"""
ISHA Candidate Generation — Phase 4 of the SWE-bench upgrade.

One bug, N attempts.  Each candidate is

  * generated with its own strategy prompt **and** temperature,
  * built inside its own git worktree so candidates never contaminate each
    other, and
  * gated *before* any test runs: the diff must apply (with the exact apply
    error fed back on failure, at most 2 retries) and every changed Python
    file must pass ``ast.parse`` / ``py_compile`` / ``pyflakes``.

Candidates that survive the gates are then scored (Phase 5/6) and one is
selected as the patch that goes to the harness.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor
from src.agents.nodes import _extract_diff, build_coder_prompt
from src.agents.state import AgentState
from src.bench.gates import changed_files, compile_gate, diff_stats
from src.config import CANDIDATE_1_MODEL, CANDIDATE_2_MODEL, CANDIDATE_3_MODEL

MAX_REPAIR_ROUNDS = int(os.getenv("ISHA_APPLY_REPAIR_ROUNDS", "2"))

# Which model each strategy is *preferred* to run on.
#
# The point is diversity of capability, not just of prompt: a surgical
# one-line edit and a cross-call-site refactor are not the same job, so
# three distinct models (Qwen, GPT-OSS-120B, Gemini) generate candidates
# for true multi-model arbitration.
#
# Override without touching code:
#   ISHA_CANDIDATE_MODELS=minimal_diff=groq/openai/gpt-oss-20b,call_site_aware=gemini/gemini-3.1-flash-lite
DEFAULT_STRATEGY_MODELS: dict[str, str] = {
    "coder_default": CANDIDATE_1_MODEL,      # seed patch / primary model
    "minimal_diff": CANDIDATE_1_MODEL,        # groq/qwen/qwen3.8-27b: surgical, low-temp, AST-focused
    "call_site_aware": CANDIDATE_2_MODEL,    # groq/openai/gpt-oss-120b: largest reasoning budget
    "root_cause_first": CANDIDATE_3_MODEL,   # gemini/gemini-3.8-flash: long-context boundary & invariants
    "defensive_fix": CANDIDATE_1_MODEL,      # defensive guardrails
    "cross_file_audit": CANDIDATE_3_MODEL,   # wide-reach audit work
}


def strategy_models() -> dict[str, str]:
    """Preferred model per strategy, with ``ISHA_CANDIDATE_MODELS`` layered on top."""
    merged = dict(DEFAULT_STRATEGY_MODELS)
    raw = os.getenv("ISHA_CANDIDATE_MODELS", "").strip()
    for part in raw.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key, value = key.strip(), value.strip()
        if key:
            merged[key] = value
    return merged


# (name, temperature, strategy notes) — varied on purpose: identical prompts
# at identical temperatures produce identical patches, which defeats the
# point of generating N candidates.
STRATEGY_VARIANTS = [
    (
        "minimal_diff",
        0.15,
        "Smallest possible diff. Touch the fewest lines and fewest files "
        "that can fix the reported behaviour. Prefer an early return or a "
        "one-line condition over a restructure.",
    ),
    (
        "call_site_aware",
        0.35,
        "Fix the root cause and update every caller in the same diff. If the "
        "signature or semantics change, propagate the change to all call "
        "sites so no caller keeps the old contract.",
    ),
    (
        "root_cause_first",
        0.6,
        "Re-read the reported symptom and fix the underlying invariant rather "
        "than the observed line. Guard the boundary that actually violates the "
        "documented behaviour.",
    ),
    (
        "defensive_fix",
        0.8,
        "Fix the reported bug and close the adjacent edge cases the report "
        "implies (invalid input, empty/zero values, case sensitivity), while "
        "still keeping the diff minimal and backward compatible.",
    ),
    (
        "cross_file_audit",
        1.0,
        "Audit the localized files and their direct callers for any place the "
        "same wrong assumption is duplicated; fix all of them in one atomic "
        "diff.",
    ),
]


@dataclass
class Candidate:
    index: int
    strategy: str
    temperature: float
    model: str = ""
    requested_model: str = ""
    substituted: bool = False
    patch: str = ""
    worktree: str = ""
    apply_ok: bool = False
    apply_message: str = ""
    gate_ok: bool = False
    gate_errors: list = field(default_factory=list)
    changed: list = field(default_factory=list)
    added: int = 0
    removed: int = 0
    rounds: int = 0
    laya: dict = field(default_factory=dict)
    laya_combined: float = 0.0
    repro: dict = field(default_factory=dict)
    regression_count: int = 0
    combined_score: float = 0.0
    rank_reason: str = ""
    elapsed_s: float = 0.0

    @property
    def valid(self) -> bool:
        return bool(self.patch) and self.apply_ok and self.gate_ok

    @property
    def diff_size(self) -> int:
        return self.added + self.removed

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "strategy": self.strategy,
            "temperature": self.temperature,
            "model": self.model,
            "requested_model": self.requested_model,
            "substituted": self.substituted,
            "patch": self.patch,
            "worktree": self.worktree,
            "apply_ok": self.apply_ok,
            "apply_message": self.apply_message[:500],
            "gate_ok": self.gate_ok,
            "gate_errors": self.gate_errors[:8],
            "changed_files": self.changed,
            "added_lines": self.added,
            "removed_lines": self.removed,
            "repair_rounds": self.rounds,
            "laya": self.laya,
            "laya_combined": round(self.laya_combined, 4),
            "repro": self.repro,
            "regression_count": self.regression_count,
            "combined_score": round(self.combined_score, 4),
            "rank_reason": self.rank_reason,
            "elapsed_s": round(self.elapsed_s, 2),
            "valid": self.valid,
        }


def _repo_slug(repo_path: str, instance_id: str) -> str:
    return (instance_id or Path(repo_path).name).replace("/", "__")[:60]


def _make_worktree(repo_path: str, instance_id: str, index: int) -> str:
    try:
        from src.tools.worktree_manager import create_worktree

        return create_worktree(repo_path, f"{_repo_slug(repo_path, instance_id)}-c{index}")
    except Exception:
        # Non-git repo (or worktree exhausted): an isolated copy is enough
        # for apply + static gating.
        from src.tools.sandbox import make_sandbox

        return make_sandbox(repo_path)


def _apply(worktree: str, patch: str) -> tuple[bool, str]:
    from src.tools.patch_engine import apply_patch

    return apply_patch(worktree, patch)


def _reset(worktree: str) -> None:
    import subprocess

    if Path(worktree, ".git").exists():
        subprocess.run(["git", "checkout", "--", "."], cwd=worktree, capture_output=True)
        subprocess.run(["git", "clean", "-xfd"], cwd=worktree, capture_output=True)


def _build_candidate(
    index: int,
    name: str,
    temperature: float,
    notes: str,
    use_seed: bool,
    seed_patch: str,
    state: AgentState,
    instance_id: str,
    preferred_models: dict[str, str],
    seed_model: str = "",
    log=None,
) -> Candidate:
    from src.config import call_coder, get_model_log

    started = time.time()
    cand = Candidate(index=index, strategy=name, temperature=temperature)
    preferred = (preferred_models.get(name) or "").strip() or None
    cand.requested_model = preferred or ""
    cand.model = preferred or ""
    try:
        cand.worktree = _make_worktree(state.repo_path, instance_id, index)
    except Exception as exc:
        cand.apply_message = f"worktree failed: {exc}"
        cand.elapsed_s = time.time() - started
        return cand

    prompt = ""
    if notes:
        prompt = build_coder_prompt(
            state,
            strategy=name,
            extra_hint="\n\nSTRATEGY NOTES:\n" + notes,
        )
    feedback = ""
    patch = ""
    for round_idx in range(MAX_REPAIR_ROUNDS + 1):
        cand.rounds = round_idx
        if round_idx == 0 and use_seed and seed_patch:
                patch = seed_patch
                cand.model = seed_model or preferred or "seed"
                if cand.requested_model:
                    from src.config import _short_name
                    cand.substituted = (_short_name(cand.model) != _short_name(cand.requested_model))
        else:
            mark = len(get_model_log())
            raw = call_coder(prompt + feedback, temperature=temperature, model=preferred)
            answered = [e for e in get_model_log()[mark:]
                        if e.get("role") == "coder"
                        and e.get("thread") == threading.current_thread().name]
            if answered:
                cand.model = answered[-1].get("model_full", "") or cand.model
                if cand.requested_model:
                    from src.config import _short_name
                    cand.substituted = (_short_name(cand.model) != _short_name(cand.requested_model))
            patch = _extract_diff(raw)
        _reset(cand.worktree)
        ok, message = _apply(cand.worktree, patch)
        if not ok:
            from src.tools.patch_engine import record_apply_failure
            record_apply_failure(instance_id, index, round_idx, patch, message)
            if round_idx == 0 and use_seed and seed_patch:
                prompt = build_coder_prompt(state, strategy=name)
            feedback = (
                "\n\nTHE PREVIOUS DIFF DID NOT APPLY. Exact error:\n"
                f"{message}\n\nReproduce the surrounding lines exactly as "
                "they appear in the file and emit a corrected diff."
            )
            if log:
                log({
                    "event": "apply_retry",
                    "candidate": index,
                    "model": cand.model,
                    "round": round_idx,
                    "error": message[:300],
                })
            continue

        canonical_patch = patch
        if Path(cand.worktree, ".git").exists():
            import subprocess
            proc = subprocess.run(
                ["git", "diff", "--no-color"],
                cwd=cand.worktree,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode == 0 and proc.stdout.strip():
                canonical_patch = proc.stdout

        from src.tools.patch_engine import record_apply_failure, validate_patch
        val_ok, val_msg = validate_patch(state.repo_path, canonical_patch)
        if not val_ok:
            record_apply_failure(instance_id, index, round_idx, canonical_patch, f"git apply --check failed: {val_msg}")
            if round_idx == 0 and use_seed and seed_patch:
                prompt = build_coder_prompt(state, strategy=name)
            feedback = (
                "\n\nTHE GENERATED DIFF FAILED `git apply --check` ON THE BASE REPO. Exact error:\n"
                f"{val_msg}\n\nEmit a corrected diff that applies cleanly."
            )
            if log:
                log({
                    "event": "apply_check_retry",
                    "candidate": index,
                    "model": cand.model,
                    "round": round_idx,
                    "error": val_msg[:300],
                })
            continue

        gate = compile_gate(cand.worktree, canonical_patch, baseline_repo=state.repo_path)
        if not gate.ok:
            if round_idx == 0 and use_seed and seed_patch:
                prompt = build_coder_prompt(state, strategy=name)
            feedback = (
                "\n\nTHE PREVIOUS DIFF FAILED THE STATIC GATES. Errors:\n"
                + "\n".join(f"- {e}" for e in gate.errors[:6])
                + "\nEmit a corrected diff that parses cleanly."
            )
            if log:
                log({
                    "event": "gate_retry",
                    "candidate": index,
                    "model": cand.model,
                    "round": round_idx,
                    "errors": gate.errors[:6],
                })
            continue
        cand.patch, cand.apply_ok, cand.apply_message = canonical_patch, True, message
        cand.gate_ok, cand.gate_errors = True, []
        break
    else:
        cand.patch = patch
        cand.apply_ok = False

    if not cand.apply_ok and patch:
        cand.patch = patch
        gate = compile_gate(cand.worktree, patch, baseline_repo=state.repo_path) if Path(cand.worktree).exists() else None
        if gate is not None:
            cand.gate_ok = gate.ok
            cand.gate_errors = gate.errors

    cand.changed = changed_files(cand.patch)
    cand.added, cand.removed = diff_stats(cand.patch)
    cand.elapsed_s = time.time() - started
    return cand


def generate_candidates(
    state: AgentState,
    n: int = 3,
    instance_id: str = "",
    seed_patch: str = "",
    log=None,
) -> list[Candidate]:
    """Produce up to ``n`` gated candidates across distinct models, each in its own worktree.

    Candidate 1: Minimal diff (Qwen 3.8/2.5) — fast AST logic
    Candidate 2: Call-site aware (GPT-OSS 120B) — deep architectural reasoning
    Candidate 3: Root-cause first (Gemini 3.8 Flash) — long context & boundary invariants

    Candidates run concurrently in parallel via ThreadPoolExecutor so generating
    3 models takes roughly the same wall-clock time as 1.
    """
    preferred_models = strategy_models()
    has_seed = bool(seed_patch and not seed_patch.startswith("["))

    jobs: list[tuple[str, float, str, bool]] = []
    if has_seed:
        jobs.append(("coder_default", 0.2, "", True))
        remaining_strats = [s for s in STRATEGY_VARIANTS if s[0] != "minimal_diff"]
        for name, temp, notes in remaining_strats:
            if len(jobs) >= max(1, n):
                break
            jobs.append((name, temp, notes, False))
    else:
        for name, temp, notes in STRATEGY_VARIANTS:
            if len(jobs) >= max(1, n):
                break
            jobs.append((name, temp, notes, False))

    parallel = os.getenv("ISHA_CANDIDATES_PARALLEL", "1") != "0"
    # Read once, before any worker thread runs: the seed patch's author is the
    # last coder call the node made, and later thread calls would pollute it.
    seed_model = ""
    if has_seed:
        from src.config import get_model_log

        for entry in reversed(get_model_log()):
            if entry.get("role") == "coder":
                seed_model = entry.get("model_full", "")
                break
    if parallel and len(jobs) > 1:
        with ThreadPoolExecutor(max_workers=len(jobs), thread_name_prefix="isha-cand") as pool:
            futures = [
                pool.submit(
                    _build_candidate,
                    index, name, temperature, notes, use_seed,
                    seed_patch, state, instance_id, preferred_models, seed_model, log,
                )
                for index, (name, temperature, notes, use_seed) in enumerate(jobs, start=1)
            ]
            candidates = [f.result() for f in futures]
    else:
        candidates = [
            _build_candidate(
                index, name, temperature, notes, use_seed,
                seed_patch, state, instance_id, preferred_models, seed_model, log,
            )
            for index, (name, temperature, notes, use_seed) in enumerate(jobs, start=1)
        ]

    return candidates


def is_survivor(c: Candidate) -> bool:
    """True when candidate passes static gates, introduces zero regressions, and passes repro if tested."""
    if not c.valid:
        return False
    if c.regression_count > 0:
        return False
    repro = c.repro or {}
    if repro.get("available") and repro.get("before_ok") and not repro.get("after_ok"):
        return False
    return True


def rank_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Phase 5 ordering — hard evidence first, LAYA ranks survivors, smallest diff breaks ties.

    Survivors:
      Tier 0: repro confirmed (fails before, passes after) & 0 regressions
      Tier 1: repro neutral (passed unpatched, discarded) & 0 regressions
      Tier 2: repro unavailable (infra missing) & 0 regressions

    Disqualified:
      Tier 3: regression detected (newly failing tests in touched modules)
      Tier 4: repro ran and failed
      Tier 5: gates failed or invalid diff
    """

    def key(c: Candidate):
        repro = c.repro or {}
        if not c.valid:
            tier = 5
        elif c.regression_count > 0:
            tier = 3  # newly failing tests disqualify
        elif repro.get("available") and repro.get("before_ok") and not repro.get("after_ok"):
            tier = 4  # failed repro
        elif repro.get("available") and repro.get("before_ok") and repro.get("after_ok"):
            tier = 0  # repro confirmed
        elif repro.get("available"):
            tier = 1  # neutral
        else:
            tier = 2  # infra unavailable
        return (tier, -c.combined_score, c.diff_size)

    return sorted(candidates, key=key)


def cleanup_candidates(candidates: list[Candidate], repo_path: str) -> None:
    """Remove every worktree / scratch copy a candidate created."""
    try:
        from src.tools.worktree_manager import cleanup_all_worktrees

        cleanup_all_worktrees(repo_path)
    except Exception:
        pass
    for cand in candidates:
        if cand.worktree and not Path(cand.worktree).exists():
            continue
        try:
            from src.tools.sandbox import cleanup_sandbox

            if Path(cand.worktree).parent.name == ".worktrees":
                continue  # handled by cleanup_all_worktrees
            if Path(cand.worktree).name.startswith("isha-sandbox-"):
                cleanup_sandbox(cand.worktree)
        except Exception:
            pass


def record_candidates_log(instance_id: str, candidates: list[Candidate], winner_index: int | None = None) -> None:
    """Save candidate evaluation outcomes to results/candidates.json."""
    import json
    path = Path(__file__).resolve().parents[2] / "results" / "candidates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    for c in candidates:
        repro = c.repro or {}
        entry = {
            "instance_id": instance_id,
            "candidate_index": c.index,
            "strategy": c.strategy,
            "temperature": c.temperature,
            "requested_model": getattr(c, "requested_model", "") or c.model,
            "model_used": c.model,
            "substituted": getattr(c, "substituted", False),
            "patch_applied": c.apply_ok,
            "gate_passed": c.gate_ok,
            "repro_passed": bool(repro.get("before_ok") and repro.get("after_ok")),
            "regression_count": c.regression_count,
            "diff_size": c.diff_size,
            "laya_score": c.laya_combined,
            "won_selection": winner_index is not None and c.index == winner_index,
            "timestamp": time.time(),
        }
        existing.append(entry)

    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def summarize_candidates(path: Path | str | None = None) -> dict:
    """Aggregate per-candidate tournament statistics for Stage D reporting."""
    import json
    p = Path(path) if path else (Path(__file__).resolve().parents[2] / "results" / "candidates.json")
    if not p.is_file():
        return {"total_candidates": 0, "models": {}}
    rows = json.loads(p.read_text(encoding="utf-8"))
    models = {}
    for r in rows:
        m = r.get("model_used") or "unknown"
        if m not in models:
            models[m] = {
                "total": 0,
                "substituted": 0,
                "applied": 0,
                "gates": 0,
                "repro_passed": 0,
                "won": 0,
            }
        models[m]["total"] += 1
        if r.get("substituted"):
            models[m]["substituted"] += 1
        if r.get("patch_applied"):
            models[m]["applied"] += 1
        if r.get("gate_passed"):
            models[m]["gates"] += 1
        if r.get("repro_passed"):
            models[m]["repro_passed"] += 1
        if r.get("won_selection"):
            models[m]["won"] += 1

    most_wins = max(models.items(), key=lambda t: t[1]["won"])[0] if models else "none"
    never_won = [m for m, stat in models.items() if stat["won"] == 0]
    return {
        "total_candidates": len(rows),
        "models": models,
        "most_wins": most_wins,
        "never_won": never_won,
    }

