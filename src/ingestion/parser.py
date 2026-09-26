"""
ISHA Repo Parser — Walks a repository and chunks source files.

Splits Python modules into module / class / function chunks and Markdown
files into section chunks. Large chunks are split so nothing blows the
planner's token budget.
"""

import re
from pathlib import Path

SKIP_DIRS = {
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    "env",
    "node_modules",
    "qdrant_storage",
    ".worktrees",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}

# ~500 tokens ≈ 2000 characters of source code.
MAX_CHUNK_CHARS = 2000

_PY_DEF = re.compile(r"^(?P<indent>\s*)(?P<kind>class|def)\s+(?P<name>\w+)")
_MD_HEADING = re.compile(r"^(#{1,6})\s+(?P<title>.+)$")


class RepoParser:
    """Parse a repository into chunks for RAG indexing."""

    def parse(self, repo_path: str) -> list:
        """Walk the repo and return a list of chunk dicts."""
        root = Path(repo_path)
        if not root.exists():
            return []

        chunks: list = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            suffix = path.suffix.lower()
            if suffix == ".py":
                chunks.extend(self._parse_python(path, root))
            elif suffix in {".md", ".rst", ".txt"}:
                chunks.extend(self._parse_markdown(path, root))

        return chunks

    # ------------------------------------------------------------------ #

    def _rel(self, path: Path, root: Path) -> str:
        try:
            return str(path.relative_to(root)).replace("\\", "/")
        except ValueError:
            return path.name

    def _emit(self, file_path: str, chunk_type: str, name: str, body: str) -> list:
        """Emit one or more chunks, splitting oversized bodies."""
        body = body.strip("\n")
        if not body.strip():
            return []
        pieces = [body[i : i + MAX_CHUNK_CHARS] for i in range(0, len(body), MAX_CHUNK_CHARS)]
        if len(pieces) == 1:
            return [
                {
                    "file_path": file_path,
                    "content": body,
                    "chunk_type": chunk_type,
                    "name": name,
                }
            ]
        return [
            {
                "file_path": file_path,
                "content": piece,
                "chunk_type": chunk_type,
                "name": f"{name}#part{i + 1}",
            }
            for i, piece in enumerate(pieces)
        ]

    def _parse_python(self, path: Path, root: Path) -> list:
        rel = self._rel(path, root)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        lines = text.splitlines()
        blocks: list = []
        current: dict | None = None
        base_indent = 0

        for line in lines:
            match = _PY_DEF.match(line)
            if match and not line.lstrip().startswith("#"):
                indent = len(match.group("indent").expandtabs(4))
                if current is None or indent <= current["indent"]:
                    if current:
                        blocks.append(current)
                    current = {
                        "kind": match.group("kind"),
                        "name": match.group("name"),
                        "indent": indent,
                        "lines": [line],
                    }
                    base_indent = indent
                else:
                    current["lines"].append(line)
            elif current is not None:
                current["lines"].append(line)

        if current:
            blocks.append(current)

        if not blocks:
            return self._emit(rel, "module", path.stem, text)

        chunks = []
        # Keep the module docstring / header as its own chunk.
        header = []
        for line in lines:
            if _PY_DEF.match(line):
                break
            header.append(line)
        if "".join(header).strip():
            chunks.extend(self._emit(rel, "module", path.stem, "\n".join(header)))

        for block in blocks:
            chunk_type = "class" if block["kind"] == "class" else "function"
            chunks.extend(self._emit(rel, chunk_type, block["name"], "\n".join(block["lines"])))
        return chunks

    def _parse_markdown(self, path: Path, root: Path) -> list:
        rel = self._rel(path, root)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        sections: list = []
        current_title = path.stem
        current_lines: list = []

        for line in text.splitlines():
            heading = _MD_HEADING.match(line)
            if heading:
                if current_lines:
                    sections.append((current_title, "\n".join(current_lines)))
                current_title = heading.group("title").strip()
                current_lines = [line]
            else:
                current_lines.append(line)
        if current_lines:
            sections.append((current_title, "\n".join(current_lines)))

        chunks: list = []
        for title, body in sections:
            chunks.extend(self._emit(rel, "section", title, body))
        return chunks
