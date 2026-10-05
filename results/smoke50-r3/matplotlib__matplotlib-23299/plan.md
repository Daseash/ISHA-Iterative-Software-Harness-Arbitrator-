# matplotlib__matplotlib-23299

## Plan

@@
-def get_backend():
-    """
-    Return the name of the current backend.
-    """
-    from matplotlib import rcParams, rcsetup
-    backend = rcParams["backend"]
-    if backend is None:
-        backend = rcsetup.defaultBackend
-    # Import the backend module to ensure it is loaded.
-    import importlib
-    importlib.import_module(f"matplotlib.backends.backend_{backend}")
-    return backend
+def get_backend():
+    """
+    Return the name of the current backend.
+
+    The backend module is imported lazily and only once.  Importing the module
+    on every call caused the backend's initialization code to run repeatedly,
+    which clears the global figure manager (``Gcf.figs``) when a figure has
+    been created inside an ``rc_context``.  By guarding the import with a
+    ``sys.modules`` check we avoid the side‑effect while preserving the
+    historical behaviour that the backend is imported on first use.
+    """
+    from matplotlib import rcParams, rcsetup
+    import sys
+    import importlib
+
+    backend = rcParams["backend"]
+    if backend is None:
+        backend = rcsetup.defaultBackend
+
+    # Import the backend module only if it hasn't been imported yet.
+    module_name = f"matplotlib.backends.backend_{backend}"
+    if module_name not in sys.modules:
+        importlib.import_module(module_name)
+
+    return backend

## Patch

```diff
diff --git a/lib/matplotlib/__init__.py b/lib/matplotlib/__init__.py
index c268a56..3000d83 100644
--- a/lib/matplotlib/__init__.py
+++ b/lib/matplotlib/__init__.py
@@ -1133,6 +1133,7 @@ def use(backend, *, force=True):
     :ref:`backends`
     matplotlib.get_backend
     """
+
     name = validate_backend(backend)
     # don't (prematurely) resolve the "auto" backend setting
     if rcParams._get_backend_or_none() == name:

```
