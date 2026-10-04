# django__django-11583

## Plan

@@
-    for filename in itertools.chain(sys_file_paths, extra_files):
-        if not filename:
-            continue
-        path = Path(filename)
-        try:
-            resolved_path = path.resolve(strict=True).absolute()
-        except FileNotFoundError:
-            # The module could have been removed, don't fail loudly if this
-            # is the case.
-            continue
-        results.add(resolved_path)
+    for filename in itertools.chain(sys_file_paths, extra_files):
+        # Skip empty entries.
+        if not filename:
+            continue
+        # Guard against paths that contain an embedded null byte.  pathlib
+        # cannot handle such strings and raises ValueError when we try to
+        # resolve them.  These paths are not useful for watching anyway, so
+        # we simply ignore them.
+        if isinstance(filename, str) and '\0' in filename:
+            continue
+        path = Path(filename)
+        try:
+            # Resolve the path strictly; if the file has disappeared or the
+            # resolve fails for any OS‑level reason we just ignore it.
+            resolved_path = path.resolve(strict=True).absolute()
+        except (FileNotFoundError, OSError, ValueError):
+            # The module could have been removed, could be a broken symlink,
+            # or could contain an invalid byte sequence – don’t let this
+            # abort the reloader.
+            continue
+        results.add(resolved_path)

## Patch

```diff
diff --git a/django/utils/autoreload.py b/django/utils/autoreload.py
index 25c3b44..ad3b4ce 100644
--- a/django/utils/autoreload.py
+++ b/django/utils/autoreload.py
@@ -134,14 +134,24 @@ def iter_modules_and_files(modules, extra_files):
 
     results = set()
     for filename in itertools.chain(sys_file_paths, extra_files):
+        # Skip empty entries.
         if not filename:
             continue
+        # Guard against paths that contain an embedded null byte.  pathlib
+        # cannot handle such strings and raises ValueError when we try to
+        # resolve them. These paths are not useful for watching anyway, so
+        # we simply ignore them.
+        if isinstance(filename, str) and '\0' in filename:
+            continue
         path = Path(filename)
         try:
+            # Resolve the path strictly; if the file has disappeared or the
+            # resolve fails for any OS‑level reason we just ignore it.
             resolved_path = path.resolve(strict=True).absolute()
-        except FileNotFoundError:
-            # The module could have been removed, don't fail loudly if this
-            # is the case.
+        except (FileNotFoundError, OSError, ValueError):
+            # The module could have been removed, could be a broken symlink,
+            # or could contain an invalid byte sequence – don’t let this
+            # abort the reloader.
             continue
         results.add(resolved_path)
     return frozenset(results)

```
