# django__django-11422

## Plan

class AutoReloader:
        def __init__(self, callable, reloader_cls, search_paths=None):
            self.callable = callable
            self.reloader_cls = reloader_cls
            self.search_paths = search_paths

## Patch

```diff
diff --git a/django/utils/autoreload.py b/django/utils/autoreload.py
index 7ca0d68..bfaa42f 100644
--- a/django/utils/autoreload.py
+++ b/django/utils/autoreload.py
@@ -79,6 +79,13 @@ def raise_last_exception():
 
 def ensure_echo_on():
     """
+    for module in tuple(sys.modules):
+        if (
+            not module.startswith('__frozen')
+            and hasattr(sys.modules[module], '__file__')
+            and sys.modules[module].__file__
+        ):
+            yield os.path.normcase(sys.modules[module].__file__)
     Ensure that echo mode is enabled. Some tools such as PDB disable
     it which causes usability issues after reload.
     """

```
