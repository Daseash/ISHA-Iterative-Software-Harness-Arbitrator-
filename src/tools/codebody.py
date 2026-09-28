"""
ISHA Code Bodies — full, untruncated views of the code the Coder must change.

Phase 3 of the upgrade: instead of shipping truncated file chunks, the Coder
gets

  * the COMPLETE body of every suspect function/class (never elided),
  * the direct callers of those symbols, taken from the dependency graph's
    call graph, each shown at its call site,
  * the relevant existing tests in full,
  * the local style conventions of the file being edited (naming, docstring
    style, type-annotation style, string quoting, line width).

Everything is bounded by a character budget so a pathological repo cannot
blow up the prompt, but within a budget nothing is silently truncated —
oversized bodies are dropped with an explicit note instead of a "...".
"""

from __future__ import annotations

import re
from pathlib import Path

MAX_BODY_CHARS = 9000
MAX_TEST_CHARS = 6000
MAX_CALLER_CHARS = 4000

_DEF_RE = re.compile(r"^(\s*)(?:async\s+)?(def|class)\s+([A-Za-z_]\w*)")


def _read(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _spans(lines: list[str]) -> list[dict]:
    """Top-level and nested (def/class) spans using indentation."""
    out = []
    for i, line in enumerate(lines):
        m = _DEF_RE.match(line)
        if not m:
            continue
        indent = len(m.group(1))
        end = len(lines)
        for j in range(i + 1, len(lines)):
            other = lines[j]
            if not other.strip():
                continue
            other_indent = len(other) - len(other.lstrip())
            if other_indent <= indent:
                end = j
                break
        out.append(
            {"name": m.group(3), "kind": m.group(2), "start": i, "end": end,
             "indent": indent}
        )
    return out


def full_bodies(repo_path: str, rel_path: str, names: list[str] | None = None,
                budget: int = MAX_BODY_CHARS) -> str:
    """Complete source of the requested symbols (or the whole small file)."""
    path = Path(repo_path) / rel_path
    if not path.is_file():
        return ""
    lines = _read(path)
    if not lines:
        return ""

    spans = _spans(lines)
    wanted = {n.split(".")[-1] for n in (names or [])}
    chosen = []
    if wanted:
        for span in spans:
            if span["name"] in wanted:
                chosen.append(span)
    if not chosen:
        # Nothing matched: hand over the file whole if it is small enough,
        # otherwise the first meaningful definition.
        if len(lines) <= 200:
            chosen = [{"start": 0, "end": len(lines), "name": path.name}]
        else:
            chosen = spans[:1] or [{"start": 0, "end": min(len(lines), 200),
                                    "name": path.name}]

    chunks, used = [], 0
    for span in chosen:
        block = "\n".join(lines[span["start"] : span["end"]])
        header = f"# {rel_path} — {span.get('name', path.name)} (lines {span['start'] + 1}-{span['end']})"
        piece = f"{header}\n{block}"
        if used + len(piece) > budget:
            break
        chunks.append(piece)
        used += len(piece)

    if not chunks:
        return f"# {rel_path} — requested body exceeded the {budget}-char budget"
    return "\n\n".join(chunks)


def caller_context(repo_path: str, symbols: list[str], budget: int = MAX_CALLER_CHARS) -> str:
    """Show each direct caller at its call site (from the reverse call graph)."""
    from src.tools.dependency_graph import DependencyGraph

    if not symbols:
        return ""
    try:
        graph = DependencyGraph(repo_path)
        impact = graph.analyze_impact(symbols, max_depth=2)
    except Exception:
        return ""

    wanted = {s.split(".")[-1] for s in symbols}
    shown, used = [], 0
    for caller in impact.upstream_callers:
        if "::" not in caller:
            continue
        rel, qual = caller.split("::", 1)
        func = qual.split(".")[-1]
        path = Path(repo_path) / rel
        if not path.is_file():
            continue
        lines = _read(path)
        for i, line in enumerate(lines):
            if not re.search(rf"\b{re.escape(func)}\s*\(", line):
                continue
            start = max(0, i - 4)
            end = min(len(lines), i + 6)
            block = "\n".join(
                f"{n + 1:5d} | {lines[n]}" for n in range(start, end)
            )
            piece = f"# caller {caller} — {rel}:{i + 1}\n{block}"
            if used + len(piece) > budget:
                break
            shown.append(piece)
            used += len(piece)
            break
        if used > budget:
            break
    if not shown:
        return ""
    return "DIRECT CALLERS (from the call graph):\n\n" + "\n\n".join(shown)


def tests_for(repo_path: str, test_paths: list[str], budget: int = MAX_TEST_CHARS) -> str:
    """Full source of the most relevant existing test files."""
    blocks, used = [], 0
    for rel in test_paths[:3]:
        path = Path(repo_path) / rel
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if used + len(content) > budget:
            keep = max(0, budget - used)
            if keep < 400:
                break
            content = content[:keep] + "\n# ...[test file budget reached]"
        blocks.append(f"# {rel}\n{content}")
        used += len(content)
    if not blocks:
        return ""
    return "EXISTING TESTS FOR THE SUSPECT CODE (read these first):\n\n" + "\n\n".join(blocks)


def style_conventions(repo_path: str, rel_path: str) -> str:
    """Infer the naming / docstring / typing conventions of one file."""
    path = Path(repo_path) / rel_path
    if not path.is_file():
        return ""
    lines = _read(path)
    if not lines:
        return ""

    def_names = [m.group(3) for line in lines if (m := _DEF_RE.match(line))]
    snake = sum(1 for n in def_names if "_" in n and n.islower())
    camel = sum(1 for n in def_names if re.search(r"[a-z][A-Z]", n))
    docstrings = len(re.findall(r'^\s*(?:async\s+)?def .*\n\s+"""', "\n".join(lines), re.M))
    type_hints = len(re.findall(r"^\s*def \w+\([^)]*\)\s*->", "\n".join(lines), re.M))
    defs = len([n for n in def_names])
    single = sum(1 for line in lines if re.search(r"=\s*'[^']*'", line))
    double = sum(1 for line in lines if re.search(r'=\s*"[^"]*"', line))
    max_len = max((len(l) for l in lines), default=0)

    bits = []
    if defs:
        if snake > camel:
            bits.append("function names are snake_case")
        elif camel > snake:
            bits.append("function names are camelCase")
        bits.append(
            "docstrings on new functions: %s"
            % ("expected (most defs have one)" if docstrings >= defs * 0.4 else "optional here")
        )
        bits.append(
            "return type annotations: %s"
            % ("used" if type_hints >= defs * 0.4 else "rarely used")
        )
    bits.append(
        "string quoting: %s" % ("single quotes" if single > double else "double quotes")
    )
    bits.append(f"longest existing line: {max_len} chars")
    return f"STYLE IN {rel_path}: " + "; ".join(bits)


def build_coder_context(
    repo_path: str,
    targets: list[dict],
    issue_text: str,
    extra_tests: list[str] | None = None,
) -> str:
    """Assemble the Phase-3 context bundle for the Coder.

    ``targets`` is a list of ``{"file": ..., "symbol": ...}`` produced by the
    localizer.  Returns a prompt-ready block; never silently truncates a
    symbol body.
    """
    sections: list[str] = []
    symbols: list[str] = []
    seen_files: list[str] = []

    for target in targets:
        rel = target.get("file", "")
        if not rel or rel in seen_files:
            continue
        seen_files.append(rel)
        symbol = target.get("symbol", "")
        if symbol:
            symbols.append(symbol.split("::")[-1])

        body = full_bodies(repo_path, rel, [symbol] if symbol else None)
        if body:
            sections.append(body)
        style = style_conventions(repo_path, rel)
        if style:
            sections.append(style)

    callers = caller_context(repo_path, symbols or [t.get("symbol", "") for t in targets])
    if callers:
        sections.append(callers)

    tests = list(extra_tests or [])
    if not tests:
        from src.tools.localizer import find_test_files

        tests = [p for p, _ in find_test_files(repo_path, [t.get("file", "") for t in targets], top_k=3)]
    test_block = tests_for(repo_path, tests)
    if test_block:
        sections.append(test_block)

    header = (
        "CODE CONTEXT (full bodies — nothing below is truncated):\n"
        + "\n\n".join(sections)
    )
    if len(header) > 40000:
        header = header[:40000] + "\n# ...[context budget reached]"
    return header
