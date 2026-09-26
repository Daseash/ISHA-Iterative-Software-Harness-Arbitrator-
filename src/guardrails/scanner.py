"""
ISHA Guardrail Scanner — secret leakage and prompt-injection detection.

Regex rules first (fast, offline); the NeMo rails config in rails.co
adds conversational input/output rails on top for the dashboard path.
"""

import re

# ── Secret / danger patterns ───────────────────────────────────────────────
SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("AWS secret key", re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][^'\"]{8,}")),
    ("OpenAI/Anthropic-style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.")),
    ("Hardcoded password", re.compile(r"(?i)\b(password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}['\"]")),
    ("Hardcoded secret", re.compile(r"(?i)\b(secret|token|api_key|apikey)\s*=\s*['\"][^'\"]{8,}['\"]")),
    ("Private key block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

DANGEROUS_PATTERNS = [
    ("os.system call", re.compile(r"\bos\.system\s*\(")),
    ("subprocess shell=True", re.compile(r"subprocess\.[a-z_]+\([^)]*shell\s*=\s*True")),
    ("eval()", re.compile(r"\beval\s*\(")),
    ("exec()", re.compile(r"\bexec\s*\(")),
    ("__import__ obfuscation", re.compile(r"__import__\s*\(")),
    ("rm -rf", re.compile(r"\brm\s+-rf\s+/")),
]

# ── Prompt-injection patterns ──────────────────────────────────────────────
INJECTION_PATTERNS = [
    ("ignore previous instructions", re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions")),
    ("reveal system prompt", re.compile(r"(?i)(reveal|show|print|output)\s+(your\s+)?(system\s+prompt|instructions|hidden\s+prompt)")),
    ("role override", re.compile(r"(?i)(you\s+are\s+now|act\s+as\s+if\s+you\s+(have|are)\s+no|pretend\s+(to\s+be|you\s+are)\s+(an?\s+)?unrestricted)")),
    ("developer/jailbreak mode", re.compile(r"(?i)(developer\s+mode|jailbreak|dan\s+mode|ignore\s+safety)")),
    ("forget everything", re.compile(r"(?i)forget\s+(everything|all\s+previous|the\s+system)")),
    ("new instructions follow", re.compile(r"(?i)(disregard|overrule)\s+(the\s+)?(system|previous|initial)")),
]


def scan_patch_for_secrets(diff_text: str) -> tuple:
    """Return (is_clean, list_of_findings) for a candidate diff."""
    findings = []
    if not diff_text:
        return True, findings

    # Only inspect added/changed lines — removed lines are going away.
    changed = "\n".join(
        line for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")
    )
    haystack = changed or diff_text

    for name, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(haystack):
            findings.append(f"{name}: {match.group(0)[:12]}…")
    for name, pattern in DANGEROUS_PATTERNS:
        if pattern.search(haystack):
            findings.append(f"{name}")

    return (len(findings) == 0), findings


def scan_input_for_injection(text: str) -> tuple:
    """Return (is_safe, reason) for user-supplied issue text."""
    if not text:
        return True, ""
    for name, pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return False, f"Prompt injection detected ({name}): “{match.group(0)[:60]}”"
    return True, ""


def scan(diff_text: str, issue_text: str = "") -> dict:
    """Combined guardrail report used by the approval gate."""
    clean, findings = scan_patch_for_secrets(diff_text)
    safe, reason = scan_input_for_injection(issue_text)
    return {
        "patch_clean": clean,
        "patch_findings": findings,
        "input_safe": safe,
        "input_reason": reason,
        "blocked": (not clean) or (not safe),
    }
