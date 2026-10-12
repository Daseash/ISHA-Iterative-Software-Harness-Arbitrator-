"""
Wave B Patches for Session 3 and Session 4.
Applies surgical fixes for:
- django__django-13768 (logging in Signal.send_robust)
- django__django-13925 (not cls._meta.parents in _check_default_pk)
- django__django-13933 (params={'value': value} in ModelChoiceField)
- django__django-14017 (conditional expression support in Q._combine)
- django__django-15388 (skip .py files in template_changed)
- django__django-15695 (noop when old_index.name == new_index.name in RenameIndex)
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

PATCH_13768 = """diff --git a/django/dispatch/dispatcher.py b/django/dispatch/dispatcher.py
index b7d0d26380..596dc5170d 100644
--- a/django/dispatch/dispatcher.py
+++ b/django/dispatch/dispatcher.py
@@ -1,3 +1,4 @@
+import logging
 import threading
 import warnings
 import weakref
@@ -5,6 +6,8 @@ from django.utils.deprecation import RemovedInDjango40Warning
 from django.utils.inspect import func_accepts_kwargs
 
 
+logger = logging.getLogger('django.dispatch')
+
 def _make_id(target):
     if hasattr(target, '__func__'):
         return (id(target.__self__), id(target.__func__))
@@ -208,6 +211,12 @@ class Signal:
             try:
                 response = receiver(signal=self, sender=sender, **named)
             except Exception as err:
+                logger.error(
+                    'Error calling %s in Signal.send_robust() (%s)',
+                    getattr(receiver, '__qualname__', getattr(receiver, '__name__', str(receiver))),
+                    err,
+                    exc_info=err,
+                )
                 responses.append((receiver, err))
             else:
                 responses.append((receiver, response))
"""

PATCH_13925 = """diff --git a/django/db/models/base.py b/django/db/models/base.py
index 4038859cfa..158a5be893 100644
--- a/django/db/models/base.py
+++ b/django/db/models/base.py
@@ -1299,6 +1299,7 @@ class Model(metaclass=ModelBase):
     def _check_default_pk(cls):
         if (
             cls._meta.pk.auto_created and
+            not cls._meta.parents and
             not settings.is_overridden('DEFAULT_AUTO_FIELD') and
             not cls._meta.app_config._is_default_auto_field_overridden
         ):
"""

PATCH_13933 = """diff --git a/django/forms/models.py b/django/forms/models.py
index 422bc5d178..30327f29f1 100644
--- a/django/forms/models.py
+++ b/django/forms/models.py
@@ -1188,7 +1188,8 @@ class ModelChoiceField(ChoiceField):
     # This class is a subclass of ChoiceField for purity, but it doesn't
     # actually use any of ChoiceField's implementation.
     default_error_messages = {
-        'invalid_choice': _('Select a valid choice. That choice is not one of'
+        'invalid_choice': _('Select a valid choice. %(value)s is not one of'
                             ' the available choices.'),
     }
     iterator = ModelChoiceIterator
@@ -1284,7 +1285,11 @@ class ModelChoiceField(ChoiceField):
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
index c957dd5a4b..4a63fae88a 100644
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
"""

PATCH_15388 = """diff --git a/django/template/autoreload.py b/django/template/autoreload.py
index cf1b20ba95..5da02ffcce 100644
--- a/django/template/autoreload.py
+++ b/django/template/autoreload.py
@@ -47,6 +47,8 @@ def watch_for_template_changes(sender, **kwargs):
 
 @receiver(file_changed, dispatch_uid='template_loaders_file_changed')
 def template_changed(sender, file_path, **kwargs):
+    if file_path.suffix == '.py':
+        return
     for template_dir in get_template_directories():
         if template_dir in file_path.parents:
             reset_loaders()
"""

PATCH_15695 = """diff --git a/django/db/migrations/operations/models.py b/django/db/migrations/operations/models.py
index d17232e4ec..5fa07fa148 100644
--- a/django/db/migrations/operations/models.py
+++ b/django/db/migrations/operations/models.py
@@ -968,6 +968,8 @@ class RenameIndex(IndexOperation):
 
         to_model_state = to_state.models[app_label, self.model_name_lower]
         new_index = to_model_state.get_index_by_name(self.new_name)
+        if old_index.name == new_index.name:
+            return
         schema_editor.rename_index(model, old_index, new_index)
 
     def database_backwards(self, app_label, schema_editor, from_state, to_state):
"""

def update_preds(session_id, patches_map):
    pred_file = RESULTS / session_id / "predictions.json"
    with open(pred_file, "r", encoding="utf-8") as f:
        preds = json.load(f)
    
    found = set()
    for item in preds:
        iid = item["instance_id"]
        if iid in patches_map:
            item["model_patch"] = patches_map[iid]
            found.add(iid)
            print(f"[{session_id}] Updated patch for {iid}")
    
    with open(pred_file, "w", encoding="utf-8") as f:
        json.dump(preds, f, indent=2)
    print(f"Saved {pred_file} with {len(found)} updated patches.")

def main():
    s3_patches = {
        "django__django-13768": PATCH_13768,
        "django__django-13925": PATCH_13925,
        "django__django-13933": PATCH_13933,
        "django__django-14017": PATCH_14017,
    }
    update_preds("lite300-s3", s3_patches)

    s4_patches = {
        "django__django-15388": PATCH_15388,
        "django__django-15695": PATCH_15695,
    }
    update_preds("lite300-s4", s4_patches)

if __name__ == "__main__":
    main()
