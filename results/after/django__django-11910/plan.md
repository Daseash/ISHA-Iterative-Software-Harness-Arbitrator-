# django__django-11910

## Plan

Step 1: Root cause — __init__() computes the wrong expression — the arithmetic operator does not match the documented behaviour in the report.
Step 2: Edit config.py — in __init__(), apply: replace the return expression with the operator the report expects.

## Patch

```diff
diff --git a/django/db/migrations/writer.py b/django/db/migrations/writer.py
index 4918261..8bec6ab 100644
--- a/django/db/migrations/writer.py
+++ b/django/db/migrations/writer.py
@@ -73,7 +73,8 @@ class OperationWriter:
 
         imports = set()
         name, args, kwargs = self.operation.deconstruct()
-        operation_args = get_func_args(self.operation.__init__)
+        # Exclude 'self' from the list of argument names returned by get_func_args
+        operation_args = get_func_args(self.operation.__init__)[1:]
 
         # See if this operation is in django.db.migrations. If it is,
         # We can just use the fact we already have that imported,

```
