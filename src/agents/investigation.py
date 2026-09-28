"""
ISHA Investigation Node — Pre-planning active exploration.

Before committing to a fix plan, the agent explores:
1. Runs existing repo test suite to establish baseline status (what's failing right now).
2. Greps the codebase for error terms, exception names, and symbol references.
3. Inspects full suspect files rather than only vector search snippets.
4. Synthesizes a structured investigation report for the planner and decomposer.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from src.agents.state import AgentState, coerce_state
from src.ingestion.parser import SKIP_DIRS
from src.tools.dependency_graph import DependencyGraph
from src.tools.sandbox import make_sandbox, run_tests


def run_baseline_tests(workdir: str) -> str:
    """Run pytest on the clean repository before any changes are made.

    The full ``short test summary info`` block is preserved: the collateral
    regression check in ``sandbox_node`` parses ``FAILED <testid>`` lines out
    of this report, so truncating them would make pre-existing failures look
    like regressions introduced by the patch.
    """
    if not workdir or not Path(workdir).exists():
        return "Baseline tests skipped: workspace not available."
    try:
        output = run_tests(workdir, test_file=None)
        if not output:
            return "Baseline tests executed: no tests collected or empty output."
        text = output.strip()

        # Prefer the short-summary block (every FAILED/ERROR id) + final tally.
        marker = "short test summary info"
        idx = text.find(marker)
        if idx != -1:
            summary = text[idx:]
            return _cap_summary(summary)

        # No summary block (e.g. all passed) — keep the tail.
        lines = text.splitlines()
        return "\n".join(lines[-5:])
    except Exception as exc:
        return f"Baseline test run failed: {exc}"


def _cap_summary(summary: str, max_lines: int = 400) -> str:
    """Bound a very long failure list while keeping its head and the tally."""
    lines = summary.splitlines()
    if len(lines) <= max_lines:
        return summary
    tally = lines[-1]
    kept = lines[: max_lines - 2]
    dropped = len(lines) - len(kept) - 1
    return "\n".join(kept + [f"... [{dropped} more summary lines omitted]", tally])


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
    meta: dict | None = None,
) -> str:
    """Perform the full diagnostic investigation and synthesize findings.

    When `meta` is given, the blast-radius analysis is also written into it
    (`meta["blast_radius"]`) so the graph can apply fan-out caution later.
    """
    target_dir = worktree or repo_path
    report_sections = ["## 🔍 Pre-Planning Investigation Report"]

    # 1. Baseline tests
    if os.getenv("ISHA_BENCH_MODE", "0") == "1":
        baseline_output = (
            "Baseline tests skipped: SWE-bench mode (the host has no environment "
            "for this instance; the official harness runs the real suites)."
        )
    else:
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

    # 3b. Ranked localization (Phase 2): the issue's stack traces, paths,
    #     symbols and snippets fused with BM25 + embeddings + the repo map.
    #     Its ordering drives which files get deep-inspected below.
    ordered_suspects: List[str] = []
    try:
        from src.tools.localizer import find_test_files, localize

        ranked = localize(issue_text, target_dir, top_k=6)
        for cand in ranked:
            if cand.file not in ordered_suspects:
                ordered_suspects.append(cand.file)
        if ranked:
            lines = []
            for rank, cand in enumerate(ranked, start=1):
                span = f" lines {cand.line_start}-{cand.line_end}" if cand.line_start else ""
                sym = f" :: {cand.symbol}" if cand.symbol else ""
                lines.append(
                    f"{rank}. `{cand.file}`{sym}{span} — score {cand.score:.2f} "
                    f"({cand.reason}; signals {cand.scores})"
                )
            report_sections.append(
                "### 2b. Hierarchical Localization\n" + "\n".join(lines)
            )
            tests = find_test_files(target_dir, ordered_suspects[:3], top_k=3)
            if tests:
                report_sections.append(
                    "### 2c. Relevant Existing Tests\n"
                    + "\n".join(f"- `{p}` — {why}" for p, why in tests)
                )
            meta_ = meta if meta is not None else {}
            meta_["localization"] = [c.as_dict() for c in ranked]
    except Exception:
        pass

    # 4. Deep inspect suspect files, best-ranked first
    for path in ordered_suspects:
        suspect_files.discard(path)
    ordered_suspects.extend(sorted(suspect_files))
    inspected = load_suspect_files(target_dir, ordered_suspects)
    if inspected:
        inspect_lines = ["### 3. Full-File Deep Inspection"]
        for fpath, code in inspected.items():
            inspect_lines.append(f"#### File: `{fpath}`\n```python\n{code}\n```")
        report_sections.append("\n".join(inspect_lines))

    # 5. Blast radius of the suspected symbols — how much breaks if we're wrong.
    if meta is not None:
        try:
            tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", issue_text))
            entry_points = [sym.name for sym in dep_graph.definitions if sym.name in tokens][:10]
            if not entry_points:
                entry_points = [t for t in tokens if len(t) > 3][:5]
            impact = dep_graph.analyze_impact(entry_points)
            meta["blast_radius"] = {
                "score": impact.blast_radius_score,
                "callers": len(impact.upstream_callers),
                "files": len(impact.affected_files),
                "symbols": impact.directly_impacted_symbols[:6],
                "tests": len(impact.impacted_test_files),
            }
            if impact.directly_impacted_symbols:
                report_sections.append(
                    "### 4. Blast Radius\n" + dep_graph.render_impact_report(impact)
                )
        except Exception:
            meta.setdefault("blast_radius", {})

    return "\n\n".join(report_sections)


def investigation_node(state: AgentState) -> AgentState:
    """LangGraph node: actively explore repo state before planning fix."""
    state = coerce_state(state)
    meta: dict = {}
    try:
        report = investigate_repository(
            repo_path=state.repo_path,
            issue_text=state.issue_text,
            worktree=state.worktree,
            meta=meta,
        )
        state.investigation_report = report
        if meta.get("blast_radius"):
            state.blast_radius = meta["blast_radius"]
        if meta.get("localization"):
            state.localization = meta["localization"]
        # Append report to repo_context so planner gets full advantage of it
        # (bounded — every prompt budgets its own context downstream too).
        prefix = report
        if len(prefix) > 18000:
            prefix = prefix[:18000] + "\n...[investigation report capped]"
        state.repo_context = f"{prefix}\n\n{state.repo_context}"
    except Exception as exc:
        state.investigation_report = f"[INVESTIGATION ERROR] {exc}"
    return state
