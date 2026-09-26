"""
ISHA LAYA Judge — typed decision primitives for every judgment point.

Wraps the LAYA decision engine (choice / score / noul) so patch quality,
danger detection, output verification and triage are calibrated on-device
probabilities instead of free-text LLM opinions.
"""

import os
import threading

# Windows: HF hub falls back to file copies instead of privileged symlinks.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")

import laya  # noqa: E402

_JUDGE = None
_JUDGE_LOCK = threading.Lock()
_INFER_LOCK = threading.Lock()

PATCH_QUESTIONS = {
    "fix_quality": {
        "type": "score",
        "instructions": "How well does this patch fix the reported issue?",
        "criteria": [
            "completely wrong or unrelated",
            "partially addresses the issue",
            "fully fixes the issue correctly",
        ],
    },
    "matches_issue": {
        "type": "noul",
        "instructions": "Does this patch directly address the specific bug described in the issue?",
    },
    "safe_to_apply": {
        "type": "noul",
        "instructions": "Is this patch safe to apply? No destructive changes, "
        "no removed tests, no unrelated modifications?",
    },
}

DANGER_QUESTIONS = {
    "secrets_or_danger": {
        "type": "noul",
        "instructions": "Does this diff contain leaked API keys, secrets, credentials, "
        "or dangerous system calls like os.system, eval, exec, subprocess with shell=True?",
    },
    "logic_drift": {
        "type": "noul",
        "instructions": "Does this diff make changes unrelated to a bug fix, such as "
        "refactoring, adding features, or modifying unrelated code?",
    },
}

VERIFY_QUESTIONS = {
    "looks_correct": {
        "type": "noul",
        "instructions": "Does this code look correct and properly handle the issue described?",
    },
}

# LAYA consumes a fixed-length token budget: anything past the limit is
# silently dropped, which would hide the diff behind a long issue report.
_MAX_ISSUE = 400
_MAX_PLAN = 200
_MAX_DIFF = 1500
_MAX_DANGER_DIFF = 4000


def _compact_issue(text: str) -> str:
    return (text or "").strip()[:_MAX_ISSUE]


def _compact_diff(patch: str) -> str:
    """Keep only the changed lines — that is what the judge scores."""
    changed = [
        line
        for line in (patch or "").splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    text = "\n".join(changed) if changed else (patch or "")
    return text[:_MAX_DIFF]


class LayaJudge:
    """Wraps LAYA decision engine for all judgment points in the pipeline."""

    def __init__(self, device: str = "cpu"):
        self.device = device
        self.agent = laya.load("convaiinnovations/laya", device=device)

    def _predict(self, state, questions) -> dict:
        """Serialized inference — parallel agent branches share one model."""
        with _INFER_LOCK:
            return self.agent.predict(state, questions)

    # ── Patch scoring ────────────────────────────────────────────────── #

    def score_patch(self, issue_text: str, plan: str, patch: str) -> dict:
        """Score a candidate patch on quality, relevance, and safety."""
        state = {
            "issue": _compact_issue(issue_text),
            "plan": (plan or "").strip()[:_MAX_PLAN],
            "patch_diff": _compact_diff(patch),
        }
        result = self._predict(state, PATCH_QUESTIONS)
        answers = result["answers"]
        quality = answers["fix_quality"]["score"]
        matches = answers["matches_issue"]["noul"]
        safe = answers["safe_to_apply"]["noul"]
        return {
            "fix_quality": quality,
            "matches_issue": matches,
            "safe_to_apply": safe,
            "composite": 0.50 * quality / 2.0 + 0.25 * matches + 0.25 * safe,
        }

    # ── Danger detection ─────────────────────────────────────────────── #

    def check_dangers(self, patch: str) -> dict:
        """Check patch for secrets, dangerous operations, logic drift."""
        result = self._predict({"patch_diff": (patch or "")[:_MAX_DANGER_DIFF]}, DANGER_QUESTIONS)
        answers = result["answers"]
        secrets = answers["secrets_or_danger"]["noul"]
        drift = answers["logic_drift"]["noul"]
        return {
            "secrets_or_danger": secrets,
            "logic_drift": drift,
            "flagged": secrets > 0.5 or drift > 0.7,
        }

    # ── Final verification ───────────────────────────────────────────── #

    def verify_output(self, file_content: str, issue_text: str) -> dict:
        """Final check: does the output file look correct?"""
        state = {"code": (file_content or "")[:2000], "original_issue": _compact_issue(issue_text)}
        result = self._predict(state, VERIFY_QUESTIONS)
        probability = result["answers"]["looks_correct"]["noul"]
        return {"correct_probability": probability, "passed": probability >= 0.6}

    # ── Triage ───────────────────────────────────────────────────────── #

    def classify_issue(self, issue_text: str) -> dict:
        """Classify the issue type and urgency using LAYA presets."""
        triage_result = self._predict(
            {"message": issue_text}, laya.triage_questions()
        )
        return triage_result["answers"]


def get_judge(device: str = "cpu") -> LayaJudge:
    """Return the cached module-level LayaJudge (model loads only once)."""
    global _JUDGE
    if _JUDGE is None:
        with _JUDGE_LOCK:
            if _JUDGE is None:
                _JUDGE = LayaJudge(device=device)
    return _JUDGE
