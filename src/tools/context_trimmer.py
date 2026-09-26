"""
ISHA Context Trimmer — Truncates long pytest tracebacks.

Prevents context overflow by extracting only the root-cause exception.
Implemented in Phase 3.
"""


def trim_traceback(raw_output: str, max_lines: int = 30) -> str:
    """Extract the last traceback + assertion error from pytest output."""
    # TODO: Implement in Phase 3
    return raw_output[-2000:] if len(raw_output) > 2000 else raw_output
