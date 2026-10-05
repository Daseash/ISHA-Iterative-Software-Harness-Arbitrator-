# django__django-11620

## Plan

except (ValueError, Http404):

## Patch

```diff
diff --git a/django/urls/resolvers.py b/django/urls/resolvers.py
index 2154a46..e18686e 100644
--- a/django/urls/resolvers.py
+++ b/django/urls/resolvers.py
@@ -25,6 +25,7 @@ from django.utils.translation import get_language
 
 from .converters import get_converter
 from .exceptions import NoReverseMatch, Resolver404
+from django.http import Http404
 from .utils import get_callable
 
 
@@ -258,7 +259,7 @@ class RoutePattern(CheckURLMixin):
                 converter = self.converters[key]
                 try:
                     kwargs[key] = converter.to_python(value)
-                except ValueError:
+                except (ValueError, Http404):
                     return None
             return path[match.end():], (), kwargs
         return None

```
