"""
ISHA AST Mapper — Tree-sitter based repository structure map.

Produces a compact, token-efficient view of a codebase showing only class
and function signatures (no bodies). This map is what the Planner sees
instead of the whole repo, keeping prompt sizes small.
"""

from pathlib import Path

from src.ingestion.parser import SKIP_DIRS

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser

    _PY_LANGUAGE = Language(tspython.language())
    _PARSER = Parser(_PY_LANGUAGE)
except Exception:  # pragma: no cover - tree-sitter optional at runtime
    _PY_LANGUAGE = None
    _PARSER = None

_SIGNATURE_NODES = {"function_definition", "class_definition"}
_SKIP_TYPES = {"comment", "string", "expression_statement"}


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _name_of(node, source: bytes) -> str:
    for child in node.children:
        if child.type == "identifier":
            return _node_text(child, source)
        if child.type == "attribute":
            return _node_text(child, source)
    return "<anonymous>"


def _signature(node, source: bytes) -> str:
    """Return `def name(args):` / `class Name(Base):` without the body."""
    name = _name_of(node, source)
    params = None
    superclass = None
    for child in node.children:
        if child.type == "parameters":
            params = child
        elif child.type == "superclass":
            superclass = child

    if params is not None:
        inner = " ".join(_node_text(params, source).strip()[1:-1].split())
        return f"{name}({inner})"
    if superclass is not None:
        return f"{name}({_node_text(superclass, source)})"
    return name


class ASTMapper:
    """Build a structural map of a Python codebase using tree-sitter."""

    def build_map(self, repo_path: str) -> str:
        """Parse all .py files and return a compact structure map."""
        root = Path(repo_path)
        if not root.exists():
            return ""

        sections: list = []
        for path in sorted(root.rglob("*.py")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            body = self._map_file(path)
            if body:
                try:
                    rel = str(path.relative_to(root)).replace("\\", "/")
                except ValueError:
                    rel = path.name
                sections.append(f"{rel}:\n{body}")

        return "\n".join(sections)

    def _map_file(self, path: Path) -> str:
        try:
            source = path.read_bytes()
        except OSError:
            return ""

        if _PARSER is None:
            return self._regex_map(source.decode("utf-8", errors="replace"))

        tree = _PARSER.parse(source)
        lines: list = []
        self._walk(tree.root_node, source, lines, depth=1)
        return "\n".join(lines)

    def _walk(self, node, source: bytes, out: list, depth: int) -> None:
        for child in node.children:
            if child.type == "module":
                self._walk(child, source, out, depth)
                continue
            if child.type in _SIGNATURE_NODES:
                indent = "  " * depth
                out.append(f"{indent}{_signature(child, source)}")
                # nested defs/classes live inside the body
                for sub in child.children:
                    if sub.type == "block":
                        self._walk(sub, source, out, depth + 1)
            elif child.type == "block":
                self._walk(child, source, out, depth)

    def _regex_map(self, text: str) -> str:
        """Fallback structural map when tree-sitter is unavailable."""
        import re

        out = []
        for line in text.splitlines():
            match = re.match(r"^(\s*)(class|def)\s+(\w+\(.*\):|[\w]+:)", line.strip())
            if match:
                out.append(line.rstrip())
        return "\n".join(out)
