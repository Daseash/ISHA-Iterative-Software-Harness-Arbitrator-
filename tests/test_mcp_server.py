"""Tests for ISHA Model Context Protocol (MCP) Server."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from src import mcp_server


def test_mcp_server_initialization_and_tool_registration():
    """Verify that all 5 core ISHA tools are registered on the MCP server."""
    tools = asyncio.run(mcp_server.mcp.list_tools())
    tool_names = {t.name for t in tools}
    expected = {
        "isha_status",
        "isha_localize",
        "isha_tournament",
        "isha_verify_patch",
        "isha_solve",
    }
    assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"


def test_isha_status_returns_operational_dict():
    """Verify isha_status returns the expected health keys."""
    status = mcp_server.isha_status()
    assert "agent" in status
    assert "planner_model" in status
    assert "coder_model" in status
    assert "tournament_candidates" in status
    assert "gemini_active_keys" in status
    assert "docker_daemon_active" in status
    assert "status" in status


def test_isha_localize_tool_returns_ranked_files(tmp_path):
    """Verify isha_localize invokes localize_node and returns ranked results."""
    dummy_file = tmp_path / "target.py"
    dummy_file.write_text("def bug():\n    return False\n", encoding="utf-8")

    result = mcp_server.isha_localize(
        repo_path=str(tmp_path),
        issue_description="fix bug in target.py",
        top_k=3,
    )
    assert "ranked_files" in result
    assert "repo_path" in result


def test_isha_verify_patch_rejects_bad_patch(tmp_path):
    """Verify isha_verify_patch handles patch apply errors safely without crashing."""
    bad_diff = "diff --git a/missing.py b/missing.py\n--- a/missing.py\n+++ b/missing.py\n@@ -1 +1 @@\n-old\n+new\n"
    res = mcp_server.isha_verify_patch(
        repo_path=str(tmp_path),
        patch_diff=bad_diff,
    )
    assert res["applied"] is False
    assert "Patch application failed" in res["error"]
