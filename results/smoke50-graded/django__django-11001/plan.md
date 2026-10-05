# django__django-11001

## Plan

# We only get the order_by clause without the ASC/DESC part.
# Normalise whitespace so that multiline ORDER BY fragments are treated as a single line.
normalized_sql = ' '.join(sql.split())
without_ordering = self.ordering_parts.search(normalized_sql).group(1)

## Patch

```diff
diff --git a/django/db/models/sql/compiler.py b/django/db/models/sql/compiler.py
index 7649c39..7fe5bb9 100644
--- a/django/db/models/sql/compiler.py
+++ b/django/db/models/sql/compiler.py
@@ -353,7 +353,9 @@ class SQLCompiler:
             # not taken into account so we strip it. When this entire method
             # is refactored into expressions, then we can check each part as we
             # generate it.
-            without_ordering = self.ordering_parts.search(sql).group(1)
+            # Normalize whitespace to correctly match multiline ORDER BY clauses.
+            sql_normalized = ' '.join(sql.split())
+            without_ordering = self.ordering_parts.search(sql_normalized).group(1)
             params_hash = make_hashable(params)
             if (without_ordering, params_hash) in seen:
                 continue

```
