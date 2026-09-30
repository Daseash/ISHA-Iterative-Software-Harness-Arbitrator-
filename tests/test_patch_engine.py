"""Tests for the patch engine — bare @@ headers and multi-file splits."""

from pathlib import Path

from src.tools.patch_engine import _split_files, apply_patch

CALC = """class Calculator:
    def percentage(self, value: float) -> float:
        return float(value)
"""

FMT = """from calculator import Calculator

_calc = Calculator()


def format_percentage(part: float, whole: float) -> str:
    pct = _calc.percentage(part)
    return f"{pct:.1f}%"
"""

BARE_MULTI = """--- a/calculator.py
+++ b/calculator.py
@@
-        return float(value)
+        return (float(value) / float(total)) * 100
--- a/formatter.py
+++ b/formatter.py
@@
-    pct = _calc.percentage(part)
+    pct = _calc.percentage(part, total=whole)
"""


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "calculator.py").write_text(CALC, encoding="utf-8")
    (tmp_path / "formatter.py").write_text(FMT, encoding="utf-8")
    return tmp_path


def test_split_files_separates_plain_file_records():
    """A plain ``---`` while a record is open must start a new file."""
    records = _split_files(BARE_MULTI)
    assert len(records) == 2
    assert {r["new"] for r in records} == {"calculator.py", "formatter.py"}
    assert all(len(r["hunks"]) == 1 for r in records)


def test_bare_hunk_headers_apply_to_the_right_files(tmp_path):
    """Bare ``@@`` headers have no line numbers — must still apply."""
    repo = _repo(tmp_path)
    ok, message = apply_patch(str(repo), BARE_MULTI)
    assert ok, message
    assert "/ float(total)) * 100" in (repo / "calculator.py").read_text(encoding="utf-8")
    assert "total=whole" in (repo / "formatter.py").read_text(encoding="utf-8")


def test_split_files_keeps_multiple_hunks_in_one_record():
    """Hunk body lines beginning with '-' stay inside their own hunk."""
    diff = (
        "--- a/formatter.py\n"
        "+++ b/formatter.py\n"
        "@@\n"
        "-    old_one()\n"
        "+    new_one()\n"
        "@@\n"
        "-    -1  # negative literal\n"
        "+    -2  # negative literal\n"
    )
    records = _split_files(diff)
    assert len(records) == 1
    assert len(records[0]["hunks"]) == 2
    assert records[0]["hunks"][1][1] == "-    -1  # negative literal"


def test_search_replace_block_application(tmp_path):
    repo = _repo(tmp_path)
    sr_patch = """
File: calculator.py
<<<<<<< SEARCH
    def percentage(self, value: float) -> float:
        return float(value)
=======
    def percentage(self, value: float) -> float:
        return float(value) * 100.0
>>>>>>> REPLACE
"""
    ok, message = apply_patch(str(repo), sr_patch)
    assert ok, message
    content = (repo / "calculator.py").read_text(encoding="utf-8")
    assert "float(value) * 100.0" in content


def test_line_ending_preservation(tmp_path):
    crlf_file = tmp_path / "crlf_target.py"
    crlf_file.write_bytes(b"def foo():\r\n    return 1\r\n")

    lf_file = tmp_path / "lf_target.py"
    lf_file.write_bytes(b"def bar():\n    return 1\n")

    diff_crlf = "--- a/crlf_target.py\n+++ b/crlf_target.py\n@@ -1,2 +1,2 @@\n def foo():\n-    return 1\n+    return 2\n"
    diff_lf = "--- a/lf_target.py\n+++ b/lf_target.py\n@@ -1,2 +1,2 @@\n def bar():\n-    return 1\n+    return 2\n"

    ok1, msg1 = apply_patch(str(tmp_path), diff_crlf)
    ok2, msg2 = apply_patch(str(tmp_path), diff_lf)
    assert ok1 and ok2, f"{msg1}; {msg2}"

    assert b"\r\n" in crlf_file.read_bytes()
    assert b"\r\n" not in lf_file.read_bytes()


def test_classify_and_record_apply_failure(tmp_path):
    from src.tools.patch_engine import classify_apply_failure, record_apply_failure

    assert classify_apply_failure("fatal: corrupt patch at line 42") == "malformed_hunk"
    assert classify_apply_failure("error: file does not exist") == "wrong_path"
    assert classify_apply_failure("error: patch does not apply: context mismatch") == "context_mismatch"
    assert classify_apply_failure("error: whitespace error in line 10") == "whitespace"

    cause = record_apply_failure("test__repo-1234", 1, 0, "dummy diff", "context mismatch at hunk 1")
    assert cause == "context_mismatch"

