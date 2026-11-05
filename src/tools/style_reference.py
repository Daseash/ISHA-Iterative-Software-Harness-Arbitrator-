"""
ISHA Style Reference — code that looks like it belongs in the codebase.

Pulls a couple of example definitions from the file the patch will touch so
the coder matches naming conventions, docstring style, and existing patterns
instead of emitting obviously foreign-looking code.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from src.tools.git_history import mentioned_files


def style_examples(repo_path: str, text: str, max_chars: int = 1400) -> str:
    """Return example functions/classes from the target file, or ""."""
    if not repo_path or not text:
        return ""
    root = Path(repo_path)
    words = set(re.findall(r"[A-Za-z_]\w*", text))

    for rel in mentioned_files(text, limit=3):
        path = root / rel
        if not path.is_file():
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        examples: list[str] = []
        try:
            tree = ast.parse(source)
            defs = [
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            ]
            # Prefer definitions the plan actually mentions, else the file's first two.
            ranked = sorted(defs, key=lambda node: 0 if node.name in words else 1)
            for node in ranked[:2]:
                segment = ast.get_source_segment(source, node) or ""
                if segment.strip():
                    examples.append(f"# {rel} :: {node.name}\n{segment.strip()}")
        except SyntaxError:
            pass

        if not examples:
            head = "\n".join(source.splitlines()[:40])
            examples.append(f"# {rel} (file head)\n{head}")

        block = "\n\n".join(examples)
        if len(block) > max_chars:
            block = block[:max_chars] + "\n...[truncated]"
        return block
    return ""
