"""
ISHA Fix History — learning from its own fixes (the long-tenure effect).

Every real attempt is appended to a local JSONL ledger and mirrored into a
Qdrant collection when a server is reachable. Before planning, past fixes
for the same repository are retrieved by similarity and shown to the
planner so it picks up the codebase's quirks — the way a senior engineer
gets sharper on a repo the longer they work there.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path

from src.rag.indexer import VECTOR_SIZE, cosine, embed_text

COLLECTION = "isha_fix_history"


def _ledger_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    path = root / "output" / "fix_history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_repo(repo_path: str) -> str:
    return Path(str(repo_path or "")).as_posix().rstrip("/").lower()


def record_fix(state) -> bool:
    """Persist a completed attempt (issue, patch, outcome) to the fix ledger."""
    patch = (state.patch or "").strip()
    if not patch or "ERROR" in patch[:60]:
        return False

    issue = (state.issue_text or "").strip()
    digest = hashlib.sha1(f"{issue}::{patch}".encode("utf-8")).hexdigest()

    entry = {
        "id": str(uuid.uuid4()),
        "digest": digest,
        "ts": time.time(),
        "repo": _normalize_repo(state.repo_path),
        "issue": issue[:1200],
        "plan": (state.plan or "")[:800],
        "patch": patch[:4000],
        "verdict": state.critic_verdict or "",
        "score": float(state.critic_score or 0.0),
        "tests": "PASSED" if "PASSED" in (state.test_output or "") else "FAILED",
        "strategy": state.strategy,
        "vector": embed_text(f"{issue} {state.plan or ''}"),
    }

    if _is_duplicate(digest):
        return False

    try:
        with open(_ledger_path(), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        return False

    _mirror_qdrant(entry)
    return True


def _is_duplicate(digest: str, tail: int = 200) -> bool:
    """Skip re-recording an identical issue+patch pair (sessions save often)."""
    try:
        with open(_ledger_path(), "r", encoding="utf-8") as fh:
            lines = fh.readlines()[-tail:]
    except OSError:
        return False
    for line in reversed(lines):
        try:
            if json.loads(line).get("digest") == digest:
                return True
        except (json.JSONDecodeError, AttributeError):
            continue
    return False


def _mirror_qdrant(entry: dict) -> None:
    """Best-effort mirror; the JSONL ledger remains the source of truth."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams

        client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_API_KEY"),
            timeout=2,
        )
        try:
            client.get_collection(COLLECTION)
        except Exception:
            client.recreate_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
        payload = {
            key: entry[key]
            for key in ("repo", "issue", "plan", "patch", "verdict", "score", "tests", "ts")
        }
        client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(id=entry["id"], vector=entry["vector"], payload=payload)],
        )
    except Exception:
        pass


def retrieve_fixes(
    issue_text: str,
    repo_path: str,
    top_k: int = 2,
    min_score: float = 0.15,
    max_entries: int = 500,
) -> list[dict]:
    """Past fixes for the same repository, most similar first."""
    if not issue_text or not repo_path:
        return []
    repo = _normalize_repo(repo_path)
    query = embed_text(issue_text)

    try:
        with open(_ledger_path(), "r", encoding="utf-8") as fh:
            lines = fh.readlines()[-max_entries:]
    except OSError:
        return []

    scored: list[tuple[float, dict]] = []
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("repo") != repo:
            continue
        vector = entry.get("vector") or []
        if len(vector) != VECTOR_SIZE:
            continue
        score = cosine(query, vector)
        if score >= min_score:
            scored.append((score, entry))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    hits = []
    for score, entry in scored[:top_k]:
        hits.append({**entry, "similarity": round(score, 3)})
    return hits


def render_hits(hits: list[dict]) -> str:
    """Format retrieved fixes for a planner prompt (trimmed)."""
    lines = []
    for hit in hits:
        lines.append(
            f"- Issue: {hit.get('issue', '')[:300]}\n"
            f"  Outcome: verdict={hit.get('verdict')} score={hit.get('score')} "
            f"tests={hit.get('tests')} (similarity {hit.get('similarity')})\n"
            f"  Patch excerpt:\n{hit.get('patch', '')[:500]}"
        )
    return "\n".join(lines)
