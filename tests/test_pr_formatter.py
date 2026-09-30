"""Tests for the Senior-Developer Draft PR formatter and run history."""

from pathlib import Path
from src.agents.state import AgentState
from src.review.pr_formatter import format_draft_pr, save_run_history


def test_format_draft_pr_sections():
    state = AgentState(
        issue_text="IndexError in array slicer when step is negative\nReported in slice_util.py",
        plan="Step 1: Root cause — negative step arithmetic underflows boundary check\nStep 2: Adjust slice bounds",
        patch="--- a/slice_util.py\n+++ b/slice_util.py\n@@ -10,1 +10,1 @@\n-    return val\n+    return val - 1\n",
        planner_confidence=0.85,
    )
    doc = format_draft_pr(state, candidate={"combined_score": 0.88, "strategy": "minimal_diff", "model": "qwen3.8-27b"})
    
    assert "# Draft PR: IndexError in array slicer" in doc
    assert "## 1. Understanding of the Bug" in doc
    assert "## 2. Root Cause Analysis" in doc
    assert "## 3. Files and Functions Changed" in doc
    assert "## 4. Diff" in doc
    assert "```diff" in doc
    assert "## 5. Tests Run & Verification" in doc
    assert "## 6. Confidence & Calibration" in doc
    assert "## 7. Risks & What to Double-Check" in doc
    assert "## 8. Attribution" in doc
    assert "`qwen3.8-27b`" in doc


def test_save_run_history(tmp_path):
    state = AgentState(
        issue_text="Fix bug",
        plan="Plan details",
        patch="diff text",
        instance_id="django__django-12345",
    )
    dest = save_run_history(state, "# Report", run_dir_root=tmp_path)
    assert dest.is_dir()
    assert (dest / "plan.md").is_file()
    assert (dest / "patch.diff").is_file()
    assert (dest / "report.md").is_file()
    assert (dest / "logs.jsonl").is_file()
    assert (dest / "plan.md").read_text(encoding="utf-8") == "Plan details"
