"""
ISHA Pre-filter — Phase 7 of the SWE-bench upgrade.

A cheap, deterministic gate that runs *before* any model is called, so the
rate-limit budget is spent on instances that can actually produce a scored
patch.  Every rule is a hard requirement of the harness itself or of the
pipeline, never a guess about difficulty:

  * the record must carry an image, an eval script and a base commit,
  * the problem statement must be long enough to be a real report,
  * the record must be unique in the slice.

Instances dropped here are still counted in the denominator (empty patch,
``failure_category = "prefiltered"``) so filtering can never flatter the
score.
"""

from __future__ import annotations

MIN_ISSUE_CHARS = 40
MAX_ISSUE_CHARS = 40000


def prefilter(record: dict) -> str | None:
    """Return a skip reason, or ``None`` when the instance is runnable."""
    if not record.get("image"):
        return "prefiltered: record has no harness image"
    if not record.get("eval_script"):
        return "prefiltered: record has no eval script"
    if not record.get("base_commit"):
        return "prefiltered: record has no base_commit"
    if not str(record.get("problem_statement") or "").strip():
        return "prefiltered: empty problem statement"
    issue = str(record.get("problem_statement") or "")
    if len(issue) < MIN_ISSUE_CHARS:
        return f"prefiltered: problem statement only {len(issue)} chars"
    if len(issue) > MAX_ISSUE_CHARS:
        return f"prefiltered: problem statement {len(issue)} chars exceeds cap"
    return None


def filter_records(records: list[dict]) -> tuple[list[dict], list[tuple[str, str]]]:
    """Split records into (kept, [(instance_id, reason)])."""
    seen: set[str] = set()
    kept: list[dict] = []
    dropped: list[tuple[str, str]] = []
    for record in records:
        iid = record.get("instance_id", "")
        if iid in seen:
            dropped.append((iid, "prefiltered: duplicate instance_id"))
            continue
        seen.add(iid)
        reason = prefilter(record)
        if reason:
            dropped.append((iid, reason))
        else:
            kept.append(record)
    return kept, dropped
