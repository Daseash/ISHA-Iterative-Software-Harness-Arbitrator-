"""
ISHA Cross-File Consistency Checker.

Validates multi-file changes and detects broken call sites across the repository:
1. Detects modified or renamed function/method signatures in candidate patches.
2. Traverses the AST dependency graph to find all call sites in other files.
3. Flags cross-file inconsistencies if callers were left un-updated.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from src.tools.dependency_graph import DependencyGraph

_DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)", re.MULTILINE)
_DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.*?)$", re.MULTILINE)


def extract_modified_signatures(diff_text: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Extract functions whose signatures were altered in the diff.
    Returns: {filename: {"added_or_changed": [(func_name, params)], "removed": [...]}}
    """
    current_file = None
    changes: Dict[str, Dict[str, List[str]]] = {}

    for line in diff_text.splitlines():
        file_match = _DIFF_FILE_RE.match(line)
        if file_match:
            current_file = file_match.group(1).strip()
            if current_file not in changes:
                changes[current_file] = {"added": [], "removed": []}
            continue

        if not current_file:
            continue

        if line.startswith("-") and not line.startswith("---"):
            match = _DEF_RE.search(line[1:])
            if match:
                changes[current_file]["removed"].append(match.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            match = _DEF_RE.search(line[1:])
            if match:
                changes[current_file]["added"].append(match.group(1))

    return changes


def check_patch_consistency(
    repo_path: str,
    diff_text: str,
    dep_graph: DependencyGraph | None = None,
) -> List[str]:
    """
    Verify cross-file consistency of candidate patches.
    Flags if a signature is modified in file A while callers in file B are ignored.
    """
    if not diff_text or not diff_text.strip():
        return []

    if dep_graph is None:
        dep_graph = DependencyGraph(repo_path)

    sig_changes = extract_modified_signatures(diff_text)
    patched_files = set(sig_changes.keys())
    warnings: List[str] = []

    for fpath, delta in sig_changes.items():
        # Check removed or changed function names
        removed_funcs = set(delta["removed"]) - set(delta["added"])
        for func in removed_funcs:
            callers = dep_graph.reverse_call_graph.get(func, set())
            for caller in callers:
                caller_file = caller.split("::")[0] if "::" in caller else caller
                if caller_file not in patched_files and caller_file != fpath:
                    warnings.append(
                        f"Cross-file inconsistency: '{func}' was removed/renamed in '{fpath}', "
                        f"but caller '{caller}' in '{caller_file}' was not updated in this patch."
                    )

        # Check modified parameters for functions present in both removed and added
        changed_funcs = set(delta["removed"]) & set(delta["added"])
        for func in changed_funcs:
            callers = dep_graph.reverse_call_graph.get(func, set())
            external_callers = [c for c in callers if not c.startswith(fpath)]
            if external_callers:
                unpatched_callers = [
                    c for c in external_callers
                    if c.split("::")[0] not in patched_files
                ]
                if unpatched_callers:
                    sample = ", ".join(unpatched_callers[:3])
                    warnings.append(
                        f"Signature changed for '{func}' in '{fpath}'. "
                        f"Verify {len(unpatched_callers)} external call sites: {sample}"
                    )

    return warnings
