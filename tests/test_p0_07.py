"""P0-07: patch engine fail-closed (markers, partial, new-file, misplacement)."""

from src.tools.patch_engine import _locate_similar, apply_patch


def test_partial_apply_returns_false(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    good = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    bad = "diff --git a/missing.py b/missing.py\n--- a/missing.py\n+++ b/missing.py\n@@ -1 +1 @@\n-old\n+new\n"
    # Good file alone applies
    ok, _ = apply_patch(str(tmp_path), good)
    assert ok is True
    # Combined good+bad must be FAILURE (was True with warnings)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    ok2, msg2 = apply_patch(str(tmp_path), good + bad)
    assert ok2 is False
    assert "Partial" in msg2 or "Missing" in msg2


def test_new_file_created(tmp_path):
    diff = "diff --git a/new_mod.py b/new_mod.py\n--- /dev/null\n+++ b/new_mod.py\n@@ -0,0 +1 @@\n+VALUE = 42\n"
    ok, _ = apply_patch(str(tmp_path), diff)
    assert ok is True
    assert (tmp_path / "new_mod.py").is_file()
    assert "VALUE = 42" in (tmp_path / "new_mod.py").read_text(encoding="utf-8")


def test_locate_similar_requires_anchor():
    lines = [f"line {i}\n" for i in range(50)]
    # Block with no anchor resemblance must not place
    old_block = ["totally different content xyz\n", "another alien line qqq\n"]
    assert _locate_similar(lines, old_block, start=25) is None
