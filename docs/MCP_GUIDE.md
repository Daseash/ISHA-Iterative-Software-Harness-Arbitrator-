# ISHA Model Context Protocol (MCP) Kit

ISHA provides a first-class **Model Context Protocol (MCP)** server, enabling any MCP-compliant client (Antigravity IDE, Claude Desktop, Cursor, Continue.dev, Zed) to autonomously repair codebases, run multi-model candidate tournaments, and verify patches in Docker containers.

---

## 🛠️ Exposed MCP Tools

| Tool Name | Description | Key Parameters |
|---|---|---|
| `isha_status` | Returns agent health, active Gemini key rotation pool size, Docker daemon status, and circuit breakers. | *None* |
| `isha_localize` | Pinpoints buggy files and candidate symbols using BM25 + Tree-sitter AST parsing. | `repo_path`, `issue_description`, `top_k` |
| `isha_tournament` | Generates 3 diverse candidate patches (`minimal_diff`, `call_site_aware`, `root_cause_first`) with AST compilation gate verification. | `repo_path`, `issue_description`, `n_candidates`, `seed_patch` |
| `isha_verify_patch` | Mounts a patch into an ephemeral Docker sandbox and runs official pytest verification. | `repo_path`, `patch_diff`, `test_file` |
| `isha_solve` | Executes the complete autonomous red-to-green LangGraph loop from bug reproduction to verified unified diff. | `repo_path`, `issue_description`, `run_tests` |

---

## 🚀 Quick Setup

### 1. Install ISHA with MCP Support
```bash
pip install -e .
pip install mcp
```

### 2. Run the MCP Server
```bash
# Direct CLI entrypoint:
isha-mcp

# Or via Python module:
python -m src.mcp_server
```

---

## 🔌 Client Configurations

### Claude Desktop (`claude_desktop_config.json`)
Add the following to your Claude configuration:
```json
{
  "mcpServers": {
    "isha": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/ISHA/isha-agent",
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "ISHA_SANDBOX_MODE": "docker"
      }
    }
  }
}
```

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "isha": {
      "command": "python",
      "args": ["-m", "src.mcp_server"]
    }
  }
}
```

---

## 🔒 Operational Invariants
- **Container Isolation**: Patches tested via `isha_verify_patch` are executed in disposable Docker containers or isolated worktree sandboxes, never touching the host environment directly.
- **AST Gate Gating**: All patches produced by `isha_tournament` and `isha_solve` pass syntax compilation gates (`ast.parse`, `py_compile`, `pyflakes`) before being returned.
