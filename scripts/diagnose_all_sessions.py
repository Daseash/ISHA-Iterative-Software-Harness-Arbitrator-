"""
Comprehensive Ground-Truth Diagnostic Script across all SWE-bench Sessions.
Parses official report.json and test_output.txt for Sessions 1, 2, 3, and 4
to categorize failure causes, error types, and pinpoint tracebacks.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

def analyze_session(session_id: str):
    rep_file = RESULTS / session_id / "harness_report.json"
    if not rep_file.is_file():
        return None
    report = json.loads(rep_file.read_text(encoding="utf-8"))
    unresolved = report.get("unresolved_ids", [])
    
    log_base = RESULTS / session_id / "logs" / "run_evaluation" / session_id
    records = []
    
    for inst in unresolved:
        inst_dir = None
        for cand in ["ISHA-v1", "isha"]:
            d = log_base / cand / inst
            if d.is_dir():
                inst_dir = d
                break
        
        applied = False
        f2p_fail = []
        p2p_fail = []
        error_type = "Assertion/Logic"
        root_cause = ""
        
        if inst_dir:
            rf = inst_dir / "report.json"
            if rf.is_file():
                try:
                    data = json.loads(rf.read_text(encoding="utf-8")).get(inst, {})
                    applied = data.get("patch_successfully_applied", False)
                    ts = data.get("tests_status", {})
                    f2p_fail = ts.get("FAIL_TO_PASS", {}).get("failure", [])
                    p2p_fail = ts.get("PASS_TO_PASS", {}).get("failure", [])
                except Exception:
                    pass
            
            tf = inst_dir / "test_output.txt"
            if tf.is_file():
                text = tf.read_text(encoding="utf-8", errors="replace")
                # Detect error types
                if "TypeError:" in text:
                    error_type = "TypeError (Signature/Type mismatch)"
                    m = re.search(r"TypeError: ([^\n]+)", text)
                    if m: root_cause = m.group(1)[:100]
                elif "AttributeError:" in text:
                    error_type = "AttributeError (Missing symbol/attribute)"
                    m = re.search(r"AttributeError: ([^\n]+)", text)
                    if m: root_cause = m.group(1)[:100]
                elif "ValueError:" in text:
                    error_type = "ValueError (Invalid argument/format)"
                    m = re.search(r"ValueError: ([^\n]+)", text)
                    if m: root_cause = m.group(1)[:100]
                elif "AssertionError:" in text:
                    error_type = "AssertionError (Edge case/return mismatch)"
                    m = re.search(r"AssertionError: ([^\n]+)", text)
                    if m: root_cause = m.group(1)[:100]
                elif not applied:
                    error_type = "Git Apply / Syntax Error"
                    root_cause = "Patch rejected by git apply or failed compile gate"
                else:
                    error_type = "Test Failure"
                    m = re.search(r"(FAIL|ERROR): ([^\n]+)", text)
                    if m: root_cause = m.group(0)[:100]

        records.append({
            "instance_id": inst,
            "applied": applied,
            "f2p_count": len(f2p_fail),
            "p2p_count": len(p2p_fail),
            "error_type": error_type,
            "root_cause": root_cause or "Assertion check failed",
            "f2p_sample": f2p_fail[0] if f2p_fail else "N/A",
        })
    return {
        "session": session_id,
        "resolved_count": report.get("resolved_instances", 0),
        "total_submitted": report.get("submitted_instances", 0),
        "unresolved_count": len(unresolved),
        "records": records,
    }

def main():
    results = {}
    for s in ["lite300-s1", "lite300-s2", "lite300-s4"]:
        data = analyze_session(s)
        if data:
            results[s] = data
            print(f"=== {s}: {data['resolved_count']}/{data['total_submitted']} Resolved ({len(data['records'])} Unresolved) ===")
            for r in data["records"]:
                print(f"  {r['instance_id']:<26} | {r['error_type']:<35} | {r['root_cause']}")

    # Save to JSON for report integration
    out_path = ROOT / "data" / "all_sessions_failure_analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote full failure catalog to {out_path}")

if __name__ == "__main__":
    main()
