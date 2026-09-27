"""
ISHA Dependency Graph & Impact Analysis Engine.

Extracts repo-level call graphs, import graphs, and symbol definitions using
AST analysis. Computes the blast radius / impact analysis of suspected bug
entry points to understand downstream callers, upstream dependencies, and
affected test files.
"""

from __future__ import annotations

import ast
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.ingestion.parser import SKIP_DIRS


@dataclass
class SymbolDefinition:
    """A function, method, or class defined in the repository."""
    name: str
    qualified_name: str  # e.g., "calculator.py::Calculator.subtract"
    file_path: str       # relative path, e.g. "calculator.py"
    line_start: int
    line_end: int
    kind: str            # "function", "method", "class"
    parameters: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ImpactAnalysis:
    """Blast radius report for a given set of entry points."""
    entry_points: List[str]
    affected_files: List[str]
    directly_impacted_symbols: List[str]
    upstream_callers: List[str]  # Functions/methods calling the affected symbols
    dependent_modules: List[str] # Files importing the affected files
    impacted_test_files: List[str]
    blast_radius_score: float    # 0.0 to 1.0 representing proportion of repo affected


class ASTVisitor(ast.NodeVisitor):
    """Walk an AST to collect definitions, imports, and function calls."""

    def __init__(self, rel_path: str):
        self.rel_path = rel_path.replace("\\", "/")
        self.definitions: List[SymbolDefinition] = []
        self.imports: Set[str] = set()
        self.calls: Dict[str, Set[str]] = defaultdict(set)  # caller_qname -> set of callee names
        self.current_scope: List[str] = []

    def _current_qname(self) -> str:
        if not self.current_scope:
            return f"{self.rel_path}::<module>"
        return f"{self.rel_path}::{'.'.join(self.current_scope)}"

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        self.imports.add(mod)
        for alias in node.names:
            self.imports.add(f"{mod}.{alias.name}" if mod else alias.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.current_scope.append(node.name)
        qname = f"{self.rel_path}::{'.'.join(self.current_scope)}"
        self.definitions.append(
            SymbolDefinition(
                name=node.name,
                qualified_name=qname,
                file_path=self.rel_path,
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                kind="class",
                parameters=[b.id for b in node.bases if isinstance(b, ast.Name)],
                docstring=ast.get_docstring(node),
            )
        )
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_func(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_func(node, is_async=True)

    def _handle_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool):
        is_method = bool(self.current_scope)
        self.current_scope.append(node.name)
        qname = f"{self.rel_path}::{'.'.join(self.current_scope)}"
        params = [arg.arg for arg in node.args.args]

        self.definitions.append(
            SymbolDefinition(
                name=node.name,
                qualified_name=qname,
                file_path=self.rel_path,
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                kind="method" if is_method else "function",
                parameters=params,
                docstring=ast.get_docstring(node),
            )
        )
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_Call(self, node: ast.Call):
        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
        if callee_name:
            caller = self._current_qname()
            self.calls[caller].add(callee_name)
        self.generic_visit(node)


class DependencyGraph:
    """Main repository-level dependency graph manager."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.definitions: List[SymbolDefinition] = []
        self.symbols_by_name: Dict[str, List[SymbolDefinition]] = defaultdict(list)
        self.symbols_by_qname: Dict[str, SymbolDefinition] = {}

        # Graphs
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)       # file -> imported files
        self.reverse_import_graph: Dict[str, Set[str]] = defaultdict(set)# file -> files importing it
        self.call_graph: Dict[str, Set[str]] = defaultdict(set)         # caller_qname -> callee names
        self.reverse_call_graph: Dict[str, Set[str]] = defaultdict(set) # callee_name -> caller qnames
        self.files: Set[str] = set()

        if self.repo_path.exists():
            self.build()

    def build(self) -> None:
        """Scan repository files and build import and call graphs."""
        for path in sorted(self.repo_path.rglob("*.py")):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            try:
                rel = str(path.relative_to(self.repo_path)).replace("\\", "/")
            except ValueError:
                rel = path.name

            self.files.add(rel)
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=str(path))
            except Exception:
                continue

            visitor = ASTVisitor(rel)
            visitor.visit(tree)

            # Store definitions
            for sym in visitor.definitions:
                self.definitions.append(sym)
                self.symbols_by_name[sym.name].append(sym)
                self.symbols_by_qname[sym.qualified_name] = sym

            # Resolve imports to repo files
            for raw_import in visitor.imports:
                target_file = self._resolve_import_to_file(raw_import)
                if target_file and target_file != rel:
                    self.import_graph[rel].add(target_file)
                    self.reverse_import_graph[target_file].add(rel)

            # Record call relationships
            for caller, callees in visitor.calls.items():
                self.call_graph[caller].update(callees)
                for callee in callees:
                    self.reverse_call_graph[callee].add(caller)

    def _resolve_import_to_file(self, import_str: str) -> Optional[str]:
        """Convert an import path like `src.config` or `calculator` to a repo file."""
        parts = import_str.split(".")
        # Try exact match as path
        potential_path = "/".join(parts) + ".py"
        for f in self.files:
            if f.endswith(potential_path) or f == potential_path:
                return f

        # Try module match
        if parts:
            cand = parts[-1] + ".py"
            for f in self.files:
                if f.endswith("/" + cand) or f == cand:
                    return f
        return None

    def find_symbols(self, query: str) -> List[SymbolDefinition]:
        """Lookup symbols by exact or partial name."""
        matches = []
        q_lower = query.lower()
        for sym in self.definitions:
            if q_lower == sym.name.lower() or q_lower in sym.qualified_name.lower():
                matches.append(sym)
        return matches

    def analyze_impact(
        self,
        entry_points: List[str],
        max_depth: int = 3,
    ) -> ImpactAnalysis:
        """
        Compute blast radius given entry symbols, functions, or files.
        Traverses reverse call graphs and reverse import graphs.
        """
        affected_files: Set[str] = set()
        direct_symbols: Set[str] = set()
        upstream_callers: Set[str] = set()
        dependent_modules: Set[str] = set()
        impacted_test_files: Set[str] = set()

        for ep in entry_points:
            # Check if entry point is a file
            for f in self.files:
                if ep in f:
                    affected_files.add(f)

            # Check if entry point matches any symbols
            matches = self.find_symbols(ep)
            for m in matches:
                direct_symbols.add(m.qualified_name)
                affected_files.add(m.file_path)

                # Upstream callers via reverse call graph
                callers = self.reverse_call_graph.get(m.name, set())
                upstream_callers.update(callers)

        # Transitive callers BFS
        queue = deque(list(upstream_callers))
        visited_callers = set(upstream_callers)
        depth = 1

        while queue and depth < max_depth:
            level_size = len(queue)
            for _ in range(level_size):
                curr_caller = queue.popleft()
                # If caller has a file, track file
                if "::" in curr_caller:
                    caller_file = curr_caller.split("::")[0]
                    affected_files.add(caller_file)

                # Check who calls this caller's function name
                func_name = curr_caller.split("::")[-1].split(".")[-1]
                for next_caller in self.reverse_call_graph.get(func_name, set()):
                    if next_caller not in visited_callers:
                        visited_callers.add(next_caller)
                        upstream_callers.add(next_caller)
                        queue.append(next_caller)
            depth += 1

        # Traverse reverse import graph for affected files
        for aff_file in list(affected_files):
            deps = self.reverse_import_graph.get(aff_file, set())
            dependent_modules.update(deps)
            affected_files.update(deps)

        # Identify test files among affected or dependent files
        for f in affected_files | dependent_modules:
            if "test" in f.lower():
                impacted_test_files.add(f)

        total_files = max(1, len(self.files))
        blast_score = min(1.0, len(affected_files) / total_files)

        return ImpactAnalysis(
            entry_points=entry_points,
            affected_files=sorted(list(affected_files)),
            directly_impacted_symbols=sorted(list(direct_symbols)),
            upstream_callers=sorted(list(upstream_callers)),
            dependent_modules=sorted(list(dependent_modules)),
            impacted_test_files=sorted(list(impacted_test_files)),
            blast_radius_score=round(blast_score, 2),
        )

    def render_impact_report(self, impact: ImpactAnalysis) -> str:
        """Format impact analysis into a prompt-friendly markdown block."""
        lines = [
            "### Repository Dependency & Impact Analysis",
            f"- Entry points: {', '.join(impact.entry_points) or 'none'}",
            f"- Blast radius score: {int(impact.blast_radius_score * 100)}% of repository",
            f"- Directly impacted symbols: {len(impact.directly_impacted_symbols)}",
        ]
        for s in impact.directly_impacted_symbols[:8]:
            lines.append(f"  * `{s}`")

        lines.append(f"- Upstream callers ({len(impact.upstream_callers)}):")
        for c in impact.upstream_callers[:8]:
            lines.append(f"  * `{c}`")
        if len(impact.upstream_callers) > 8:
            lines.append(f"  * ... (+{len(impact.upstream_callers) - 8} more)")

        lines.append(f"- Dependent modules: {', '.join(impact.dependent_modules[:6]) or 'none'}")
        lines.append(f"- Impacted test files: {', '.join(impact.impacted_test_files) or 'none'}")
        return "\n".join(lines)
