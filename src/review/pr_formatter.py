"""
ISHA Senior-Developer Draft PR Formatter — Phase 7 & Stage G.

Formats the final output as a senior-developer draft PR ready for human approval:
  1. Understanding of the bug
  2. Root cause
  3. Files/functions changed and why
  4. Diff
  5. Tests run (repro + regression results)
  6. Confidence with reasons (with LOW CONFIDENCE or 'no confident fix' escalations)
  7. Risks / what to double check
  8. Which model produced this patch
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from src.agents.state import AgentState
from src.bench.gates import changed_files, diff_stats

ROOT = Path(__file__).resolve().parents[2]


def format_draft_pr(
    state: AgentState,
    candidate: dict | None = None,
    threshold: float = 0.80,
    model_name: str = "",
) -> str:
    """Format final output as a senior-developer draft PR."""
    patch = ((candidate.get("patch") if candidate else None) or state.patch or "")
    cand_model = (candidate.get("model") if candidate else model_name) or "primary"
    strategy = candidate.get("strategy") if candidate else "default"
    repro = ((candidate.get("repro") if candidate else {}) or {})
    regressions = (candidate.get("regression_count", 0) if candidate else 0) or 0
    confidence = candidate.get("combined_score", state.planner_confidence) if candidate else state.planner_confidence

    if confidence is None or confidence < 0:
        confidence = 0.5

    files = changed_files(patch) if patch else []
    added, removed = diff_stats(patch) if patch else (0, 0)

    # 1. Understanding of the bug
    issue_lines = [l.strip() for l in (state.issue_text or "").splitlines() if l.strip()]
    title = issue_lines[0] if issue_lines else "Bug Fix"
    summary = " ".join(issue_lines[:4])[:400]

    # Check for empty / no confident fix
    is_confident_fix = bool(patch.strip()) and (confidence >= threshold or (repro.get("after_ok") and regressions == 0))
    low_confidence = bool(patch.strip()) and (confidence < threshold)

    doc = []
    doc.append(f"# Draft PR: {title[:80]}")
    doc.append("")

    if not patch.strip() or state.escalation:
        doc.append("> [!WARNING]")
        doc.append("> **No confident fix produced.**")
        doc.append(f"> ISHA escalated this ticket to human engineering review. Reason: {state.escalation or 'All candidate patches failed verification or static gates.'}")
        doc.append("")

    elif low_confidence:
        doc.append("> [!CAUTION]")
        doc.append(f"> **LOW CONFIDENCE ({confidence:.1%}), review carefully.**")
        doc.append(f"> Candidate score is below the auto-approve threshold ({threshold:.0%}). Manual inspection recommended before merging.")
        doc.append("")
    else:
        doc.append("> [!NOTE]")
        doc.append(f"> **Automated Candidate Fix — Confidence {confidence:.1%} (meets threshold {threshold:.0%})**")
        doc.append("")

    # Section 1: Understanding of the bug
    doc.append("## 1. Understanding of the Bug")
    doc.append(summary)
    doc.append("")

    # Section 2: Root cause
    doc.append("## 2. Root Cause Analysis")
    plan = (state.plan or "").strip()
    root_cause_match = re.search(r"(?:Step 1:\s*(?:Root cause|What is the root cause)[—:\s]*)(.*?)(?:\n\n|\nStep 2:|$)", plan, re.DOTALL | re.IGNORECASE)
    if root_cause_match:
        doc.append(root_cause_match.group(1).strip())
    elif plan:
        doc.append(plan.splitlines()[0] if plan else "Identified via static analysis and reproduction test.")
    else:
        doc.append("Defect identified in localized components.")
    doc.append("")

    # Section 3: Files/functions changed and why
    doc.append("## 3. Files and Functions Changed")
    if files:
        for f in files:
            doc.append(f"- `{f}` (+{added}, -{removed} lines)")
    else:
        doc.append("- No files modified.")
    doc.append("")
    if state.localization:
        top_loc = state.localization[:3]
        doc.append("**Localized Context Target(s):**")
        for loc in top_loc:
            doc.append(f"- `{loc}`")
        doc.append("")

    # Section 4: Diff
    doc.append("## 4. Diff")
    if patch.strip():
        doc.append("```diff")
        doc.append(patch.strip())
        doc.append("```")
    else:
        doc.append("_No patch generated._")
    doc.append("")

    # Section 5: Tests run
    doc.append("## 5. Tests Run & Verification")
    if isinstance(repro, dict) and repro.get("available"):
        repro_status = "PASSED (red before, green after)" if (repro.get("before_ok") and repro.get("after_ok")) else "FAILED"
        doc.append(f"- **Reproduction Test**: {repro_status}")
    else:
        doc.append("- **Reproduction Test**: Evaluated via static AST/compile gates")
    doc.append(f"- **Regression Check**: {regressions} regressions detected across touched modules")
    if state.test_output:
        doc.append("<details><summary>Test Output Snippet</summary>")
        doc.append("")
        doc.append("```")
        doc.append(state.test_output[:800].strip())
        doc.append("```")
        doc.append("</details>")
    doc.append("")

    # Section 6: Confidence with reasons
    doc.append("## 6. Confidence & Calibration")
    doc.append(f"- **Calibrated Confidence**: {confidence:.2f}")
    doc.append(f"- **Auto-Approve Threshold**: {threshold:.2f}")
    if confidence >= threshold:
        doc.append("- **Decision**: Ready for automated approval or staging test pass.")
    else:
        doc.append("- **Decision**: Requires human review before application.")
    doc.append("")

    # Section 7: Risks / what to double check
    doc.append("## 7. Risks & What to Double-Check")
    doc.append("- Verify boundary conditions and edge cases in touched functions.")
    if regressions > 0:
        doc.append(f"- ⚠️ Pay special attention to {regressions} test suite changes.")
    doc.append("- Ensure backward compatibility with existing external callers.")
    doc.append("")

    # Section 8: Which model produced this patch
    doc.append("## 8. Attribution")
    doc.append(f"- **Model**: `{cand_model}`")
    doc.append(f"- **Strategy**: `{strategy}`")
    if candidate and candidate.get("substituted"):
        doc.append(f"- **Substitution**: Substituted from requested model `{candidate.get('requested_model')}` due to provider limits.")
    doc.append(f"- **Generated At**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    doc.append("")

    return "\n".join(doc)


def save_run_history(
    state: AgentState,
    report_text: str,
    candidate: dict | None = None,
    run_dir_root: Path | None = None,
) -> Path:
    """Save execution history to runs/<timestamp>/."""
    root = run_dir_root or (ROOT / "runs")
    ts = time.strftime("%Y%m%d_%H%M%S")
    slug = (state.instance_id or "run").replace("/", "__")[:40]
    dest = root / f"{ts}_{slug}"
    dest.mkdir(parents=True, exist_ok=True)

    (dest / "plan.md").write_text(state.plan or "# Plan\n(no plan)", encoding="utf-8")
    (dest / "patch.diff").write_text(state.patch or "", encoding="utf-8")
    (dest / "report.md").write_text(report_text, encoding="utf-8")

    from src.config import get_model_log
    logs = get_model_log()
    with (dest / "logs.jsonl").open("w", encoding="utf-8") as fh:
        for entry in logs:
            fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")

    return dest
