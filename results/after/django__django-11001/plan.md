# django__django-11001

## Plan

# Before:
without_ordering = self.ordering_parts.search(sql).group(1)

# After:
# Collapse multiline SQL into a single line to ensure the regex 
# identifies the full expression rather than just the final line.
normalized_sql = ' '.join(sql.split())
without_ordering = self.ordering_parts.search(normalized_sql).group(1)

## Patch

```diff
diff --git a/django/db/models/sql/compiler.py b/django/db/models/sql/compiler.py
index 7649c39..7ea5465 100644
--- a/django/db/models/sql/compiler.py
+++ b/django/db/models/sql/compiler.py
@@ -366,7 +366,8 @@ class SQLCompiler:
         if self.query.distinct and not self.query.distinct_fields:
             select_sql = [t[1] for t in select]
             for expr, (sql, params, is_ref) in order_by:
-                without_ordering = self.ordering_parts.search(sql).group(1)
+                normalized_sql = ' '.join(sql.split())
+                without_ordering = self.ordering_parts.search(normalized_sql).group(1)
                 if not is_ref and (without_ordering, params) not in select_sql:
                     extra_select.append((expr, (without_ordering, params), None))
         return extra_select

```
