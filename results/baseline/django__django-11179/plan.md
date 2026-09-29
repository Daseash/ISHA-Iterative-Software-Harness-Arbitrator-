# django__django-11179

## Plan

# After the delete query executes successfully
            for model, obj in self.data.items():
                obj.pk = None

## Patch

```diff
diff --git a/django/db/models/deletion.py b/django/db/models/deletion.py
index 92fe4af..e135f7c 100644
--- a/django/db/models/deletion.py
+++ b/django/db/models/deletion.py
@@ -275,6 +275,8 @@ class Collector:
         if len(self.data) == 1 and len(instances) == 1:
             instance = list(instances)[0]
             if self.can_fast_delete(instance):
+                for model, obj in self.data.items():
+                    obj.pk = None
                 with transaction.mark_for_rollback_on_error():
                     count = sql.DeleteQuery(model).delete_batch([instance.pk], self.using)
                 return count, {model._meta.label: count}

```
