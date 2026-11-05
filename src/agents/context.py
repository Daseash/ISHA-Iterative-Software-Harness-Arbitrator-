"""
ISHA Repo Context — Assembles the planner's view of the target repo.

Combines the compact tree-sitter AST map, dependency graph impact analysis,
full file contents of impacted files and their callers, related test files,
and RAG retrieval hits so the planner sees structure first, then the most
relevant source in full for accurate reasoning.
"""

import os
from pathlib import Path

from src.ingestion.parser import RepoParser
from src.rag.indexer import QdrantIndexer
from src.rag.retriever import CodeRetriever
from src.tools.ast_mapper import ASTMapper
from src.tools.dependency_graph import DependencyGraph

# Total assembled context handed to the graph.  Downstream prompts clip this
# further per role (see src/agents/nodes.py budgets), so the cap here only
# bounds the worst case.  Raise via ISHA_MAX_CONTEXT_CHARS when running on a
# quota that tolerates larger prompts.
MAX_CONTEXT_CHARS = int(os.getenv("ISHA_MAX_CONTEXT_CHARS", "40000"))
MAX_FILE_LINES = int(os.getenv("ISHA_MAX_FILE_LINES", "400"))


def _read_file(repo_path: str, rel: str, max_lines: int = MAX_FILE_LINES) -> str:
    """Read full file content with line numbers for reference."""
    path = Path(repo_path) / rel
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        preview = lines[:max_lines]
        content = "\n".join(f"{i:4d} | {line}" for i, line in enumerate(preview, 1))
        if len(lines) > max_lines:
            content += f"\n... [+{len(lines) - max_lines} more lines]"
        return content
    except Exception:
        return ""


def build_repo_context(issue_text: str, repo_path: str, top_k: int = 4) -> str:
    """Return AST MAP + IMPACT + FULL FILES + TEST FILES + SNIPPETS for the planner."""
    repo_map = ASTMapper().build_map(repo_path)
    chunks = RepoParser().parse(repo_path)

    # Dependency graph & impact analysis
    dep_graph = DependencyGraph(repo_path)
    import re
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", issue_text))
    # Filter candidates against known symbols and files in dep_graph
    entry_points = [
        sym.name for sym in dep_graph.definitions if sym.name in tokens
    ]
    for f in dep_graph.files:
        stem = f.split("/")[-1].replace(".py", "")
        if stem in tokens:
            entry_points.append(f)
    if not entry_points:
        entry_points = [t for t in tokens if len(t) > 3][:5]

    impact = dep_graph.analyze_impact(entry_points)
    impact_report = dep_graph.render_impact_report(impact)

    # ── Full file contents of impacted files + caller files ────────────────
    files_to_read = set()
    for f in impact.affected_files[:5]:
        if not f.lower().startswith("test"):
            files_to_read.add(f)
    # Files that call impacted symbols — essential for multi-file patches
    for caller in impact.upstream_callers[:8]:
        if "::" in caller:
            caller_file = caller.split("::")[0]
            files_to_read.add(caller_file)

    full_contents = []
    for rel in sorted(files_to_read)[:6]:
        content = _read_file(repo_path, rel)
        if content:
            full_contents.append(f"#### {rel}\n```python\n{content}\n```")

    full_files_section = ""
    if full_contents:
        full_files_section = (
            "FULL FILE CONTENTS (impacted files + callers):\n"
            + "\n\n".join(full_contents)
        )

    # ── Related test file summaries ────────────────────────────────────────
    test_section = ""
    test_contents = []
    for tf in impact.impacted_test_files[:3]:
        content = _read_file(repo_path, tf, max_lines=80)
        if content:
            test_contents.append(f"#### {tf}\n```python\n{content}\n```")
    if test_contents:
        test_section = (
            "RELATED TEST FILES (account for these expectations):\n"
            + "\n\n".join(test_contents)
        )

    # ── RAG snippet retrieval ──────────────────────────────────────────────
    snippets = []
    if chunks:
        indexer = QdrantIndexer()
        indexer.index(chunks)
        hits = CodeRetriever(chunks=chunks).search(issue_text, top_k=top_k)
        seen = set()
        for hit in hits:
            key = (hit.get("file_path"), hit.get("name"))
            if key in seen:
                continue
            seen.add(key)
            content = hit.get("content", "").strip()
            if content:
                snippets.append(
                    f"# {hit.get('file_path')} :: {hit.get('name')} "
                    f"(score {hit.get('score', 0):.3f})\n{content}"
                )

    # ── Assemble context (highest-value sections survive the cap first) ────
    sections: list[tuple[str, int]] = []
    if repo_map:
        sections.append(("AST MAP:\n" + repo_map, 5))
    if impact_report:
        sections.append((impact_report, 4))
    if full_files_section:
        sections.append((full_files_section, 3))
    if test_section:
        sections.append((test_section, 2))
    if snippets:
        sections.append(("RELEVANT SNIPPETS:\n" + "\n\n".join(snippets), 1))

    kept: list[str] = []
    total = 0
    for text, priority in sorted(sections, key=lambda p: p[1], reverse=True):
        if total + len(text) + 2 <= MAX_CONTEXT_CHARS:
            kept.append(text)
            total += len(text) + 2
    if kept:
        context = "\n\n".join(kept)
        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS] + "\n...[truncated]"
    return context
