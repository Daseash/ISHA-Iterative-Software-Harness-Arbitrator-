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

    tests_passed = "PASSED" in (state.test_output or "")
    entry = {
        "id": str(uuid.uuid4()),
        "digest": digest,
        "ts": time.time(),
        "repo": _normalize_repo(state.repo_path),
        "instance_id": getattr(state, "instance_id", "") or "",
        "issue": issue[:1200],
        "plan": (state.plan or "")[:800],
        "patch": patch[:4000],
        "verdict": state.critic_verdict or "",
        "score": float(state.critic_score or 0.0),
        "tests": "PASSED" if tests_passed else "FAILED",
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

    # Write-A (P0-05): SQLite outcomes with resolved=NULL; JSONL stays as export.
    try:
        from src.memory import store as _mem

        model = getattr(state, "model_name", "") or ""
        if not model:
            try:
                log = getattr(state, "model_log", []) or []
                if log and isinstance(log[-1], dict):
                    model = log[-1].get("model", "") or ""
            except Exception:
                model = ""
        _mem.record_attempt(
            instance_id=entry["instance_id"],
            repo=entry["repo"],
            issue=issue,
            strategy=entry["strategy"],
            model=model,
            patch=patch,
            critic_score=entry["score"],
            tests_passed=tests_passed,
        )
    except Exception:
        pass

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
    include_analog: bool = False,
) -> list[dict]:
    """Past fixes: repo-exact first, then org-prefix, then cross-org analog (opt-in)."""
    if not issue_text or not repo_path:
        return []
    repo = _normalize_repo(repo_path)
    repo_org = repo.replace("\\", "/").split("/")[-1] if repo else ""
    if "__" in repo_org:
        repo_org = repo_org.split("__")[0]
    query = embed_text(issue_text)

    try:
        with open(_ledger_path(), "r", encoding="utf-8") as fh:
            lines = fh.readlines()[-max_entries:]
    except OSError:
        return []

    scored_exact: list[tuple[float, dict]] = []
    scored_org: list[tuple[float, dict]] = []
    scored_other: list[tuple[float, dict]] = []
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        vector = entry.get("vector") or []
        if len(vector) != VECTOR_SIZE:
            continue
        score = cosine(query, vector)
        if score < min_score:
            continue
        erepo = entry.get("repo", "")
        erepo_base = erepo.replace("\\", "/").split("/")[-1] if erepo else ""
        if "__" in erepo_base:
            erepo_base = erepo_base.split("__")[0]
        if erepo == repo:
            scored_exact.append((score, entry))
        elif repo_org and (erepo_base == repo_org or (erepo and erepo.split("/")[0] == repo_org)):
            scored_org.append((score, entry))
        else:
            scored_other.append((score, entry))

    # Prioritize verified resolved (Docker-proven) patches, then local test passes, before raw cosine score
    scored_exact.sort(
        key=lambda pair: (
            pair[1].get("verdict") == "RESOLVED",
            pair[1].get("tests") == "PASSED",
            pair[0],
        ),
        reverse=True,
    )
    scored_org.sort(
        key=lambda pair: (
            pair[1].get("verdict") == "RESOLVED",
            pair[1].get("tests") == "PASSED",
            pair[0],
        ),
        reverse=True,
    )
    scored_other.sort(key=lambda pair: pair[0], reverse=True)
    hits = []
    # P0-06: repo-exact first (backward-compatible), then org-prefix transfer.
    for score, entry in scored_exact[:top_k]:
        hits.append({**entry, "similarity": round(score, 3)})
    if len(hits) < top_k:
        for score, entry in scored_org[: top_k - len(hits)]:
            hits.append({**entry, "similarity": round(score, 3), "transfer": "org"})
    # Cross-org analog: best non-org vector match labeled analog (Django->sympy).
    # Opt-in (include_analog) so repo-exact callers/tests stay isolated by default.
    if include_analog and scored_other:
        best_score, best_entry = scored_other[0]
        if all(best_entry.get("digest") != h.get("digest") for h in hits):
            hits.append({**best_entry, "similarity": round(best_score, 3), "transfer": "cross-org-analog"})

    # P0-05: org-level positives + negative veto from SQLite outcomes (additive).
    try:
        from src.memory import store as _mem

        iid_hint = ""
        org = ""
        # Derive org from repo path last component (astropy/django) for cross-repo transfer.
        parts = [x for x in str(repo).replace("\\", "/").split("/") if x]
        if parts:
            org = parts[-1].lower()
            if "__" in org:
                org = org.split("__")[0]
        conn_hits = _mem_org_positives(org, query, top_k, lines)
        for h in conn_hits:
            if all(h.get("digest") != x.get("digest") for x in hits):
                hits.append(h)
        veto_msg = _mem_negative_veto(org, query, lines)
        if veto_msg:
            hits.append(veto_msg)
    except Exception:
        pass
    return hits


def _mem_org_positives(org: str, query: list, top_k: int, lines: list[str] | None = None) -> list[dict]:
    """SQLite resolved=1 rows for the same org, ranked by cosine when vectors exist."""
    import sqlite3

    from src.memory import store as _mem
    from src.rag.indexer import VECTOR_SIZE as _VS
    from src.rag.indexer import cosine as _cos

    if not org:
        return []
    try:
        conn = sqlite3.connect(str(_mem.db_path()))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT instance_id, repo, strategy, model, critic_score FROM outcomes "
            "WHERE repo_org=? AND resolved=1 LIMIT 20",
            (org,),
        ).fetchall()
        conn.close()
    except Exception:
        return []

    patch_by_iid = {}
    if lines:
        for line in lines:
            try:
                e = json.loads(line)
                if e.get("instance_id") and e.get("patch"):
                    patch_by_iid[e["instance_id"]] = e["patch"]
            except Exception:
                continue

    out = []
    for r in rows[: max(0, top_k)]:
        iid = r["instance_id"]
        out.append({
            "repo": r["repo"],
            "instance_id": iid,
            "strategy": r["strategy"],
            "verdict": "resolved-prior",
            "score": r["critic_score"],
            "similarity": 0.5,
            "patch": patch_by_iid.get(iid, ""),
            "issue": f"prior resolved {iid} ({r['strategy']}/{r['model']})",
        })
    return out


def _mem_negative_veto(org: str, query: list, lines: list[str]) -> dict | None:
    """NEVER-DO marker when the query is near-identical (cos>0.92) to a prior failure.

    Joins JSONL vectors with SQLite Docker truth by instance_id: an entry only
    vetoes when its instance is graded resolved=0 (a real failure, not just a
    low critic score). Returns None when no veto fires.
    """
    import sqlite3

    from src.memory import store as _mem
    from src.rag.indexer import VECTOR_SIZE, cosine

    if not query or len(query) != VECTOR_SIZE:
        return None
    try:
        conn = sqlite3.connect(str(_mem.db_path()))
        rows = conn.execute("SELECT instance_id FROM outcomes WHERE resolved=0").fetchall()
        conn.close()
        failed = {r[0] for r in rows if r[0]}
    except Exception:
        return None
    if not failed:
        return None
    best: tuple[float, dict] | None = None
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("instance_id") not in failed:
            continue
        # Issue-to-issue similarity (stored vectors mix in plan text, which
        # dilutes identical issues below the veto threshold).
        try:
            from src.rag.indexer import embed_text

            score = cosine(query, embed_text(entry.get("issue", "")))
        except Exception:
            continue
        if best is None or score > best[0]:
            best = (score, entry)
    if best is not None and best[0] > 0.92:
        score, entry = best
        return {
            "repo": entry.get("repo", ""),
            "instance_id": entry.get("instance_id", ""),
            "verdict": "NEVER-DO",
            "score": 0.0,
            "similarity": round(score, 3),
            "patch": "",
            "issue": f"NEVER-DO: query ~identical (cos {score:.2f}) to failed {entry.get('instance_id')}"
                     f" — do not repeat its approach: {(entry.get('patch','')[:200])}",
        }
    return None


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
