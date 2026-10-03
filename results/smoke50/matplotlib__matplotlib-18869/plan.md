# matplotlib__matplotlib-18869

## Plan

def __getattr__(name):
       if name == "__version__":
           # existing logic …
           return __version__
       elif name == "version_info":
           # Ensure __version__ is cached (reuse the logic above)
           if "__version__" not in globals():
               # Populate __version__ using the same code path
               # (duplicate the block that computes __version__)
               import setuptools_scm
               root = Path(__file__).resolve().parents[2]
               if (root / ".git").exists() and not (root / ".git/shallow").exists():
                   __version__ = setuptools_scm.get_version(
                       root=root,
                       version_scheme="post-release",
                       local_scheme="node-and-date",
                       fallback_version=_version.version,
                   )
               else:
                   __version__ = _version.version
               globals()["__version__"] = __version__
           # Parse the version string into a comparable tuple
           parsed = parse_version(__version__)          # already imported
           version_info = parsed.release                # e.g. (3, 9, 2)
           globals()["version_info"] = version_info
           return version_info
       raise AttributeError(...)

## Patch

```diff
diff --git a/lib/matplotlib/__init__.py b/lib/matplotlib/__init__.py
index b657a35..095993e 100644
--- a/lib/matplotlib/__init__.py
+++ b/lib/matplotlib/__init__.py
@@ -148,6 +148,14 @@ def __getattr__(name):
         else:  # Get the version from the _version.py setuptools_scm file.
             __version__ = _version.version
         return __version__
+    elif name == "version_info":
+        # Ensure __version__ is cached
+        if "__version__" not in globals():
+            __getattr__("__version__")
+        parsed = parse_version(globals()["__version__"])
+        version_info = parsed.release
+        globals()["version_info"] = version_info
+        return version_info
     raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
 
 

```
