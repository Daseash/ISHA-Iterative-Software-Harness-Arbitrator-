"""P0-07: patch engine fail-closed (markers, partial, new-file, misplacement)."""

from src.agents.candidates import _hunk_excerpts
from src.tools.patch_engine import _locate_similar, apply_patch, diagnose_missing_removals


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


def test_diagnose_names_hallucinated_removal(tmp_path):
    (tmp_path / "m.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    hallu = (
        "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n"
        "@@ -1,2 +1,2 @@\n     def f():\n-    return text.replace('_', r'\\_')\n+    return 2\n"
    )
    hint = diagnose_missing_removals(str(tmp_path), hallu)
    assert "return text.replace" in hint
    assert "NOT found" in hint
    # Real lines produce no hint
    real = (
        "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n"
        "@@ -1,2 +1,2 @@\n     def f():\n-    return 1\n+    return 2\n"
    )
    assert diagnose_missing_removals(str(tmp_path), real) == ""


def test_hunk_excerpts_shows_real_file_lines(tmp_path):
    real = "\n".join(
        ["alpha line", "beta line", "gamma line", "def real_f():", "    return 7", "zeta line"]
    )
    (tmp_path / "m.py").write_text(real + "\n", encoding="utf-8")
    patch = (
        "diff --git a/m.py b/m.py\n--- a/m.py\n+++ b/m.py\n"
        "@@ -4,2 +4,2 @@\n-    return 1\n+    return 2\n"
    )
    out = _hunk_excerpts(str(tmp_path), patch)
    assert "def real_f():" in out
    assert "return 7" in out
    assert "m.py around real line 4" in out
    # Patch for a file that does not exist on disk yields no excerpt.
    ghost = patch.replace("m.py", "ghost.py")
    assert _hunk_excerpts(str(tmp_path), ghost) == ""
    # Empty patch is safe no-op.
    assert _hunk_excerpts(str(tmp_path), "") == ""
