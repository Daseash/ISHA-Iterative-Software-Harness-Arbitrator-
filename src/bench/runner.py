"""
ISHA Resumable SWE-bench Runner — Phase 1 measurement.

Design rules:

  * **Checkpoint per instance.**  Everything lands in
    ``results/<run_id>/<instance_id>/``; a re-run of the same ``run_id``
    skips any instance whose ``meta.json`` says ``done``.
  * **No gold patch / test patch during solving.**  Only the fields returned
    by ``bench.dataset.agent_view`` are ever handed to the agent.
  * **Backoff on rate limits.**  An instance that ends in an API failure is
    retried with exponential backoff; providers already marked unavailable
    are reset between instances so one quota blip does not kill the run.
  * **Per-instance log folder.**  ``log.jsonl`` (step/model events),
    ``patch.diff``, ``meta.json``, ``plan.md``.
  * **Model audit.**  Every model call is recorded with its role, model and
    position (primary vs fallback) so results are attributable.

Usage:
    python -m src.bench.runner --limit 30 --run-id baseline
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS_DIR = ROOT / "results"

DEFAULT_INSTANCE_TIMEOUT = int(os.getenv("ISHA_BENCH_INSTANCE_TIMEOUT", "900"))
DEFAULT_MAX_RETRIES = int(os.getenv("ISHA_BENCH_MAX_RETRIES", "2"))
BASE_BACKOFF = float(os.getenv("ISHA_BENCH_BACKOFF", "20"))
# Extra attempts granted only to instances whose diff would not apply.
APPLY_RETRIES = int(os.getenv("ISHA_BENCH_APPLY_RETRIES", "1"))


# ── Environment for a benchmark run ────────────────────────────────────────
def apply_bench_env(
    candidates: int | None = None,
    verify: bool | None = None,
) -> None:
    """Turn on bench mode before any node reads the environment.

    * ``ISHA_BENCH_MODE=1``  — no local pytest (the host has no environment
      for these repos); patches are gated statically instead.
    * confidence threshold 0 — there is no human in the loop during a
      benchmark run, so the pre-patch human-escalation gate is disabled and
      recorded instead of silently producing an empty patch.
    * ``ISHA_CANDIDATES`` / ``ISHA_VERIFY`` — Phase 4/5 switches; defaults
      (1 candidate, verification on) keep the single-candidate baseline path
      unchanged.
    """
    os.environ["ISHA_BENCH_MODE"] = "1"
    os.environ.setdefault("ISHA_CONFIDENCE_THRESHOLD", "0")
    os.environ.setdefault("ISHA_SANDBOX_MODE", "local")
    os.environ.setdefault("ISHA_PROMPT_STATS", "1")
    os.environ.setdefault("ISHA_CANDIDATES", "1")
    if candidates is not None:
        os.environ["ISHA_CANDIDATES"] = str(max(1, candidates))
    if verify is not None:
        os.environ["ISHA_VERIFY"] = "1" if verify else "0"


# ── Per-instance log folder ────────────────────────────────────────────────
def instance_dir(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id.replace("/", "__")


def _append(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def load_checkpoint(path: Path) -> dict | None:
    if not (path / "meta.json").is_file():
        return None
    try:
        return json.loads((path / "meta.json").read_text(encoding="utf-8"))
    except Exception:
        return None


def save_checkpoint(path: Path, meta: dict) -> None:
    path.mkdir(parents=True, exist_ok=True)
    tmp = path / "meta.json.tmp"
    tmp.write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=str),
                   encoding="utf-8")
    tmp.replace(path / "meta.json")


# ── Patch normalisation ────────────────────────────────────────────────────
def canonical_patch(repo_path: str, raw_patch: str, instance_id: str = "") -> tuple[str, dict]:
    """Apply the LLM diff to a clean checkout and read back ``git diff``.

    The **regenerated** diff is what gets submitted: it is produced by git
    from the actual tree, so the harness's own ``git apply`` on the same base
    commit cannot fail on hunk offsets or context drift in the model's text.
    If regeneration is unavailable the raw diff is kept.
    """
    from src.bench.gates import compile_gate
    from src.tools.patch_engine import apply_patch, record_apply_failure, validate_patch
    from src.tools.sandbox import cleanup_sandbox, make_sandbox

    info: dict = {"applied": False, "message": "", "gates": {}, "regenerated": False}
    if not raw_patch or raw_patch.startswith("["):
        info["message"] = "no usable patch"
        return "", info

    sandbox = make_sandbox(repo_path)
    try:
        info["git_ready"] = _ensure_git(sandbox)
        ok, message = apply_patch(sandbox, raw_patch)
        info["applied"] = ok
        info["message"] = message
        if not ok:
            record_apply_failure(instance_id, 0, 0, raw_patch, message)
            return "", info
        gate = compile_gate(sandbox, raw_patch, baseline_repo=repo_path)
        info["gates"] = gate.as_dict()
        if not gate.ok:
            info["message"] = "static gate failed: " + "; ".join(gate.errors)
            return "", info
        if info["git_ready"]:
            regenerated = _git_diff(sandbox)
            if regenerated.strip():
                val_ok, val_msg = validate_patch(repo_path, regenerated)
                info["validate_check_ok"] = val_ok
                info["validate_check_msg"] = val_msg
                if not val_ok:
                    record_apply_failure(instance_id, 0, 0, regenerated, f"git apply --check failed: {val_msg}")
                info["regenerated"] = True
                return regenerated, info
        info["regenerated"] = False
        return raw_patch, info
    finally:
        cleanup_sandbox(sandbox)


def _git_diff(repo_path: str) -> str:
    import subprocess

    try:
        proc = subprocess.run(
            ["git", "diff", "--no-color"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        return proc.stdout or ""
    except Exception:
        return ""


def _ensure_git(root) -> bool:
    """Make a plain sandbox copy diffable.

    ``copy_repo`` deliberately drops ``.git`` (it is a scratch tree), but the
    patch we submit has to be a *git-generated* diff or the harness's own
    ``git apply`` can reject it on hunk offsets.  Initialising an empty repo
    and committing the pristine tree costs a couple of seconds and gives us
    exactly that guarantee.
    """
    import subprocess

    root = Path(root)
    if (root / ".git").exists():
        return True
    base = ["git", "-c", "user.email=isha@local", "-c", "user.name=isha"]
    commands = [
        ["git", "init", "-q"],
        ["git", "config", "core.autocrlf", "false"],
        ["git", "add", "-A"],
        base + ["commit", "-qm", "isha base"],
    ]
    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd, cwd=str(root), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=600,
            )
        except Exception:
            return False
        if proc.returncode != 0:
            return False
    return True


def reset_checkout(repo_path: str) -> None:
    import subprocess

    for cmd in (["git", "checkout", "--", "."], ["git", "clean", "-xfd"]):
        try:
            subprocess.run(cmd, cwd=repo_path, capture_output=True, timeout=300)
        except Exception:
            pass


# ── One instance ───────────────────────────────────────────────────────────
def _invoke_graph(record: dict, thread_id: str, notes: list[str] | None = None) -> dict:
    from src.agents.context import build_repo_context
    from src.agents.graph import compiled_graph
    from src.agents.state import AgentState
    from src.config import clear_model_log, get_model_log

    repo_path = str(instance_checkout(record))
    clear_model_log()
    started = time.time()
    state = AgentState(
        issue_text=record["problem_statement"],
        instance_id=record["instance_id"],
        repo_path=repo_path,
        repo_context=build_repo_context(record["problem_statement"], repo_path),
        context_notes=list(notes or []),
    )
    out = compiled_graph.invoke(
        state,
        config={"configurable": {"thread_id": thread_id, "approval_mode": "auto"}},
    )
    result = AgentState(**out) if isinstance(out, dict) else out
    return {
        "state": result,
        "model_log": get_model_log(),
        "elapsed": round(time.time() - started, 2),
    }


def instance_checkout(record: dict) -> Path:
    from src.bench.checkout import checkout_path

    return checkout_path(record["instance_id"])


def _apply_feedback(repo: Path, info: dict) -> str:
    """Turn a failed apply into something the next attempt can actually use.

    The dominant way a patch dies is a context line the model invented, so the
    useful reply is the *verbatim* source around the failure — not another
    abstract "try again".
    """
    message = str(info.get("message") or "")
    if not message:
        return ""
    rel_match = re.search(r"Hunk failed in ([^:]+):", message)
    rel = rel_match.group(1).strip() if rel_match else ""
    wanted = ""
    ctx_match = re.search(r"not found in file: (.+)$", message, re.S)
    if ctx_match:
        raw = ctx_match.group(1).strip()
        try:
            wanted = str(ast.literal_eval(raw))
        except Exception:
            wanted = raw.strip("'\"")

    header = f"PREVIOUS PATCH DID NOT APPLY. {message[:400]}"
    if not rel:
        return header
    target = repo / rel
    if not target.is_file():
        return header

    try:
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return header

    idx = None
    if wanted:
        probe = wanted.rstrip()
        idx = next(
            (i for i, line in enumerate(lines) if line.rstrip() == probe), None
        )
    if idx is None:
        head = "\n".join(f"{i + 1:5d}| {line}" for i, line in enumerate(lines[:80]))
        return (
            f"{header}\nThe context line {wanted[:160]!r} does not exist in "
            f"{rel}. Do not invent it. The file starts:\n{head}"
        )[:3800]
    lo = max(0, idx - 30)
    hi = min(len(lines), idx + 45)
    body = "\n".join(f"{i + 1:5d}| {lines[i]}" for i in range(lo, hi))
    return (
        f"{header}\nVERBATIM SOURCE OF {rel} LINES {lo + 1}-{hi} — copy these "
        f"lines character-for-character, changing only what the fix requires:\n{body}"
    )[:3800]


def run_instance(
    record: dict,
    path: Path,
    timeout: int = DEFAULT_INSTANCE_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    thread_id: str = "bench",
) -> dict:
    """Solve one instance, writing checkpoints as it goes.

    Returns the final ``meta`` dict.  Re-entrant: a checkpoint marked ``done``
    is returned untouched so the run resumes for free.
    """
    existing = load_checkpoint(path)
    if existing and existing.get("status") == "done":
        existing["resumed"] = True
        return existing

    path.mkdir(parents=True, exist_ok=True)
    log_path = path / "log.jsonl"
    if not log_path.exists():
        _append(log_path, {"event": "start", "instance_id": record["instance_id"],
                           "ts": time.time()})

    from src.config import reset_provider_state

    attempt = 0
    notes: list[str] = []
    meta: dict = {
        "instance_id": record["instance_id"],
        "repo": record["repo"],
        "base_commit": record["base_commit"],
        "status": "started",
        "attempts": 0,
        "failure_category": None,
        "model_log": [],
        "patch_info": {},
        "started_at": time.time(),
    }

    while attempt <= max_retries:
        attempt += 1
        meta["attempts"] = attempt
        reset_provider_state()
        reset_checkout(str(instance_checkout(record)))

        _append(log_path, {"event": "attempt", "n": attempt, "ts": time.time()})
        pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="isha-bench")
        future = pool.submit(_invoke_graph, record, f"{thread_id}-{attempt}", notes)
        try:
            outcome = future.result(timeout=timeout)
        except FutureTimeout:
            meta.update({
                "status": "done",
                "failure_category": "timeout",
                "error": f"instance exceeded {timeout}s",
            })
            save_checkpoint(path, meta)
            pool.shutdown(wait=False, cancel_futures=True)
            _append(log_path, {"event": "timeout", "attempt": attempt, "ts": time.time()})
            return meta
        except Exception as exc:  # noqa: BLE001 — recorded, never crashes the run
            pool.shutdown(wait=False, cancel_futures=True)
            if attempt > max_retries:
                meta.update({
                    "status": "done",
                    "failure_category": "api_failure",
                    "error": f"{type(exc).__name__}: {exc}",
                })
                save_checkpoint(path, meta)
                return meta
            wait = BASE_BACKOFF * (2 ** (attempt - 1))
            _append(log_path, {"event": "error", "attempt": attempt,
                               "error": f"{type(exc).__name__}: {exc}",
                               "backoff_s": wait, "ts": time.time()})
            time.sleep(wait)
            continue
        else:
            pool.shutdown(wait=False)

        state = outcome["state"]
        meta["model_log"] = outcome["model_log"]
        meta["elapsed_s"] = outcome["elapsed"]
        meta["plan"] = state.plan
        meta["planner_confidence"] = state.planner_confidence
        meta["localization"] = state.localization
        meta["retry_count"] = state.retry_count
        meta["critic_verdict"] = state.critic_verdict
        meta["critic_score"] = state.critic_score
        meta["laya_scores"] = state.laya_scores
        meta["test_output"] = (state.test_output or "")[:2000]
        meta["regression_test"] = state.regression_test
        meta["escalation"] = state.escalation
        meta["candidates"] = getattr(state, "candidates", []) or []
        meta["selected_candidate"] = getattr(state, "selected_candidate", {}) or {}

        for entry in outcome["model_log"]:
            _append(log_path, {"event": "model", "ts": entry.get("timestamp"),
                               "role": entry.get("role"), "model": entry.get("model"),
                               "position": entry.get("position"),
                               "note": entry.get("note", "")})

        patch, info = canonical_patch(str(instance_checkout(record)), state.patch, instance_id=record["instance_id"])
        meta["patch_info"] = info
        meta["model_patch"] = patch
        # Always keep the model's own text — it is the only way to see why a
        # patch was rejected after the fact.
        try:
            (path / "raw.patch").write_text(state.patch or "", encoding="utf-8")
        except OSError:
            pass

        offline = [e for e in outcome["model_log"] if e.get("position") == "offline"]
        meta["offline_calls"] = len(offline)

        if not patch:
            meta["failure_category"] = _categorize_unsolved(meta, info)
            if meta["failure_category"] == "api_failure" and attempt <= max_retries:
                wait = BASE_BACKOFF * (2 ** (attempt - 1))
                _append(log_path, {"event": "api_retry", "backoff_s": wait,
                                   "ts": time.time()})
                time.sleep(wait)
                continue
            # A patch the apply engine cannot place is the single largest
            # bucket of wasted attempts; one retry carrying the *verbatim*
            # source around the failure converts a good share of them.
            if (meta["failure_category"] == "patch_apply_failed"
                    and attempt <= APPLY_RETRIES):
                feedback = _apply_feedback(instance_checkout(record), info)
                if feedback:
                    notes = (notes + [feedback])[-4:]
                    _append(log_path, {"event": "apply_retry", "attempt": attempt,
                                       "message": str(info.get("message", ""))[:300],
                                       "ts": time.time()})
                    continue
        else:
            meta["failure_category"] = None

        (path / "patch.diff").write_text(patch or "", encoding="utf-8")
        (path / "plan.md").write_text(
            f"# {record['instance_id']}\n\n## Plan\n\n{state.plan}\n\n"
            f"## Patch\n\n```diff\n{patch}\n```\n",
            encoding="utf-8",
        )
        meta["status"] = "done"
        save_checkpoint(path, meta)
        _append(log_path, {"event": "finish", "status": "done",
                           "has_patch": bool(patch), "ts": time.time()})
        return meta

    save_checkpoint(path, meta)
    return meta


def _categorize_unsolved(meta: dict, info: dict) -> str:
    """First-pass category for an instance that produced no usable patch."""
    if meta.get("failure_category") == "timeout":
        return "timeout"
    message = str(info.get("message", ""))
    if "static gate failed" in message or "STATIC" in message:
        return "syntax_error"
    if not info.get("applied") and message not in ("", "no usable patch"):
        return "patch_apply_failed"
    if meta.get("offline_calls"):
        return "api_failure"
    if meta.get("escalation"):
        if "no confident fix" in str(meta.get("escalation", "")).lower():
            return "no_confident_fix"
        return "api_failure"
    if not meta.get("model_log"):
        return "api_failure"
    return "api_failure"


# ── Driver ─────────────────────────────────────────────────────────────────
def run_bench(
    limit: int = 30,
    run_id: str = "",
    slice_mode: str = "head",
    timeout: int = DEFAULT_INSTANCE_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    limit_instances: list[str] | None = None,
    candidates: int | None = None,
    verify: bool | None = None,
    pre_filter: bool = True,
) -> Path:
    """Run (or resume) the benchmark slice. Returns the run directory."""
    from src.bench import dataset as ds
    from src.bench.checkout import ensure_all

    apply_bench_env(candidates=candidates, verify=verify)
    run_id = run_id or time.strftime("run-%Y%m%d-%H%M%S")
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if limit_instances:
        by_id = {r["instance_id"]: r for r in ds.load_records()}
        records = [by_id[i] for i in limit_instances if i in by_id]
    else:
        records = ds.load_slice(limit, slice_mode)

    if pre_filter:
        from src.bench.prefilter import filter_records

        kept, dropped = filter_records(records)
        for iid, reason in dropped:
            path = instance_dir(run_dir, iid)
            save_checkpoint(path, {
                "instance_id": iid, "status": "done",
                "failure_category": "prefiltered", "model_patch": "",
                "skip_reason": reason, "model_log": [], "patch_info": {},
            })
            print(f"  [prefilter] {iid}: {reason}")
        records = kept

    ds.write_slice(run_id, records)
    print(f"[bench] run={run_id} slice={len(records)} instances ({slice_mode}) "
          f"candidates={os.environ.get('ISHA_CANDIDATES', '1')} "
          f"verify={os.environ.get('ISHA_VERIFY', '1')}")

    print("[bench] preparing checkouts ...")
    ok, failures = ensure_all(records)
    print(f"[bench] checkouts ready: {ok}/{len(records)} (failures: {len(failures)})")
    # An instance whose tree could not be prepared would only burn its full
    # timeout inside the graph — skip it explicitly and record why.
    failed_checkouts = {str(f).split(":", 1)[0].strip() for f in failures}

    for idx, record in enumerate(records, start=1):
        path = instance_dir(run_dir, record["instance_id"])
        done = load_checkpoint(path)
        if done and done.get("status") == "done":
            print(f"  [{idx}/{len(records)}] {record['instance_id']} — skipped (checkpoint)")
            continue
        if record["instance_id"] in failed_checkouts:
            save_checkpoint(path, {
                "instance_id": record["instance_id"], "status": "done",
                "failure_category": "checkout_failed", "model_patch": "",
                "model_log": [], "patch_info": {},
            })
            print(f"  [{idx}/{len(records)}] {record['instance_id']} — skipped (checkout failed)")
            continue
        print(f"  [{idx}/{len(records)}] {record['instance_id']} — solving ...", flush=True)
        meta = run_instance(record, path, timeout=timeout, max_retries=max_retries,
                            thread_id=f"{run_id}-{idx}")
        patch = (path / "patch.diff").read_text(encoding="utf-8") if (path / "patch.diff").is_file() else ""
        print(
            f"      -> {'patch' if patch.strip() else 'NO PATCH'}"
            f"{' (' + meta['failure_category'] + ')' if meta.get('failure_category') else ''}"
            f" in {meta.get('elapsed_s', 0)}s",
            flush=True,
        )

    write_predictions(run_dir, records)
    return run_dir


def write_predictions(run_dir: Path, records: list[dict] | None = None) -> Path:
    """Build the official harness predictions file from the run's checkpoints."""
    preds = []
    for meta_path in sorted(run_dir.glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") != "done":
            continue
        preds.append({
            "instance_id": meta["instance_id"],
            "model_patch": meta.get("model_patch", ""),
            "model_name_or_path": "isha",
        })
    out = run_dir / "predictions.json"
    out.write_text(json.dumps(preds, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="ISHA resumable SWE-bench runner")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--run-id", type=str, default="")
    parser.add_argument("--slice", choices=["head", "stratified", "ids", "dev", "final", "train"], default="head")
    parser.add_argument("--timeout", type=int, default=DEFAULT_INSTANCE_TIMEOUT)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--instances", nargs="*", default=None)
    parser.add_argument("--candidates", type=int, default=None,
                        help="N candidates per issue (Phase 4); default 1")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip repro verification inside the harness image")
    parser.add_argument("--no-prefilter", action="store_true",
                        help="run records the pre-filter would drop")
    args = parser.parse_args()

    run_dir = run_bench(
        limit=args.limit,
        run_id=args.run_id,
        slice_mode=args.slice,
        timeout=args.timeout,
        max_retries=args.max_retries,
        limit_instances=args.instances,
        candidates=args.candidates,
        verify=False if args.no_verify else None,
        pre_filter=not args.no_prefilter,
    )
    print(f"[bench] wrote {run_dir / 'predictions.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
