---
description: Run ISHA autonomous engineering harness to localize, test, and fix a bug.
---

# /isha — Autonomous Software Engineering Arbitrator

You are invoking the **ISHA (Iterative Software Harness & Arbitrator)** system to solve an issue in the codebase.

## Task
Issue / Bug Description:
$ARGUMENTS

## Instructions
1. Check if the ISHA MCP server is active:
   - If `mcp__isha__isha_solve` is available, invoke:
     `mcp__isha__isha_solve(repo_path=".", issue_description="$ARGUMENTS")`
2. If MCP is not connected, run the ISHA CLI in the terminal:
   `isha fix . --issue "$ARGUMENTS"`
   *(Or `python -m src.cli fix . --issue "$ARGUMENTS"`)*
3. Review the output:
   - **Fault Localization**: Which files/AST nodes were identified.
   - **Phase RED**: Reproduction test synthesis.
   - **Phase GREEN**: Multi-candidate tournament & test verification.
   - **LAYA Score**: Decision confidence and safety verdict.
4. Present the verified minimal diff and ask the user if they would like to apply it (`--apply`) or open a PR (`--pr`).
