"""
ISHA CLI — Phase 7 of the SWE-bench upgrade.

Subcommands behind the existing ``isha`` entry point:

    isha fix     run the agentic loop on one issue (the original CLI)
    isha bench   run / resume a SWE-bench slice, then evaluate it
    isha report  render a run's results table (and append to progress.md)
    isha doctor  environment self-check: git, docker, images, models, dataset
    isha ui      launch the Streamlit dashboard

``isha`` with no subcommand keeps the historical behaviour, so nothing
existing breaks.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "results"


def _ok(label: str, detail: str = "") -> None:
    print(f"  [ok]   {label:<26} {detail}")


def _bad(label: str, detail: str = "") -> None:
    print(f"  [FAIL] {label:<26} {detail}")


def _warn(label: str, detail: str = "") -> None:
    print(f"  [warn] {label:<26} {detail}")


def _which(name: str) -> str | None:
    return shutil.which(name)


def _run(cmd: list[str], timeout: int = 45) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
        )
        return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"


# ── doctor ─────────────────────────────────────────────────────────────────
def cmd_doctor(args: argparse.Namespace) -> int:
    print("\nISHA doctor\n" + "=" * 60)
    failures = 0

    print("\nToolchain")
    rc, out = _run([sys.executable, "--version"])
    _ok("python", out) if rc == 0 else _bad("python", out)
    rc, out = _run(["git", "--version"])
    if rc == 0:
        _ok("git", out)
    else:
        _bad("git", "not on PATH — SWE-bench checkouts need it")
        failures += 1

    print("\nAPI Keys")
    groq_key = os.getenv("GROQ_API_KEY", "")
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    if groq_key:
        _ok("GROQ_API_KEY", f"{groq_key[:6]}...{groq_key[-4:]}")
    else:
        _warn("GROQ_API_KEY", "missing — Groq models will be skipped")
    if google_key:
        _ok("GOOGLE_API_KEY", f"{google_key[:6]}...{google_key[-4:]}")
    else:
        _warn("GOOGLE_API_KEY", "missing — Gemini models will be skipped")
    if not groq_key and not google_key:
        _bad("API keys", "no keys configured — running in offline-only mode")
        failures += 1

    print("\nDisk & Storage")
    try:
        total, used, free = shutil.disk_usage(ROOT)
        free_gb = free / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        if free_gb < 15:
            _warn("disk space", f"{free_gb:.1f} GB free of {total_gb:.1f} GB — Docker images require ~20 GB")
        else:
            _ok("disk space", f"{free_gb:.1f} GB free of {total_gb:.1f} GB")
    except Exception as exc:
        _bad("disk space", str(exc))

    print("\nDocker & WSL Environment")
    if not _which("docker"):
        _bad("docker", "binary not found — no harness evaluation possible")
        failures += 1
    else:
        rc, out = _run(["docker", "version", "--format", "{{.Server.Version}}"])
        if rc == 0:
            _ok("docker daemon", out)
        else:
            _bad("docker daemon", out.splitlines()[0] if out else "not running")
            failures += 1

    if _which("wsl"):
        rc, out = _run(["wsl", "-l", "-v"])
        if rc == 0:
            distros = [line.strip() for line in out.splitlines() if line.strip() and not line.startswith("NAME") and not line.startswith("N A M E")]
            _ok("WSL2 subsystem", f"{len(distros)} distribution(s) registered")
        else:
            _warn("WSL2 subsystem", "wsl command failed")
    else:
        _warn("WSL2 subsystem", "wsl binary not found on host PATH")

    print("\nVector DB (Qdrant)")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    try:
        import urllib.request
        req = urllib.request.Request(f"{qdrant_url.rstrip('/')}/healthz", headers={"User-Agent": "ISHA-doctor"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                _ok("qdrant", f"reachable at {qdrant_url}")
            else:
                _warn("qdrant", f"status {resp.status} at {qdrant_url}")
    except Exception:
        _warn("qdrant", f"unreachable at {qdrant_url} — local in-memory fallback active")

    print("\nPython packages")
    for mod, label in [
        ("langgraph", "langgraph"),
        ("litellm", "litellm"),
        ("laya", "laya"),
        ("swebench", "swebench"),
        ("datasets", "datasets"),
    ]:
        try:
            __import__(mod)
            _ok(label)
        except Exception as exc:
            _bad(label, f"{type(exc).__name__}: {exc}")
            failures += 1

    print("\nModel chain")
    try:
        from src.config import CODER_CHAIN, OFFLINE_MODE, PLANNER_CHAIN, _short_name

        if OFFLINE_MODE:
            _warn("models", "OFFLINE_MODE set — deterministic brain, no API calls")
        else:
            _ok("planner chain", " -> ".join(_short_name(m) for m in PLANNER_CHAIN))
            _ok("coder chain", " -> ".join(_short_name(m) for m in CODER_CHAIN))
    except Exception as exc:
        _bad("models", f"{type(exc).__name__}: {exc}")
        failures += 1

    print("\nModel reachability (one tiny live call per provider role)")
    if os.getenv("ISHA_SKIP_LIVE_CHECK", "0") == "1":
        _warn("live check", "skipped (ISHA_SKIP_LIVE_CHECK=1)")
    else:
        try:
            from src.config import call_planner, get_model_log, reset_provider_state

            reset_provider_state()
            reply = call_planner("Reply with exactly: OK")
            log = get_model_log()
            primary = log[-1] if log else {}
            if (reply or "").strip():
                _ok("planner call", f"{reply.strip()[:40]} [{primary.get('model', '?')}]")
            else:
                _bad("planner call", "empty reply")
                failures += 1
        except Exception as exc:
            _bad("planner call", f"{type(exc).__name__}: {exc}")
            failures += 1

    print("\nBenchmark data")
    try:
        from src.bench.dataset import load_records

        records = load_records()
        _ok("SWE-bench Lite", f"{len(records)} instances cached")
    except Exception as exc:
        _bad("SWE-bench Lite", f"{type(exc).__name__}: {exc}")
        failures += 1

    mirrors = ROOT / "swebench_checkouts" / ".mirrors"
    if mirrors.is_dir():
        repos = [p for p in mirrors.iterdir() if p.is_dir()]
        _ok("checkout mirrors", f"{len(repos)} repos")
    else:
        _warn("checkout mirrors", "none yet (created on first bench run)")

    try:
        from src.review import calibration

        model = calibration.load()
        labels = calibration.load_labels()
        if model:
            n_lbl = model.get('n_labels') or model.get('n_total', '?')
            ece_val = model.get('ece_scaled') or model.get('val_ece_scaled', '?')
            _ok("laya combiner",
                f"fitted on {n_lbl} labels, "
                f"ece={ece_val} thr={model.get('threshold')}")
        elif labels:
            _warn("laya combiner",
                  f"{len(labels)} labels but not fitted — run `isha bench --fit-laya`")
        else:
            _warn("laya combiner", "no labels yet — hand-weighted fallback in use")
    except Exception as exc:
        _bad("laya combiner", str(exc))

    print("\n" + "=" * 60)
    print(f"{'ALL CLEAR' if failures == 0 else str(failures) + ' PROBLEM(S) FOUND'}\n")
    return 0 if failures == 0 else 1


# ── bench ──────────────────────────────────────────────────────────────────
def cmd_bench(args: argparse.Namespace) -> int:
    from src.bench.runner import run_bench

    if args.doctor_first:
        if cmd_doctor(argparse.Namespace()) != 0:
            print("[bench] doctor found problems — aborting before spending budget")
            return 1

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

    if args.fit_laya:
        from src.review import calibration

        model = calibration.fit()
        keys = ("fitted", "n_labels", "ece_raw", "ece_scaled", "brier_raw",
                "brier_scaled", "threshold")
        print("[bench] laya combiner: " + json.dumps({k: model.get(k) for k in keys},
                                                     default=str))

    rc = 0
    if args.eval:
        from src.bench.harness_eval import evaluate, is_docker_ready

        ready, message = is_docker_ready()
        print(f"[bench] {message}")
        if not ready:
            print("[bench] evaluation skipped — start Docker Desktop and re-run "
                  "`isha report --run-id <id>` once it is up")
            rc = 1
        else:
            try:
                report = evaluate(run_dir, max_workers=args.eval_workers,
                                  keep_images=args.keep_images)
            except Exception as exc:
                print(f"[bench] evaluation failed: {type(exc).__name__}: {exc}")
                rc = 1
            else:
                # The harness only submits instances that produced a patch; the
                # denominator has to stay the whole slice or the rate flatters
                # the model. Empty patches count as unresolved, as in SWE-bench.
                submitted = report.get("total_instances", 0)
                expected = 0
                try:
                    expected = len(json.loads(
                        (run_dir / "predictions.json").read_text(encoding="utf-8")
                    ))
                except Exception:
                    expected = submitted
                resolved = report.get("resolved_instances", 0)
                rate = (resolved / expected) if expected else 0.0
                print(f"[bench] resolved: {resolved}/{expected} ({rate:.1%})"
                      f" — {submitted} submitted to the harness")
                print(f"[bench] report: {run_dir / 'harness_report.json'}")

    if args.report or args.eval:
        from src.bench.report import render_table, summarize

        try:
            payload = summarize(args.run_id or run_dir.name)
            print()
            print(render_table(payload))
        except Exception as exc:
            print(f"[bench] report skipped: {type(exc).__name__}: {exc}")
            rc = rc or 1

    return rc


# ── report ─────────────────────────────────────────────────────────────────
def cmd_report(args: argparse.Namespace) -> int:
    from src.bench.report import append_progress, compare, load_run, render_table

    if not (RESULTS / args.run_id).is_dir():
        print(f"report: no such run '{args.run_id}' (looked in {RESULTS})")
        return 1
    payload = load_run(args.run_id)
    print(render_table(payload))

    if args.append:
        append_progress(
            f"{payload['run_id']} — {time.strftime('%Y-%m-%d %H:%M')}",
            render_table(payload),
        )
        print("[report] appended to results/progress.md")

    if args.compare:
        if (RESULTS / args.compare).is_dir():
            print("\n" + compare(load_run(args.compare), payload))
        else:
            print(f"\n[report] compare run not found: {args.compare}")
    return 0


# ── ui ─────────────────────────────────────────────────────────────────────
def cmd_ui(args: argparse.Namespace) -> int:
    app = ROOT / "src" / "dashboard" / "app.py"
    if not app.is_file():
        print(f"ui: dashboard not found at {app}")
        return 1
    cmd = [_which("streamlit") or sys.executable]
    if cmd[0] == sys.executable:
        cmd += ["-m", "streamlit"]
    cmd += ["run", str(app), "--server.port", str(args.port)]
    print(f"[ui] {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(ROOT))


# ── fix ────────────────────────────────────────────────────────────────────
def cmd_fix(args: argparse.Namespace) -> int:
    from src.main import main as fix_main

    forwarded = []
    if args.issue:
        forwarded += ["--issue", args.issue]
    if args.repo:
        forwarded += ["--repo", args.repo]
    if args.apply:
        forwarded += ["--apply"]
    if args.multi:
        forwarded += ["--multi"]
    forwarded += ["--thread-id", args.thread_id]
    argv = sys.argv
    try:
        sys.argv = [argv[0]] + forwarded
        return fix_main()
    finally:
        sys.argv = argv


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="isha", description="ISHA CLI")
    sub = parser.add_subparsers(dest="command")

    fix = sub.add_parser("fix", help="solve one issue")
    fix.add_argument("--issue", default=None)
    fix.add_argument("--repo", default=None)
    fix.add_argument("--apply", action="store_true")
    fix.add_argument("--multi", action="store_true")
    fix.add_argument("--thread-id", default="1")
    fix.set_defaults(func=cmd_fix)

    bench = sub.add_parser("bench", help="run a SWE-bench slice")
    bench.add_argument("--limit", type=int, default=30)
    bench.add_argument("--run-id", default="")
    bench.add_argument("--slice", choices=["head", "stratified", "ids", "dev", "final", "train"], default="head")
    bench.add_argument("--timeout", type=int, default=900)
    bench.add_argument("--max-retries", type=int, default=2)
    bench.add_argument("--instances", nargs="*", default=None)
    bench.add_argument("--candidates", type=int, default=None,
                       help="N candidates per issue (Phase 4); default 1")
    bench.add_argument("--no-verify", action="store_true",
                       help="skip repro verification in the harness image")
    bench.add_argument("--eval", action="store_true",
                       help="run the official SWE-bench Docker harness afterwards")
    bench.add_argument("--eval-workers", type=int, default=3,
                       help="parallel containers for the official harness")
    bench.add_argument("--keep-images", action="store_true",
                       help="keep the ~4GB-per-instance eval images after grading")
    bench.add_argument("--report", action="store_true", help="render the results table")
    bench.add_argument("--fit-laya", action="store_true",
                       help="fit the LAYA combiner on the label store")
    bench.add_argument("--doctor-first", action="store_true",
                       help="abort if `isha doctor` finds a problem")
    bench.add_argument("--no-prefilter", action="store_true",
                       help="run records the pre-filter would drop")
    bench.set_defaults(func=cmd_bench)

    rep = sub.add_parser("report", help="render a run's results")
    rep.add_argument("--run-id", required=True)
    rep.add_argument("--append", action="store_true", help="append to results/progress.md")
    rep.add_argument("--compare", default=None, help="another run-id to diff against")
    rep.set_defaults(func=cmd_report)

    doctor = sub.add_parser("doctor", help="environment self-check")
    doctor.set_defaults(func=cmd_doctor)

    ui = sub.add_parser("ui", help="launch the Streamlit dashboard")
    ui.add_argument("--port", type=int, default=8501)
    ui.set_defaults(func=cmd_ui)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-"):
        # Historical no-subcommand behaviour is handled by src.main.main().
        return -1
    args = _parser().parse_args(argv)
    if not getattr(args, "func", None):
        _parser().print_help()
        return 1
    started = time.time()
    code = args.func(args)
    print(f"\n[isha {args.command}] exit={code} in {time.time() - started:.1f}s")
    return code


if __name__ == "__main__":
    raise SystemExit(max(main(), 0))
