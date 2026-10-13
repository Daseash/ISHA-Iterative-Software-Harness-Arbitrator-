"""
ISHA Model Context Protocol (MCP) Server.

Enables any MCP-compliant client (Claude Desktop, Antigravity IDE, Cursor, Zed, Continue)
to interact directly with ISHA's autonomous software engineering harness:
  - isha_solve: End-to-end bug localization, TDD reproduction, multi-model candidate generation, and Docker verification.
  - isha_localize: Fast BM25 + AST file and function fault ranking.
  - isha_tournament: Generate 3 diverse candidate patches across distinct model strategies with AST gating.
  - isha_verify_patch: Apply patch into Docker/local sandbox and test for regressions.
  - isha_status: Health of model keys, Docker daemon, circuit breakers, and configuration.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except Exception:
        from mcp.server import Server as MCPServer

# Initialize MCP Server
mcp = MCPServer(
    "ISHA-Agent",
)


@mcp.tool()
def isha_status() -> dict[str, Any]:
    """Check ISHA operational status, active LLM key pool, Docker daemon health, and circuit breakers."""
    import src.config as cfg
    from src.tools.docker_sandbox import docker_available

    docker_ok = docker_available()
    active_keys = len(getattr(cfg, "_gemini_key_pool", []))
    cb = getattr(cfg, "_circuit_breaker", None) or getattr(cfg, "circuit_breaker", None)
    circuit_states = dict(cb.state) if cb and hasattr(cb, "state") else {}

    return {
        "agent": getattr(cfg, "AGENT_NAME", "ISHA"),
        "planner_model": getattr(cfg, "PLANNER_MODEL", "gemini/gemini-3.5-flash-lite"),
        "coder_model": getattr(cfg, "CODER_MODEL", "gemini/gemini-3.5-flash-lite"),
        "tournament_candidates": getattr(cfg, "DEFAULT_CANDIDATES", 3),
        "gemini_active_keys": active_keys,
        "docker_daemon_active": docker_ok,
        "circuit_breaker_states": circuit_states,
        "status": "ready" if (active_keys > 0 or os.getenv("ISHA_FORCE_OFFLINE") == "1") else "active",
    }


@mcp.tool()
def isha_localize(repo_path: str, issue_description: str, top_k: int = 5) -> dict[str, Any]:
    """Pinpoint buggy files and code locations using ISHA's BM25 + Tree-sitter AST localizer.

    Args:
        repo_path: Absolute path to the git repository workspace.
        issue_description: The issue report, bug description, or error log.
        top_k: Number of candidate files to return (default: 5).
    """
    from src.tools.localizer import localize

    resolved_path = str(Path(repo_path).resolve())
    candidates = localize(issue_description, resolved_path, top_k=top_k)

    ranked = []
    for c in candidates:
        ranked.append({
            "file_path": getattr(c, "file_path", str(c)),
            "symbol": getattr(c, "symbol_name", ""),
            "score": round(getattr(c, "score", 0.0), 4),
        })

    return {
        "repo_path": resolved_path,
        "ranked_files": ranked,
        "total_ranked": len(ranked),
    }


@mcp.tool()
def isha_tournament(
    repo_path: str,
    issue_description: str,
    n_candidates: int = 3,
    seed_patch: str = "",
) -> dict[str, Any]:
    """Execute ISHA's Multi-Model Tournament across 3 distinct strategies:
    1. minimal_diff (surgical AST logic)
    2. call_site_aware (deep reasoning across callers)
    3. root_cause_first (boundary & container invariants)

    Evaluates candidates through AST compilation gates before returning surviving diffs.

    Args:
        repo_path: Absolute path to target repository.
        issue_description: Bug description or problem statement.
        n_candidates: Number of tournament candidates (default: 3).
        seed_patch: Optional initial diff to seed Candidate #1.
    """
    from src.agents.candidates import generate_candidates
    from src.agents.state import AgentState

    resolved_path = str(Path(repo_path).resolve())
    state = AgentState(
        issue_text=issue_description,
        repo_path=resolved_path,
        patch=seed_patch,
    )

    candidates = generate_candidates(
        state=state,
        n=n_candidates,
        seed_patch=seed_patch,
    )

    survivors = []
    for c in candidates:
        survivors.append({
            "index": c.index,
            "strategy": c.strategy,
            "model": c.model,
            "valid": c.valid,
            "apply_ok": c.apply_ok,
            "gate_ok": c.gate_ok,
            "added_lines": c.added,
            "removed_lines": c.removed,
            "patch": c.patch,
            "gate_errors": c.gate_errors,
        })

    return {
        "total_generated": len(candidates),
        "candidates": survivors,
    }


@mcp.tool()
def isha_verify_patch(
    repo_path: str,
    patch_diff: str,
    test_file: str = "",
) -> dict[str, Any]:
    """Apply a patch diff to a scratch copy of the repository and execute test verification.
    Uses official Docker sandbox when available, otherwise falls back to local sandbox.

    Args:
        repo_path: Target repository path.
        patch_diff: Unified diff patch content.
        test_file: Optional path to a specific pytest file to execute.
    """
    from src.tools.sandbox import make_sandbox
    from src.tools.patch_engine import apply_patch
    from src.bench.gates import compile_gate
    from src.tools.docker_sandbox import run_tests_docker, docker_available

    sbx_path = make_sandbox(repo_path)
    ok, msg = apply_patch(sbx_path, patch_diff)
    if not ok:
        return {
            "applied": False,
            "error": f"Patch application failed: {msg}",
            "passed": False,
        }

    # Static AST compilation gate
    gate = compile_gate(sbx_path, patch_diff, baseline_repo=repo_path)
    if not gate.ok:
        return {
            "applied": True,
            "gate_ok": False,
            "gate_errors": gate.errors,
            "passed": False,
        }

    # Sandbox test execution
    test_output = None
    if docker_available():
        test_output = run_tests_docker(sbx_path, test_file=test_file or None)

    if test_output is None:
        from src.tools.sandbox import _run_tests_local
        test_output = _run_tests_local(sbx_path)

    return {
        "applied": True,
        "gate_ok": True,
        "test_output": test_output,
        "passed": "failed" not in (test_output or "").lower() and "error" not in (test_output or "").lower(),
    }


@mcp.tool()
def isha_solve(
    repo_path: str,
    issue_description: str,
    run_tests: bool = True,
) -> dict[str, Any]:
    """Run ISHA's full autonomous repair lifecycle:
    reproduce bug -> localize fault -> multi-model tournament -> Docker verify -> output unified diff.

    Args:
        repo_path: Path to the target repository workspace.
        issue_description: Description of the bug, issue, or failing requirement.
        run_tests: Whether to execute verification tests in the sandbox (default: True).
    """
    from src.agents.graph import run_agent

    resolved_path = str(Path(repo_path).resolve())
    result_state = run_agent(
        repo_path=resolved_path,
        issue_text=issue_description,
    )

    patch = getattr(result_state, "patch", "")
    plan = getattr(result_state, "plan", "")
    test_output = getattr(result_state, "test_output", "")

    return {
        "status": "solved" if patch and not patch.startswith("[") else "failed",
        "patch": patch,
        "plan": plan,
        "test_output": test_output,
    }


def main():
    """Run the ISHA MCP Server over standard I/O (stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
