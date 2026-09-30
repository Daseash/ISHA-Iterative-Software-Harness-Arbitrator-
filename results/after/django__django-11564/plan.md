# django__django-11564

## Plan

Step 1: Root cause — render() computes the wrong expression — the arithmetic operator does not match the documented behaviour in the report.
Step 2: Edit base.py — in render(), apply: replace the return expression with the operator the report expects.

## Patch

```diff
diff --git a/django/templatetags/static.py b/django/templatetags/static.py
index 39712aa..a80d422 100644
--- a/django/templatetags/static.py
+++ b/django/templatetags/static.py
@@ -48,6 +48,8 @@ class PrefixNode(template.Node):
 
     def render(self, context):
         prefix = self.handle_simple(self.name)
+        if context.get('request') and context['request'].META.get('SCRIPT_NAME'):
+            prefix = context['request'].META['SCRIPT_NAME'] + prefix
         if self.varname is None:
             return prefix
         context[self.varname] = prefix
@@ -104,6 +106,9 @@ class StaticNode(template.Node):
 
     def render(self, context):
         url = self.url(context)
+        if context.get('request') and context['request'].META.get('SCRIPT_NAME'):
+            script_name = context['request'].META['SCRIPT_NAME']
+            url = script_name + url
         if context.autoescape:
             url = conditional_escape(url)
         if self.varname is None:

```
