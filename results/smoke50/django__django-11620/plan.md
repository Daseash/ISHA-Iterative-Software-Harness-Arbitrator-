# django__django-11620

## Plan

--- a/django/urls/resolvers.py
+++ b/django/urls/resolvers.py
@@
-from django.core.exceptions import ImproperlyConfigured, ViewDoesNotExist
+from django.core.exceptions import ImproperlyConfigured, ViewDoesNotExist
+from django.http import Http404                     # ← new import
@@
-        for converter, value in zip(self.pattern.converters, args):
-            try:
-                value = converter.to_python(value)
-            except ValueError:
-                return None
+        for converter, value in zip(self.pattern.converters, args):
+            try:
+                value = converter.to_python(value)
+            except (ValueError, Http404):   # ← also treat Http404 as non‑match
+                return None

## Patch

```diff

```
