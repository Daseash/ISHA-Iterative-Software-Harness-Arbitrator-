# django__django-11001

## Plan

Step 1: What is the root cause
The root cause resides in the `get_order_by` method within `django/db/models/sql/compiler.py`. When Django compiles the `ORDER BY` clause, it iterates through the ordering expressions and attempts to deduplicate them. It achieves this by using a regular expression (`self.ordering_parts`) to search for `ASC` or `DESC` keywords within the SQL string generated for each expression. If the `sql` string is multiline (common with `RawSQL` wrapper classes), Python's `re` module (which is case-sensitive and line-bound for `\n`) may fail to match the ordering keyword if it is appended on a new line or if the whitespace structure interferes with the pattern match logic intended to isolate the "without ordering" part. Consequently, `search()` returns `None`, or more likely as described in the report, the logic intended to strip the ordering direction fails or behaves unexpectedly for multiline input, leading to incorrect parsing of the "seen" SQL parts. Specifically, the report indicates that `self.ordering_parts.search(sql)` on multiline SQL results in capturing only the fragment containing `ASC`/`DESC` (e.g., `then 2 else 1 end)`) rather than the full clause, or fails to normalize the whitespace so that distinct multiline SQL strings appearing identical to the deduplication logic (or the same string appearing with slightly different whitespace) are mishandled. The specific failure mode described is that `ordering_parts.search` returns a group that, when used to identify the base SQL, doesn't correctly account for the multi-line nature, causing valid, distinct clauses to be marked as duplicates or malformed. However, looking closely at the bug report, the user says `search` returns strings like `'				 then 2 else 1 end)'`. This implies the regex matches the `ASC`/`DESC` part but the "without_ordering" extraction (group 1) is capturing the *entire* preceding text up to that point, including newlines and tabs. If two distinct `RawSQL` clauses end with similar structures or if the deduplication check (`if sql in seen`) is performed on the raw multiline string *before* normalization, or if the "seen" set contains these oddly formatted substrings, a collision occurs. The standard fix involves normalizing the SQL string (collapsing whitespace/newlines) before applying the regex or the deduplication check to ensure consistent comparison.

Step 2: What exact changes to make
File: `django/db/models/sql/compiler.py`
Function: `get_order_by`
Change:
1. Locate the line where the compiler searches for ordering parts within the generated SQL: `without_ordering = self.ordering_parts.search(sql).group(1)`.
2. Before applying the regex search, normalize the `sql` string to remove extra whitespace and newlines. This ensures that the regex behaves consistently regardless of whether the input SQL was single-line or multi-line `RawSQL`.
3. Replace the direct usage of `sql` in the search with a normalized version.
   - Add: `sql_normalized = ' '.join(sql.split())`
   - Change: `without_ordering = self.ordering_parts.search(sql).group(1)` to `without_ordering = self.ordering_parts.search(sql_normalized).group(1)`
4. Ensure the variable `without_ordering` (which represents the base SQL clause without the `ASC`/`DESC` direction) is then added to the `seen` set as normal. The normalization ensures that `seen` contains consistently formatted strings, preventing false positives for distinct multiline queries that might otherwise be conflated or causing the regex to fail/match incorrectly when trailing whitespace/newlines are present.

## Patch

```diff
diff --git a/django/db/models/sql/compiler.py b/django/db/models/sql/compiler.py
index 7649c39..d460040 100644
--- a/django/db/models/sql/compiler.py
+++ b/django/db/models/sql/compiler.py
@@ -366,7 +366,9 @@ class SQLCompiler:
         if self.query.distinct and not self.query.distinct_fields:
             select_sql = [t[1] for t in select]
             for expr, (sql, params, is_ref) in order_by:
-                without_ordering = self.ordering_parts.search(sql).group(1)
+                # Collapse multiline order expressions to a single line before deduplication.
+                sql_oneline = ' '.join(sql.splitlines())
+                without_ordering = self.ordering_parts.search(sql_oneline).group(1)
                 if not is_ref and (without_ordering, params) not in select_sql:
                     extra_select.append((expr, (without_ordering, params), None))
         return extra_select

```
