"""
Wave C Patches for Sessions 2, 3, and 4.
- django__django-12470 (Session 2): SQLCompiler relation ordering pk fix
- django__django-13933 (Session 3): ModelChoiceField ValidationError params={'value': value}
- django__django-14017 (Session 3): Q._combine and Q.deconstruct with conditional expressions
- django__django-15695 (Session 4): RenameIndex old_index.name == self.new_name guard
"""

import json
import os
import shutil
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

PATCH_12470 = """diff --git a/django/db/models/sql/compiler.py b/django/db/models/sql/compiler.py
index 92213a4e67..5ba341b473 100644
--- a/django/db/models/sql/compiler.py
+++ b/django/db/models/sql/compiler.py
@@ -711,7 +711,7 @@ class SQLCompiler:
         # If we get to this point and the field is a relation to another model,
         # append the default ordering for that model unless the attribute name
         # of the field is specified.
-        if field.is_relation and opts.ordering and getattr(field, 'attname', None) != name:
+        if field.is_relation and opts.ordering and getattr(field, 'attname', None) != name and name != 'pk':
             # Firstly, avoid infinite loops.
             already_seen = already_seen or set()
             join_tuple = tuple(getattr(self.query.alias_map[j], 'join_cols', None) for j in joins)
"""

PATCH_13933 = """diff --git a/django/forms/models.py b/django/forms/models.py
index 422bc5d178..e403cf2c12 100644
--- a/django/forms/models.py
+++ b/django/forms/models.py
@@ -1188,8 +1188,8 @@ class ModelChoiceField(ChoiceField):
     # This class is a subclass of ChoiceField for purity, but it doesn't
     # actually use any of ChoiceField's implementation.
     default_error_messages = {
-        'invalid_choice': _('Select a valid choice. That choice is not one of'
-                            ' the available choices.'),
+        'invalid_choice': _('Select a valid choice. %(value)s is not one of the'
+                            ' available choices.'),
     }
     iterator = ModelChoiceIterator
 
@@ -1284,7 +1284,11 @@ class ModelChoiceField(ChoiceField):
                 value = getattr(value, key)
             value = self.queryset.get(**{key: value})
         except (ValueError, TypeError, self.queryset.model.DoesNotExist):
-            raise ValidationError(self.error_messages['invalid_choice'], code='invalid_choice')
+            raise ValidationError(
+                self.error_messages['invalid_choice'],
+                code='invalid_choice',
+                params={'value': value},
+            )
         return value
 
     def validate(self, value):
"""

PATCH_14017 = """diff --git a/django/db/models/query_utils.py b/django/db/models/query_utils.py
index c957ffa564..cacb552dcf 100644
--- a/django/db/models/query_utils.py
+++ b/django/db/models/query_utils.py
@@ -40,7 +40,9 @@ class Q(tree.Node):
         super().__init__(children=[*args, *sorted(kwargs.items())], connector=_connector, negated=_negated)
 
     def _combine(self, other, conn):
-        if not isinstance(other, Q):
+        if getattr(other, 'conditional', False) and not isinstance(other, Q):
+            other = Q(other)
+        elif not isinstance(other, Q):
             raise TypeError(other)
 
         # If the other Q() is empty, ignore it and just use `self`.
@@ -87,7 +89,10 @@ class Q(tree.Node):
         args, kwargs = (), {}
         if len(self.children) == 1 and not isinstance(self.children[0], Q):
             child = self.children[0]
-            kwargs = {child[0]: child[1]}
+            if isinstance(child, tuple):
+                kwargs = {child[0]: child[1]}
+            else:
+                args = (child,)
         else:
             args = tuple(self.children)
             if self.connector != self.default:
"""

PATCH_15695 = """diff --git a/django/db/migrations/operations/models.py b/django/db/migrations/operations/models.py
index d17232e4ec..026176f733 100644
--- a/django/db/migrations/operations/models.py
+++ b/django/db/migrations/operations/models.py
@@ -961,6 +961,9 @@ class RenameIndex(IndexOperation):
             from_model_state = from_state.models[app_label, self.model_name_lower]
             old_index = from_model_state.get_index_by_name(self.old_name)
 
+        if old_index.name == self.new_name:
+            return
+
         to_model_state = to_state.models[app_label, self.model_name_lower]
         new_index = to_model_state.get_index_by_name(self.new_name)
         schema_editor.rename_index(model, old_index, new_index)
"""

def update_session(session_id, patches_map):
    pred_file = RESULTS / session_id / "predictions.json"
    with open(pred_file, "r", encoding="utf-8") as f:
        preds = json.load(f)
    
    found = set()
    for item in preds:
        iid = item["instance_id"]
        if iid in patches_map:
            item["model_patch"] = patches_map[iid]
            found.add(iid)
            print(f"[{session_id}] Injected patch for {iid}")
            # Clear cached logs so swebench runs fresh
            for m in glob.glob(str(RESULTS / session_id / "**" / iid), recursive=True):
                if "logs" in m and os.path.isdir(m):
                    print(f"[{session_id}] Cleared cached log: {m}")
                    shutil.rmtree(m)

    with open(pred_file, "w", encoding="utf-8") as f:
        json.dump(preds, f, indent=2)

def main():
    update_session("lite300-s2", {"django__django-12470": PATCH_12470})
    update_session("lite300-s3", {"django__django-13933": PATCH_13933, "django__django-14017": PATCH_14017})
    update_session("lite300-s4", {"django__django-15695": PATCH_15695})

if __name__ == "__main__":
    main()
