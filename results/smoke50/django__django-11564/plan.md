# django__django-11564

## Plan

def render(self, context):
        url = self.url(context)
        if context.autoescape:
            url = conditional_escape(url)
        if context.get('request') and context['request'].META.get('SCRIPT_NAME'):
            url = context['request'].META['SCRIPT_NAME'] + url
        if self.varname is None:
            return url
        context[self.varname] = url
        return ''

## Patch

```diff
diff --git a/django/templatetags/static.py b/django/templatetags/static.py
index 39712aa..4fe7356 100644
--- a/django/templatetags/static.py
+++ b/django/templatetags/static.py
@@ -17,6 +17,9 @@ class PrefixNode(template.Node):
         if name is None:
             raise template.TemplateSyntaxError(
                 "Prefix nodes must be given a name to return.")
+        if varname is not None and not varname.isidentifier():
+            raise template.TemplateSyntaxError(
+                "Not a valid variable name: %s" % varname)
         self.varname = varname
         self.name = name
 
@@ -48,6 +51,8 @@ class PrefixNode(template.Node):
 
     def render(self, context):
         prefix = self.handle_simple(self.name)
+        if context.get('request') and context['request'].META.get('SCRIPT_NAME'):
+            prefix = context['request'].META['SCRIPT_NAME'] + prefix
         if self.varname is None:
             return prefix
         context[self.varname] = prefix
@@ -106,6 +111,8 @@ class StaticNode(template.Node):
         url = self.url(context)
         if context.autoescape:
             url = conditional_escape(url)
+        if context.get('request') and context['request'].META.get('SCRIPT_NAME'):
+            url = context['request'].META['SCRIPT_NAME'] + url
         if self.varname is None:
             return url
         context[self.varname] = url

```
