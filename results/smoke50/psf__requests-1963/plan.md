# psf__requests-1963

## Plan

while resp.is_redirect:
            # We need to copy the *last* prepared request, not the original,
            # to ensure state changes (like method transitions) persist.
            prepared_request = resp.request.copy()

## Patch

```diff
diff --git a/requests/sessions.py b/requests/sessions.py
index 425db22..23d2563 100644
--- a/requests/sessions.py
+++ b/requests/sessions.py
@@ -88,7 +88,7 @@ class SessionRedirectMixin(object):
         i = 0
 
         while resp.is_redirect:
-            prepared_request = req.copy()
+            prepared_request = resp.request.copy()
 
             resp.content  # Consume socket so it can be released
 

```
