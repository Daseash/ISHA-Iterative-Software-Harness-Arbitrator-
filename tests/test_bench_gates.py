"""Tests for the bench validity gates, failure categorisation and symbol
targeting.

These encode decisions that are easy to get silently wrong:

  * a whitespace-only diff passes apply + ast.parse + pyflakes, so without an
    explicit no-op check it reaches the official harness and scores 0 while
    looking perfectly valid,
  * an instance the runner never reached must not be reported as an
    ``api_failure``, because the release criteria gate on that number, and
  * issue text is prose, so identifier extraction must not treat a backticked
    sentence as a symbol name.
"""

import json
from pathlib import Path

from src.bench.classify import CATEGORIES, build_breakdown, classify_instance
from src.bench.gates import (
    _hunk_touched_lines,
    is_semantic_noop,
    noop_gate,
    rewrite_risk,
)
from src.tools.symbol_target import (
    report_identifiers,
    score_symbols,
    target_file,
)

# The exact patch astropy__astropy-14365 produced in the baseline run: it
# re-indented the line it was told to fix and changed nothing else.
WHITESPACE_NOOP = """diff --git a/astropy/io/ascii/qdp.py b/astropy/io/ascii/qdp.py
--- a/astropy/io/ascii/qdp.py
+++ b/astropy/io/ascii/qdp.py
@@ -1,3 +1,3 @@
-    if not line:
+        if not line:
"""

# Same shape as the no-op (1 add / 1 remove) but a real behavioural change.
REAL_ONE_LINE = """diff --git a/astropy/io/fits/fitsrec.py b/astropy/io/fits/fitsrec.py
--- a/astropy/io/fits/fitsrec.py
+++ b/astropy/io/fits/fitsrec.py
@@ -1261,3 +1261,3 @@
-            output_field.replace(encode_ascii('E'), encode_ascii('D'))
+            output_field = output_field.replace(encode_ascii('E'), encode_ascii('D'))
"""

COMMENT_ONLY = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,2 @@
-    x = 1
+    x = 1  # noqa
"""


def test_whitespace_only_diff_is_a_noop():
    assert is_semantic_noop(WHITESPACE_NOOP)
    gate = noop_gate(WHITESPACE_NOOP)
    assert not gate.ok
    assert "no-op" in gate.errors[0].lower()
    # A rejected no-op must not be mistaken for an empty patch.
    assert gate.added_lines == 1 and gate.removed_lines == 1


def test_comment_only_diff_is_a_noop():
    assert is_semantic_noop(COMMENT_ONLY)


def test_real_one_line_change_is_not_a_noop():
    # Guards against a gate that rejects every 1-add/1-remove diff, which
    # would be a false positive on perfectly good patches.
    assert not is_semantic_noop(REAL_ONE_LINE)
    assert noop_gate(REAL_ONE_LINE).ok


def test_add_only_diff_is_not_a_noop():
    add_only = """--- a/x.py
+++ b/x.py
@@ -1,2 +1,3 @@
     y = 2
+    z = 3
"""
    assert not is_semantic_noop(add_only)


def test_empty_patch_is_a_noop():
    assert is_semantic_noop("")


def test_unrun_instance_is_not_an_api_failure():
    # An instance with no meta.json at all: the runner never reached it.
    assert classify_instance({}, None, None, False) == "not_run"


def test_missing_meta_yields_not_run_in_breakdown(tmp_path=None):
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    (tmp / "a__b-1").mkdir(parents=True, exist_ok=True)
    (tmp / "a__b-2").mkdir(parents=True, exist_ok=True)
    (tmp / "a__b-2" / "meta.json").write_text(
        json.dumps({"instance_id": "a__b-2", "status": "done",
                    "model_patch": "--- a/x.py\n+++ b/x.py\n@@\n-a\n+b\n",
                    "attempts": 1, "model_log": []}),
        encoding="utf-8",
    )
    records = [{"instance_id": "a__b-1"}, {"instance_id": "a__b-2"}]
    out = build_breakdown(tmp, records, {"resolved_ids": []})
    by_id = {r["instance_id"]: r["category"] for r in out["rows"]}
    assert by_id["a__b-1"] == "not_run"
    assert out["counts"]["not_run"] == 1
    assert out["counts"]["api_failure"] == 0


def test_new_categories_are_registered():
    # report.py iterates CATEGORIES, so an unregistered bucket would be
    # silently dropped from the printed breakdown.
    for name in ("not_run", "harness_no_output", "api_failure"):
        assert name in CATEGORIES


# ── Symbol targeting ────────────────────────────────────────────────────────

SRC = '''
def entry_point(x):
    """Public entry the reporter calls."""
    return _helper(x)


def _helper(x):
    return x + 1


def _unrelated(y):
    return y
'''

OPERATOR_SRC = '''
# Maps operators to the function implementing each one.
_operators = {'&': _stack, '|': _other}


def _stack(left, right):
    return left


def _other(left, right):
    return left
'''


def _write(tmp_path, name, text):
    p = Path(tmp_path) / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_report_identifiers_ignores_prose_in_backticks():
    # Backticks in an issue are markdown far more often than code. Capturing
    # the whole sentence made every file look like it had a "symbol" called
    # "How to Reproduce".
    ids = report_identifiers(
        "It broke when I used `Table.read`. See `How to Reproduce` for details."
    )
    assert "read" in ids
    assert not any(" " in i for i in ids)
    assert "Reproduce" not in ids


def test_report_identifiers_from_dotted_paths():
    ids = report_identifiers("calling astropy.modeling.separability_matrix fails")
    assert "separability_matrix" in ids


def test_symbol_targeting_prefers_helper_over_entry_point():
    # The report names the entry point; the defect is the private helper it
    # delegates to. Ranking the entry point first is what produced the
    # astropy-12907 wrong-function patch.
    import tempfile

    tmp = tempfile.mkdtemp()
    _write(tmp, "mod.py", SRC)
    ranked = [r["symbol"] for r in score_symbols(
        tmp, "mod.py", "calling entry_point() gives the wrong answer")]
    assert ranked, "expected at least one ranked symbol"
    assert ranked[0] == "_helper", ranked


def test_symbol_targeting_finds_dict_valued_operator_binding():
    # '_stack' is never called directly - it is a dict value - so a call-graph
    # walk cannot reach it. This is the shape of astropy-12907's real fix.
    import tempfile

    tmp = tempfile.mkdtemp()
    _write(tmp, "ops.py", OPERATOR_SRC)
    issue = "nested compound models are not separable when combined with &"
    ranked = [r["symbol"] for r in score_symbols(tmp, "ops.py", issue)]
    # '_other' is the '|' branch and the report never touches '|', so it should
    # not be offered at all rather than being ranked below the right answer.
    assert ranked[0] == "_stack", ranked
    assert "_other" not in ranked


def test_target_file_shape_matches_localizer_targets():
    import tempfile

    tmp = tempfile.mkdtemp()
    _write(tmp, "mod.py", SRC)
    out = target_file(tmp, "mod.py", "entry_point() is wrong")
    assert out and out[0]["file"] == "mod.py"
    assert {"symbol", "score", "reason"} <= set(out[0])


def test_hunk_touched_lines_counts_removed_lines():
    # A '-' line still occupies a position in the new file. Skipping it made a
    # five-line rewrite look like a one-line change and disabled the risk check.
    patch = (
        "--- a/f.py\n"
        "+++ b/f.py\n"
        "@@ -10,5 +10,5 @@\n"
        " keep\n"
        "-old one\n"
        "-old two\n"
        "+new one\n"
        "+new two\n"
        " keep\n"
    )
    touched = _hunk_touched_lines(patch)
    assert len(touched["f.py"]) == 4, touched
    # 10 is context, 11/12 are the removed pair, 13/14 the added pair.
    assert {11, 12, 13, 14} <= touched["f.py"]


def test_rewrite_risk_flags_broad_rewrite():
    import tempfile

    body = "\n".join("    step%d = %d" % (i, i) for i in range(20))
    src = "def target(a, b):\n%s\n" % body
    tmp = tempfile.mkdtemp()
    _write(tmp, "big.py", src)

    replaced = "\n".join("-    step%d = %d" % (i, i) for i in range(15))
    added = "\n".join("+    step%d = %d + 1" % (i, i) for i in range(15))
    patch = "--- a/big.py\n+++ b/big.py\n@@ -1,21 +1,21 @@\n%s\n%s\n" % (
        replaced, added)
    warnings = rewrite_risk(tmp, patch)
    assert warnings, "a 15/20-line body rewrite should be flagged"
    assert "rewrite risk" in warnings[0]


def test_rewrite_risk_quiet_on_small_change():
    # A three-line edit inside a large function is normal, and flagging it
    # would train the coder to ignore the warning.
    import tempfile

    body = "\n".join("    step%d = %d" % (i, i) for i in range(20))
    src = "def target(a, b):\n%s\n" % body
    tmp = tempfile.mkdtemp()
    _write(tmp, "big.py", src)
    patch = "--- a/big.py\n+++ b/big.py\n@@ -1,21 +1,21 @@\n-    step0 = 0\n+    step0 = 1\n"
    assert rewrite_risk(tmp, patch) == []
