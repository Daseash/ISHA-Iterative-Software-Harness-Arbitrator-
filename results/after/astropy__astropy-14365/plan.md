# astropy__astropy-14365

## Plan

**Step 1 – Root cause**
`astropy/io/ascii/qdp.py` determines the type of each line with a regular‑expression that matches only the upper‑case command words (e.g. `READ`, `SET`, `NEW`, …). The pattern is compiled without any flag, so the match is case‑sensitive. Later the parser compares the extracted command string against literal upper‑case strings. Consequently a perfectly valid QDP file that uses lower‑case (or mixed‑case) commands is classified as “unrecognized line” and raises the `ValueError` shown in the bug report.

**Step 2 – Exact code changes**

| File | Location | Change |
|------|----------|--------|
| `astropy/io/ascii/qdp.py` | Definition of `_line_type` (around the compilation of `_line_type_re`) | Replace the compilation line<br>`_line_type_re = re.compile(_type_re)`<br>with<br>`_line_type_re = re.compile(_type_re, re.IGNORECASE)` |
| `astropy/io/ascii/qdp.py` | In `_get_tables_from_qdp_file` (the main parsing loop) where commands are inspected (e.g. `if command == 'READ':`, `elif command == 'SET':`, `elif command == 'NEW':`, etc.) | Change each comparison to be case‑insensitive, e.g.<br>`if command.upper() == 'READ':`<br>`elif command.upper() == 'SET':`<br>`elif command.upper() == 'NEW':`<br>and similarly for any other command checks (`SERR`, `PLOT`, `ERROR`, …). |
| `astropy/io/ascii/qdp.py` | Any place where the command token is used to select a parsing branch (including the handling of error specifications) | Ensure the token is normalised with `.upper()` before the `if/elif` chain, e.g.<br>`cmd = command.upper()`<br>`if cmd == 'READ': …` |

These modifications make the command recogniser case‑insensitive while leaving the rest of the QDP reader unchanged. No other modules need to be touched because the parser’s public interface and return values stay the same.

**Confidence:** 0.97

## Patch

```diff
diff --git a/astropy/io/ascii/qdp.py b/astropy/io/ascii/qdp.py
index 83a4f00..768beb0 100644
--- a/astropy/io/ascii/qdp.py
+++ b/astropy/io/ascii/qdp.py
@@ -68,7 +68,7 @@ def _line_type(line, delimiter=None):
     _new_re = rf"NO({sep}NO)+"
     _data_re = rf"({_decimal_re}|NO|[-+]?nan)({sep}({_decimal_re}|NO|[-+]?nan))*)"
     _type_re = rf"^\s*((?P<command>{_command_re})|(?P<new>{_new_re})|(?P<data>{_data_re})?\s*(\!(?P<comment>.*))?\s*$"
-    _line_type_re = re.compile(_type_re)
+    _line_type_re = re.compile(_type_re, re.IGNORECASE)
     line = line.strip()
     if not line:
         return "comment"

```
