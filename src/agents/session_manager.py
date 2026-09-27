"""
ISHA Session Manager & Progress Ledger.

Provides checkpointed, resumable long-running sessions:
- Persists intermediate progress to disk (`output/sessions/{session_id}.json`).
- Tracks sub-issue completion, accumulated patches, retry history, and human interventions.
- Allows sessions to pause (e.g. for human review or budget limit) and resume seamlessly.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.agents.state import AgentState


class SessionSnapshot(BaseModel):
    """Persisted snapshot of an agentic session."""
    session_id: str
    status: str = "in_progress"  # in_progress | paused_human_review | paused_budget | completed | failed
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    issue_text: str
    repo_path: str
    current_sub_issue_index: int = 0
    sub_issues: List[dict] = Field(default_factory=list)
    accumulated_patches: List[str] = Field(default_factory=list)
    retry_count: int = 0
    critic_verdict: Optional[str] = None
    critic_score: float = 0.0
    history: List[dict] = Field(default_factory=list)


def _sessions_dir() -> Path:
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    out = root / "output" / "sessions"
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_session(
    state: AgentState,
    status: str = "in_progress",
    note: str = "",
) -> str:
    """Save an AgentState snapshot to disk."""
    if not state.session_id:
        state.session_id = f"session_{uuid.uuid4().hex[:10]}"

    out_file = _sessions_dir() / f"{state.session_id}.json"
    existing_history = []
    accumulated_patches = []

    if out_file.exists():
        try:
            prev = json.loads(out_file.read_text(encoding="utf-8"))
            existing_history = prev.get("history", [])
            accumulated_patches = prev.get("accumulated_patches", [])
        except Exception:
            pass

    if state.patch and state.patch not in accumulated_patches and not state.patch.startswith("[CODER ERROR]"):
        accumulated_patches.append(state.patch)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "retry_count": state.retry_count,
        "critic_verdict": state.critic_verdict,
        "critic_score": state.critic_score,
        "note": note,
    }
    existing_history.append(entry)

    snapshot = SessionSnapshot(
        session_id=state.session_id,
        status=status,
        updated_at=datetime.now(timezone.utc).isoformat(),
        issue_text=state.issue_text,
        repo_path=state.repo_path,
        current_sub_issue_index=state.current_sub_issue_index,
        sub_issues=state.sub_issues,
        accumulated_patches=accumulated_patches,
        retry_count=state.retry_count,
        critic_verdict=state.critic_verdict,
        critic_score=state.critic_score,
        history=existing_history,
    )

    out_file.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    return state.session_id


def load_session(session_id: str) -> Optional[dict]:
    """Load a session snapshot by ID."""
    out_file = _sessions_dir() / f"{session_id}.json"
    if not out_file.exists():
        return None
    try:
        return json.loads(out_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_sessions() -> List[dict]:
    """List all saved sessions in output/sessions/."""
    sdir = _sessions_dir()
    sessions = []
    for f in sorted(sdir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "session_id": data.get("session_id", f.stem),
                "status": data.get("status", "unknown"),
                "updated_at": data.get("updated_at", ""),
                "issue_text": data.get("issue_text", "")[:80],
                "sub_issues_count": len(data.get("sub_issues", [])),
                "retry_count": data.get("retry_count", 0),
            })
        except Exception:
            continue
    return sessions


def resume_session_state(session_id: str, human_approved: Optional[bool] = None) -> Optional[AgentState]:
    """Reconstitute an AgentState from a saved session snapshot to resume work."""
    data = load_session(session_id)
    if not data:
        return None

    state = AgentState(
        session_id=data["session_id"],
        issue_text=data["issue_text"],
        repo_path=data["repo_path"],
        sub_issues=data.get("sub_issues", []),
        current_sub_issue_index=data.get("current_sub_issue_index", 0),
        retry_count=0,  # Reset retry budget for the resumed session
        approved=human_approved,
    )
    if data.get("accumulated_patches"):
        state.patch = data["accumulated_patches"][-1]
    return state
