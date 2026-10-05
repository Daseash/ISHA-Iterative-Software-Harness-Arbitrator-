# django__django-11099

## Plan

**Step 1 – Root cause**
`ASCIIUsernameValidator` and `UnicodeUsernameValidator` inherit from `RegexValidator` and define their pattern as `r'^[\w.@+-]+$'`. In Python regular expressions the metacharacter `$` matches the end of the string **or** the position just before a trailing newline. Consequently a username that ends with `\n` satisfies the pattern, allowing invalid usernames that contain a newline at the end.

**Step 2 – Fix (exact code changes)**

| File | Location | Change |
|------|----------|--------|
| `django/contrib/auth/validators.py` | class `ASCIIUsernameValidator` (line 9‑11) | Replace the `regex` definition with an anchored pattern that does **not** treat a trailing newline as a match: <br>```python\n-    regex = r'^[\\w.@+-]+$'\n+    # Use \\A and \\Z to anchor the pattern to the absolute start and end of the string.\n+    # Unlike ^/$, \\A/\\Z do not allow a trailing newline, preventing usernames like \"bob\\n\".\n+    regex = r'\\A[\\w.@+-]+\\Z'\n``` |
| `django/contrib/auth/validators.py` | class `UnicodeUsernameValidator` (line 18‑20) | Apply the same change: <br>```python\n-    regex = r'^[\\w.@+-]+$'\n+    # Use \\A and \\Z to anchor the pattern to the absolute start and end of the string.\n+    # This disallows a trailing newline in the username.\n+    regex = r'\\A[\\w.@+-]+\\Z'\n``` |

No other files need to be modified because the validators are only defined here; the rest of the code uses the `regex` attribute directly via `RegexValidator.__call__`. After this change the validators will reject usernames that end with a newline.

**CONFIDENCE:** 0.96

## Patch

```diff
diff --git a/django/contrib/auth/validators.py b/django/contrib/auth/validators.py
index b4878cf..030c845 100644
--- a/django/contrib/auth/validators.py
+++ b/django/contrib/auth/validators.py
@@ -7,7 +7,9 @@ from django.utils.translation import gettext_lazy as _
 
 @deconstructible
 class ASCIIUsernameValidator(validators.RegexValidator):
-    regex = r'^[\w.@+-]+$'
+    # Use \A and \Z to anchor the pattern to the absolute start and end of the string.
+    # Unlike ^/$, \A/\Z do not allow a trailing newline, preventing usernames like "bob\n".
+    regex = r'\A[\w.@+-]+\Z'
     message = _(
         'Enter a valid username. This value may contain only English letters, '
         'numbers, and @/./+/-/_ characters.'
@@ -17,7 +19,9 @@ class ASCIIUsernameValidator(validators.RegexValidator):
 
 @deconstructible
 class UnicodeUsernameValidator(validators.RegexValidator):
-    regex = r'^[\w.@+-]+$'
+    # Use \A and \Z to anchor the pattern to the absolute start and end of the string.
+    # This disallows a trailing newline in the username.
+    regex = r'\A[\w.@+-]+\Z'
     message = _(
         'Enter a valid username. This value may contain only letters, '
         'numbers, and @/./+/-/_ characters.'

```
