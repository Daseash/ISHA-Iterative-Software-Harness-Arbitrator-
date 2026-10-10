"""
ISHA Test-Driven Self-Correction Engine (Tier 1 & Tier 2 Implementation)

Reads SWE-bench Docker test evaluation logs (report.json and test_output.txt),
extracts exact failed test names, AssertionError/TypeError tracebacks,
generates structured high-priority validation feedback notes, and runs
the multi-candidate tournament runner with targeted failure context.

Usage:
    python scripts/self_correct_docker.py --session lite300-s4
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
FEEDBACK_DIR = ROOT / "data" / "feedback"
PYTHON = sys.executable


def extract_instance_feedback(session: str, instance_id: str) -> str | None:
    """Extract pinpoint traceback and failure notes for an instance."""
    inst_dir = RESULTS_DIR / session / "logs" / "run_evaluation" / session / "isha" / instance_id
    if not inst_dir.is_dir():
        return None

    report_path = inst_dir / "report.json"
    test_out_path = inst_dir / "test_output.txt"
    patch_path = inst_dir / "patch.diff"

    f2p_failures = []
    p2p_failures = []
    if report_path.is_file():
        try:
            rep_data = json.loads(report_path.read_text(encoding="utf-8")).get(instance_id, {})
            ts = rep_data.get("tests_status", {})
            f2p_failures = ts.get("FAIL_TO_PASS", {}).get("failure", [])
            p2p_failures = ts.get("PASS_TO_PASS", {}).get("failure", [])
        except Exception:
            pass

    tb_snippets = []
    if test_out_path.is_file():
        try:
            content = test_out_path.read_text(encoding="utf-8", errors="replace")
            # Look for FAIL: or ERROR: blocks
            matches = list(re.finditer(
                r"(FAIL|ERROR): (.*?)\n-{10,}\n(.*?)(?=\n={10,}|\n-{10,}|\nRan \d+ tests|\Z)",
                content,
                re.DOTALL
            ))
            if matches:
                for m in matches[-3:]:
                    tb_snippets.append(m.group(0).strip())
            else:
                lines = content.splitlines()[-80:]
                tb_snippets.append("\n".join(lines[-40:]))
        except Exception:
            pass

    traceback_text = "\n\n".join(tb_snippets)
    if len(traceback_text) > 3500:
        traceback_text = traceback_text[-3500:]

    patch_snippet = ""
    if patch_path.is_file():
        p_text = patch_path.read_text(encoding="utf-8", errors="replace")
        if len(p_text) > 1200:
            patch_snippet = p_text[:1200] + "\n...[truncated]"
        else:
            patch_snippet = p_text

    note = (
        "CRITICAL SWE-BENCH DOCKER TEST FAILURE FEEDBACK:\n"
        "Your previous patch applied cleanly, but the official Docker test suite failed!\n"
    )
    if f2p_failures:
        note += "FAILED REQUIREMENT TESTS (FAIL_TO_PASS):\n"
        for f in f2p_failures[:5]:
            note += f"  - {f}\n"
    if p2p_failures:
        note += f"REGRESSION WARNING: {len(p2p_failures)} previously passing tests failed!\n"
    if traceback_text:
        note += f"\nTEST TRACEBACK & ASSERTION ERRORS:\n{traceback_text}\n"
    if patch_snippet:
        note += f"\nPREVIOUS FLAWED PATCH (DO NOT REPEAT THIS EXACT DIFF):\n{patch_snippet}\n"

    note += (
        "\nACTIONABLE REPAIR INSTRUCTIONS:\n"
        "1. Check the exact AssertionError/TypeError and line numbers above.\n"
        "2. Ensure the fix is applied inside the EXACT correct class and function.\n"
        "3. Preserve all existing behaviors, types, and return values.\n"
        "4. Produce a minimal, clean unified diff that satisfies the assertion."
    )
    return note


def generate_session_feedback(session: str) -> dict[str, list[str]]:
    """Scan session harness report and build feedback map for all unresolved instances."""
    report_path = RESULTS_DIR / session / "harness_report.json"
    if not report_path.is_file():
        print(f"[self-correct] Error: {report_path} not found.")
        return {}

    report = json.loads(report_path.read_text(encoding="utf-8"))
    unresolved = report.get("unresolved_ids", [])
    print(f"[self-correct] Found {len(unresolved)} unresolved instances in {session}")

    feedback_map = {}
    for inst in unresolved:
        note = extract_instance_feedback(session, inst)
        if note:
            feedback_map[inst] = [note]
        else:
            feedback_map[inst] = [
                "CRITICAL SWE-BENCH DOCKER TEST FEEDBACK: Previous patch did not resolve the issue. "
                "Re-examine the issue statement and produce a clean root-cause fix."
            ]

    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    out_file = FEEDBACK_DIR / f"{session}-feedback.json"
    out_file.write_text(json.dumps(feedback_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[self-correct] Saved feedback notes for {len(feedback_map)} instances to {out_file}")
    return feedback_map


def run_self_correction(session: str, instances: list[str] | None = None, candidates: int = 3, workers: int = 1) -> int:
    """Run runner with the generated feedback notes."""
    feedback_map = generate_session_feedback(session)
    if not feedback_map:
        return 1

    target_instances = instances or list(feedback_map.keys())
    run_id = f"{session}-r2"
    feedback_file = FEEDBACK_DIR / f"{session}-feedback.json"

    print(f"\n[self-correct] Launching improvement run {run_id} on {len(target_instances)} instances...")
    cmd = [
        PYTHON, "-m", "src.bench.runner",
        "--run-id", run_id,
        "--instances", *target_instances,
        "--notes-file", str(feedback_file),
        "--candidates", str(candidates),
        "--workers", str(workers),
        "--timeout", "600",
        "--max-retries", "2",
    ]
    print(f"[self-correct] Command: {' '.join(cmd[:8])} ...")
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        print(f"[self-correct] Runner finished with exit code {proc.returncode}")

    # Merge improved patches into session predictions (preserving golden passing instances)
    source_dir = RESULTS_DIR / run_id
    target_dir = RESULTS_DIR / session
    if source_dir.is_dir() and target_dir.is_dir():
        print(f"\n[self-correct] Merging improved patches from {run_id} into {session}...")
        merge_cmd = [
            PYTHON, "scripts/merge_predictions.py",
            "--source", str(source_dir),
            "--target", str(target_dir),
        ]
        subprocess.run(merge_cmd, cwd=str(ROOT))

    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="ISHA Test-Driven Self-Correction")
    parser.add_argument("--session", type=str, default="lite300-s4", help="Session ID (e.g. lite300-s4)")
    parser.add_argument("--instances", nargs="*", default=None, help="Optional subset of instance IDs")
    parser.add_argument("--candidates", type=int, default=3, help="Tournament candidates (default 3)")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers (default 1)")
    parser.add_argument("--dry-run", action="store_true", help="Generate feedback without running runner")
    args = parser.parse_args()

    if args.dry_run:
        generate_session_feedback(args.session)
        return

    rc = run_self_correction(
        session=args.session,
        instances=args.instances,
        candidates=args.candidates,
        workers=args.workers,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
