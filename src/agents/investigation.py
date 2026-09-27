"""
ISHA Investigation Node — Pre-planning active exploration.

Before committing to a fix plan, the agent explores:
1. Runs existing repo test suite to establish baseline status (what's failing right now).
2. Greps the codebase for error terms, exception names, and symbol references.
3. Inspects full suspect files rather than only vector search snippets.
4. Synthesizes a structured investigation report for the planner and decomposer.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from src.agents.state import AgentState, coerce_state
from src.ingestion.parser import SKIP_DIRS
from src.tools.dependency_graph import DependencyGraph
from src.tools.sandbox import make_sandbox, run_tests


def run_baseline_tests(workdir: str) -> str:
    """Run pytest on the clean repository before any changes are made."""
    if not workdir or not Path(workdir).exists():
        return "Baseline tests skipped: workspace not available."
    try:
        output = run_tests(workdir, test_file=None)
        if not output:
            return "Baseline tests executed: no tests collected or empty output."
        # Truncate if excessively long
        lines = output.strip().splitlines()
        summary = lines[-5:] if len(lines) > 5 else lines
        return "\n".join(summary)
    except Exception as exc:
        return f"Baseline test run failed: {exc}"


def grep_codebase(
    repo_path: str,
    patterns: List[str],
    max_matches: int = 15,
) -> List[Dict[str, str]]:
    """Search for relevant terms, function names, or exceptions in the codebase."""
    root = Path(repo_path)
    if not root.exists():
        return []

    matches = []
    clean_patterns = [p for p in patterns if len(p) >= 3 and not p.isspace()]
    if not clean_patterns:
        return []

    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            rel = str(path.relative_to(root)).replace("\\", "/")
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        for idx, line in enumerate(lines, start=1):
            for pat in clean_patterns:
                if pat.lower() in line.lower():
                    matches.append({
                        "file": rel,
                        "line": idx,
                        "pattern": pat,
                        "snippet": line.strip()[:140],
                    })
                    if len(matches) >= max_matches:
                        return matches
    return matches


def load_suspect_files(repo_path: str, file_rel_paths: List[str], max_lines: int = 300) -> Dict[str, str]:
    """Read full contents of high-priority suspect files for deep inspection."""
    root = Path(repo_path)
    results = {}
    for rel in file_rel_paths[:3]:  # Top 3 files
        full_path = root / rel
        if full_path.exists() and full_path.is_file():
            try:
                lines = full_path.read_text(encoding="utf-8", errors="replace").splitlines()
                preview = lines[:max_lines]
                content = "\n".join(f"{i:4d} | {line}" for i, line in enumerate(preview, start=1))
                if len(lines) > max_lines:
                    content += f"\n... [+{len(lines) - max_lines} more lines]"
                results[rel] = content
            except Exception:
                pass
    return results


def investigate_repository(
    repo_path: str,
    issue_text: str,
    worktree: str = "",
) -> str:
    """Perform the full diagnostic investigation and synthesize findings."""
    target_dir = worktree or repo_path
    report_sections = ["## 🔍 Pre-Planning Investigation Report"]

    # 1. Baseline tests
    baseline_output = run_baseline_tests(target_dir)
    report_sections.append(f"### 1. Baseline Test Execution\n```\n{baseline_output}\n```")

    # 2. Extract keywords for targeted grep
    raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", issue_text)
    keywords = list(dict.fromkeys(t for t in raw_tokens if len(t) > 3))[:8]
    grep_hits = grep_codebase(target_dir, keywords)

    grep_lines = []
    suspect_files = set()
    if grep_hits:
        for hit in grep_hits:
            grep_lines.append(f"- `{hit['file']}:{hit['line']}` ({hit['pattern']}): {hit['snippet']}")
            suspect_files.add(hit["file"])
        report_sections.append("### 2. Codebase Grep Matches\n" + "\n".join(grep_lines))
    else:
        report_sections.append("### 2. Codebase Grep Matches\nNo direct keyword matches found.")

    # 3. Add files identified by Dependency Graph
    dep_graph = DependencyGraph(target_dir)
    for sym in dep_graph.definitions:
        if sym.name in keywords:
            suspect_files.add(sym.file_path)

    # 4. Deep inspect suspect files
    inspected = load_suspect_files(target_dir, list(suspect_files))
    if inspected:
        inspect_lines = ["### 3. Full-File Deep Inspection"]
        for fpath, code in inspected.items():
            inspect_lines.append(f"#### File: `{fpath}`\n```python\n{code}\n```")
        report_sections.append("\n".join(inspect_lines))

    return "\n\n".join(report_sections)


def investigation_node(state: AgentState) -> AgentState:
    """LangGraph node: actively explore repo state before planning fix."""
    state = coerce_state(state)
    try:
        report = investigate_repository(
            repo_path=state.repo_path,
            issue_text=state.issue_text,
            worktree=state.worktree,
        )
        state.investigation_report = report
        # Append report to repo_context so planner gets full advantage of it
        state.repo_context = f"{report}\n\n{state.repo_context}"
    except Exception as exc:
        state.investigation_report = f"[INVESTIGATION ERROR] {exc}"
    return state
