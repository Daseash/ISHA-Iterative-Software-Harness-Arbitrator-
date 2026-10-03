# django__django-11179

## Plan

if self.can_fast_delete(specified_objects):
            # ... existing code to set self.fast_deletes ...
            self.fast_delete(specified_objects) 
            # ADD THIS:
            for model, instances in self.data.items():
                for obj in instances:
                    obj.pk = None
            self.fast_deletes = []
            return

## Patch

```diff
diff --git a/django/db/models/deletion.py b/django/db/models/deletion.py
index 92fe4af..759f030 100644
--- a/django/db/models/deletion.py
+++ b/django/db/models/deletion.py
@@ -280,6 +280,10 @@ class Collector:
                 return count, {model._meta.label: count}
 
         with transaction.atomic(using=self.using, savepoint=False):
+            for model, instances in self.data.items():
+                for obj in instances:
+                    obj.pk = None
+            self.fast_deletes = []
             # send pre_delete signals
             for model, obj in self.instances_with_model():
                 if not model._meta.auto_created:

```
