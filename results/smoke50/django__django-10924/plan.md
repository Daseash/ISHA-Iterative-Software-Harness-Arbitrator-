# django__django-10924

## Plan

if callable(self.path):
            self.path = self.path()

## Patch

```diff
diff --git a/django/db/models/fields/files.py b/django/db/models/fields/files.py
index 8f12e80..eba22b9 100644
--- a/django/db/models/fields/files.py
+++ b/django/db/models/fields/files.py
@@ -87,6 +87,8 @@ class FieldFile(File):
         self.name = self.storage.save(name, content, max_length=self.field.max_length)
         setattr(self.instance, self.field.name, self.name)
         self._committed = True
+        if callable(self.path):
+            self.path = self.path()
 
         # Save the object because it has changed, unless save is False
         if save:

```
