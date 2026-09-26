"""
ISHA Context Trimmer — Truncates long pytest tracebacks.

Keeps only the tail of a test run (the actual failure) so retry prompts
never blow the model's context window.
"""

import re

_PATH_RE = re.compile(r'File "[^"]*[\\/]([^"\\/]+)"')


def trim_traceback(raw_output: str, max_lines: int = 30) -> str:
    """Extract the last traceback + assertion error from pytest output."""
    if not raw_output:
        return ""

    # Prefer the section after the last "=== FAILURES ===" marker.
    marker = raw_output.rfind("=== FAILURES ===")
    body = raw_output[marker:] if marker != -1 else raw_output

    lines = body.splitlines()
    trimmed = lines[-max_lines:] if len(lines) > max_lines else lines

    out = []
    for line in trimmed:
        # Keep only filename.py:lineno, drop long absolute paths.
        match = re.search(r'File ".*[\\/]"', line)
        if match and "line" in line:
            line = line[: match.start()] + 'File ".../' + _path_re.search(line).group(1) + '"' + line[match.end():]
        line = re.sub(r"\\", "/", line)
        if len(line) > 240:
            line = line[:240] + " ..."
        out.append(line)

    text = "\n".join(out)
    if len(text) > 4000:
        text = text[-4000:]
    return text
