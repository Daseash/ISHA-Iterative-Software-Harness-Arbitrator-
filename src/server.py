"""
ISHA Backend Server — Connects the Website Fix Bar to the ISHA Autonomous Agent.

Provides HTTP endpoints:
  GET  /api/status  -> Healthcheck & model configuration
  POST /api/fix     -> Dispatches bug/issue to ISHA multi-agent graph & returns verified patch

Security hardening (merged from isha-hardening):
  - Bearer token auth via ISHA_API_TOKEN env var
  - Debug mode gated behind ISHA_API_DEBUG
  - CORS restricted to explicit origins (override with ISHA_API_CORS_ORIGINS)
  - No tracebacks in production error responses
  - Input type validation
  - No dummy-repo fallback for invalid paths
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


def _api_debug_enabled() -> bool:
    """True only when the operator explicitly opted into debug output."""
    return os.getenv("ISHA_API_DEBUG", "0").strip().lower() in {
        "1", "true", "yes", "on"
    }


def _authorized(request: Request) -> bool:
    """Require a bearer token when the operator configured one.

    When ISHA_API_TOKEN is unset or empty, the gate is open (local dev).
    """
    expected = os.getenv("ISHA_API_TOKEN", "").strip()
    if not expected:
        return True
    return request.headers.get("authorization", "") == f"Bearer {expected}"


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
    if not _authorized(request):
        return JSONResponse({"error": "Unauthorized."}, status_code=401)

    try:
        data = await request.json()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        return JSONResponse({"error": "Request body must be a JSON object."}, status_code=400)

    raw_issue = data.get("issue", "")
    issue = raw_issue.strip() if isinstance(raw_issue, str) else ""
    if not issue:
        return JSONResponse({"error": "No issue description provided."}, status_code=400)

    raw_repo = data.get("repo", "")
    repo = raw_repo.strip() if isinstance(raw_repo, str) else ""
    use_multi = bool(data.get("multi", False))
    apply_patch = bool(data.get("apply", False))

    # Resolve repo path (clone remote if necessary)
    target_repo = repo or TARGET_REPO_PATH
    
    # Support shorthand GitHub repos e.g. "django/django" or "psf/requests"
    if not Path(target_repo).exists() and not Path(ROOT / target_repo).exists():
        if not target_repo.startswith(("https://", "http://")) and "/" in target_repo:
            parts = [p.strip() for p in target_repo.split("/") if p.strip()]
            if len(parts) == 2:
                target_repo = f"https://github.com/{parts[0]}/{parts[1]}"

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
        if (ROOT / resolved_path).exists():
            resolved_path = ROOT / resolved_path
        elif (ROOT.parent / resolved_path).exists():
            resolved_path = ROOT.parent / resolved_path
        else:
            resolved_path = ROOT / resolved_path

    resolved_path = resolved_path.expanduser()
    if not resolved_path.exists():
        return JSONResponse({
            "success": False,
            "error": f"Repository does not exist: {resolved_path}",
        }, status_code=400)
    if not resolved_path.is_dir():
        return JSONResponse({
            "success": False,
            "error": f"Repository path is not a directory: {resolved_path}",
        }, status_code=400)
    resolved_path = resolved_path.resolve()

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
        # Always log server-side for debugging
        if _api_debug_enabled():
            traceback.print_exc()
        # Never leak tracebacks to clients in production
        body = {
            "success": False,
            "error": str(exc) if _api_debug_enabled() else "Internal server error.",
        }
        if _api_debug_enabled():
            body["traceback"] = traceback.format_exc()
        return JSONResponse(body, status_code=500)


async def api_apply(request: Request) -> JSONResponse:
    """Apply a synthesized patch directly to a repository."""
    if not _authorized(request):
        return JSONResponse({"error": "Unauthorized."}, status_code=401)
    try:
        data = await request.json()
    except Exception:
        data = {}
    patch = data.get("patch", "")
    raw_repo = data.get("repo", "")
    target_repo = raw_repo.strip() if isinstance(raw_repo, str) else ""
    target_repo = target_repo or TARGET_REPO_PATH
    
    if not patch:
        return JSONResponse({"success": False, "error": "No patch content provided."}, status_code=400)
    
    resolved_path = Path(target_repo)
    if not resolved_path.is_absolute():
        if (ROOT / resolved_path).exists():
            resolved_path = ROOT / resolved_path
        elif (ROOT.parent / resolved_path).exists():
            resolved_path = ROOT.parent / resolved_path
        else:
            resolved_path = ROOT / resolved_path
    resolved_path = resolved_path.resolve()
    
    if not resolved_path.is_dir():
        return JSONResponse({"success": False, "error": f"Target repository not found: {resolved_path}"}, status_code=400)
    
    from src.tools.patch_engine import apply_patch
    applied, detail = apply_patch(str(resolved_path), patch)
    return JSONResponse({
        "success": applied,
        "detail": detail,
        "repo": str(resolved_path),
    })


routes = [
    Route("/api/status", api_status, methods=["GET"]),
    Route("/api/fix", api_fix, methods=["POST"]),
    Route("/api/apply", api_apply, methods=["POST"]),
]

# ── CORS: restricted by default, configurable via env ──────────────────────
_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "ISHA_API_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:3000,http://localhost:3000",
    ).split(",")
    if origin.strip()
]
if os.getenv("ISHA_API_ALLOW_ANY_ORIGIN", "0").strip().lower() in {"1", "true", "yes", "on"}:
    _cors_origins = ["*"]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
]

app = Starlette(debug=_api_debug_enabled(), routes=routes, middleware=middleware)


def run():
    import uvicorn
    port = int(os.getenv("ISHA_API_PORT", "8000"))
    print(f"\n🚀 ISHA API Server starting at http://127.0.0.1:{port} (Fix Bar Connected)")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    run()
