# sphinx-doc__sphinx-10325

## Plan

def inherited_members_option(arg: Any) -> Union[object, Set[str]]:
    """Used to convert the :inherited-members: option to auto directives."""
    if arg in (None, True):
        return {'object'}
    else:
        return {x.strip() for x in arg.split(',') if x.strip()}

## Patch

```diff
diff --git a/sphinx/ext/autodoc/__init__.py b/sphinx/ext/autodoc/__init__.py
index 62631f7..14478ff 100644
--- a/sphinx/ext/autodoc/__init__.py
+++ b/sphinx/ext/autodoc/__init__.py
@@ -99,7 +99,7 @@ def members_set_option(arg: Any) -> Union[object, Set[str]]:
                   RemovedInSphinx50Warning, stacklevel=2)
     if arg is None:
         return ALL
-    return {x.strip() for x in arg.split(',') if x.strip()}
+        return {x.strip() for x in arg.split(',') if x.strip()} | {'object'}
 
 
 def exclude_members_option(arg: Any) -> Union[object, Set[str]]:

```
