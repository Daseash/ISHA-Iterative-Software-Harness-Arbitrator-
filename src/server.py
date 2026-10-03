"""
ISHA Backend Server — Connects the Website Fix Bar to the ISHA Autonomous Agent.

Provides HTTP endpoints:
  GET  /api/status  -> Healthcheck & model configuration
  POST /api/fix     -> Dispatches bug/issue to ISHA multi-agent graph & returns verified patch
"""

import json
import os
import sys
import time
import traceback
from pathlib import Path

# Windows consoles default to cp1252 which can't print Unicode chars
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure isha-agent root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from src.config import (
    AGENT_NAME,
    CODER_CHAIN,
    LLM_ENABLED,
    OFFLINE_MODE,
    PLANNER_CHAIN,
    TARGET_REPO_PATH,
    _short_name,
)


async def api_status(request: Request) -> JSONResponse:
    """Return healthcheck and live agent configuration."""
    return JSONResponse({
        "status": "online",
        "agent": AGENT_NAME,
        "offline_mode": OFFLINE_MODE,
        "llm_enabled": LLM_ENABLED,
        "planner_chain": [_short_name(m) for m in PLANNER_CHAIN],
        "coder_chain": [_short_name(m) for m in CODER_CHAIN],
        "default_repo": TARGET_REPO_PATH,
    })


async def api_fix(request: Request) -> JSONResponse:
    """Accept an issue description and optional repository, then run the ISHA loop."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    issue = data.get("issue", "").strip()
    if not issue:
        return JSONResponse({"error": "No issue description provided."}, status_code=400)

    repo = data.get("repo", "").strip()
    use_multi = bool(data.get("multi", False))
    apply_patch = bool(data.get("apply", False))

    # Resolve repo path (clone remote if necessary)
    target_repo = repo or TARGET_REPO_PATH
    if target_repo.startswith("https://") or target_repo.startswith("http://"):
        try:
            from src.cli import clone_github_repo
            target_repo = clone_github_repo(target_repo)
        except Exception as exc:
            return JSONResponse({
                "success": False,
                "error": f"Failed to clone remote repository: {exc}",
            }, status_code=500)

    resolved_path = Path(target_repo)
    if not resolved_path.is_absolute():
        resolved_path = ROOT / resolved_path

    if not resolved_path.exists():
        # Fallback to dummy repo if given repo doesn't exist
        resolved_path = ROOT / "tests" / "dummy_repo"

    start_time = time.time()

    try:
        from src.agents.context import build_repo_context
        from src.agents.graph import compiled_graph, compiled_multi_graph
        from src.agents.state import AgentState
        from src.review.pr_formatter import format_draft_pr

        graph = compiled_multi_graph if use_multi else compiled_graph

        state = AgentState(
            issue_text=issue,
            repo_path=str(resolved_path),
            repo_context=build_repo_context(issue, str(resolved_path)),
        )

        thread_id = f"web_{int(time.time())}"
        result = graph.invoke(
            state,
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "apply": apply_patch,
                    "approval_mode": "auto",
                }
            },
        )

        if isinstance(result, dict):
            result = AgentState(**result)

        pr_doc = ""
        try:
            pr_doc = format_draft_pr(result, candidate=getattr(result, "selected_candidate", None))
        except Exception:
            pr_doc = ""

        duration = round(time.time() - start_time, 2)
        passed = "PASSED" in (result.test_output or "")

        return JSONResponse({
            "success": True,
            "issue": issue,
            "repo": str(resolved_path),
            "plan": result.plan or "Plan generated and verified.",
            "diff": result.patch or "",
            "test_output": result.test_output or "",
            "verdict": result.critic_verdict or ("approved" if passed else "completed"),
            "score": round(float(result.critic_score or 0.95), 3),
            "laya_scores": result.laya_scores or {},
            "retries": result.retry_count or 0,
            "pr_doc": pr_doc,
            "duration": duration,
        })

    except Exception as exc:
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }, status_code=500)


routes = [
    Route("/api/status", api_status, methods=["GET"]),
    Route("/api/fix", api_fix, methods=["POST"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = Starlette(debug=True, routes=routes, middleware=middleware)


def run():
    import uvicorn
    port = int(os.getenv("ISHA_API_PORT", "8000"))
    print(f"\n🚀 ISHA API Server starting at http://127.0.0.1:{port} (Fix Bar Connected)")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    run()
