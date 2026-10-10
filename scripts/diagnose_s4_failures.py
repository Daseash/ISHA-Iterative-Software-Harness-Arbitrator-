"""
Diagnostic tool to inspect SWE-bench test failure logs for Session 4
and summarize failed assertions, tracebacks, and modified files.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S4_LOGS = ROOT / "results" / "lite300-s4" / "logs" / "run_evaluation" / "lite300-s4" / "isha"
REPORT_PATH = ROOT / "results" / "lite300-s4" / "harness_report.json"

def main():
    if not REPORT_PATH.is_file():
        print("Harness report not found")
        return
    
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    unresolved = report.get("unresolved_ids", [])
    print(f"Total unresolved instances in Session 4: {len(unresolved)}\n")

    summary = []
    for inst in unresolved:
        inst_dir = S4_LOGS / inst
        if not inst_dir.is_dir():
            print(f"[{inst}] Directory not found: {inst_dir}")
            continue

        report_file = inst_dir / "report.json"
        test_out_file = inst_dir / "test_output.txt"
        patch_file = inst_dir / "patch.diff"

        patch_str = patch_file.read_text(encoding="utf-8", errors="replace") if patch_file.is_file() else ""
        patch_files = re.findall(r"diff --git a/(\S+)", patch_str)

        f2p_fail = []
        p2p_fail = []
        if report_file.is_file():
            rep = json.loads(report_file.read_text(encoding="utf-8")).get(inst, {})
            f2p_fail = rep.get("tests_status", {}).get("FAIL_TO_PASS", {}).get("failure", [])
            p2p_fail = rep.get("tests_status", {}).get("PASS_TO_PASS", {}).get("failure", [])

        # Extract last traceback from test_output.txt
        tb = ""
        if test_out_file.is_file():
            content = test_out_file.read_text(encoding="utf-8", errors="replace")
            # find FAIL: or ERROR: blocks
            matches = list(re.finditer(r"(FAIL|ERROR): (.*?)\n-{10,}\n(.*?)(?=\n={10,}|\n-{10,}|\nRan \d+ tests|\Z)", content, re.DOTALL))
            if matches:
                last_few = [m.group(0).strip() for m in matches[-3:]]
                tb = "\n\n".join(last_few)
            else:
                # search for AssertionError or Exception in last 100 lines
                lines = content.splitlines()[-100:]
                tb = "\n".join(lines[-40:])

        summary.append({
            "instance_id": inst,
            "patch_files": patch_files,
            "f2p_fail": f2p_fail,
            "p2p_fail": p2p_fail,
            "traceback_summary": tb[:800],
        })

    for item in summary:
        print(f"==================================================")
        print(f"Instance: {item['instance_id']}")
        print(f"Modified Files: {item['patch_files']}")
        print(f"FAIL_TO_PASS Failures: {item['f2p_fail']}")
        if item['p2p_fail']:
            print(f"PASS_TO_PASS Regressions: {item['p2p_fail']}")
        print(f"--- Traceback Snippet ---")
        print(item['traceback_summary'])
        print("\n")

if __name__ == "__main__":
    main()
