# django__django-11583

## Plan

@@
-def iter_modules_and_files(modules, error_files):
-    results = set()
-    for module in modules:
-        filename = getattr(module, '__file__', None)
-        if not filename:
-            continue
-        try:
-            path = Path(filename).resolve()
-        except OSError:
-            continue
-        results.add(path)
-    results.update(error_files)
-    return results
+def iter_modules_and_files(modules, error_files):
+    """
+    Return a set of ``Path`` objects for the given modules plus any previously
+    errored files.
+
+    Some module ``__file__`` values may contain an embedded null byte (for
+    example, modules loaded from zip archives or frozen modules). ``Path.resolve``
+    raises ``ValueError`` for such strings, which previously bubbled up and
+    crashed the autoreloader. We now treat those modules as unwatchable and
+    simply skip them.
+    """
+    results = set()
+    for module in modules:
+        filename = getattr(module, '__file__', None)
+        if not filename:
+            continue
+        try:
+            # ``Path.resolve`` can raise OSError or ValueError (embedded NUL).
+            path = Path(filename).resolve()
+        except (OSError, ValueError):
+            # If the path cannot be resolved, ignore this module – it cannot be
+            # watched reliably.
+            continue
+        results.add(path)
+    # ``error_files`` may contain string paths; normalise them to ``Path``.
+    results.update(Path(p) if not isinstance(p, Path) else p for p in error_files)
+    return results

## Patch

```diff

```
