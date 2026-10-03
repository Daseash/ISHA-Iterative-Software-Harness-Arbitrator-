# pallets__flask-4045

## Plan

Step 1: Root cause — github_link() does not match the behaviour described in the report.
Step 2: Edit conf.py — in github_link(), apply: make the return value match the documented behaviour.

## Patch

```diff
diff --git a/src/flask/blueprints.py b/src/flask/blueprints.py
index 5fb84d8..83c8cca 100644
--- a/src/flask/blueprints.py
+++ b/src/flask/blueprints.py
@@ -188,6 +188,10 @@ class Blueprint(Scaffold):
             template_folder=template_folder,
             root_path=root_path,
         )
+        if "." in name:
+            raise ValueError(
+                f"Blueprint name {name!r} cannot contain '.'; it is used for nested blueprints."
+            )
         self.name = name
         self.url_prefix = url_prefix
         self.subdomain = subdomain

```
