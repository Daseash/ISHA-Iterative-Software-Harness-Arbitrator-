# django__django-11797

## Plan

elif self.group_by:
            clone.group_by = tuple(
                expr.resolve_expression(query, *args, **kwargs)
                for expr in self.group_by
            )

## Patch

```diff
diff --git a/django/db/models/sql/query.py b/django/db/models/sql/query.py
index 8e55bd0..43c320f 100644
--- a/django/db/models/sql/query.py
+++ b/django/db/models/sql/query.py
@@ -1022,6 +1022,13 @@ class Query(BaseExpression):
                 not self.distinct_fields and
                 not self.select_for_update):
             clone.clear_ordering(True)
+        if self.group_by is True:
+            pass
+        elif self.group_by:
+            clone.group_by = tuple(
+                expr.resolve_expression(query, *args, **kwargs)
+                for expr in self.group_by
+            )
         clone.where.resolve_expression(query, *args, **kwargs)
         for key, value in clone.annotations.items():
             resolved = value.resolve_expression(query, *args, **kwargs)

```
