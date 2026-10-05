# django__django-11630

## Plan

**Step 1 – Root cause**
Starting with Django 2.2 the system‑check framework added *models.E028* which validates that **every model in the project has a unique `db_table` name**. The check iterates over *all* registered models and flags a duplicate even when the models are routed to *different* databases. In a multi‑database project this behaviour is incorrect – tables with the same name may safely coexist on separate databases. The new check therefore raises the error that the bug report describes.

**Step 2 – Required code changes**

| File | Location | Change |
|------|----------|--------|
| `django/core/checks/model_checks.py` | import section | Add the needed imports: <br>`from django.conf import settings`<br>`from django.db import router` |
| `django/core/checks/model_checks.py` | `check_all_models` function (the part that builds `db_table_models`) | Replace the simple collection that only uses `model._meta.db_table` with a *database‑aware* collection:<br>```python\n    db_table_models = defaultdict(list)\n    for model in models:\n        db_table = model._meta.db_table\n        # Determine on which database(s) this model is allowed to migrate.\n        for alias in settings.DATABASES:\n            if router.allow_migrate(alias, model):\n                # key includes the database alias so the same table name on\n                # different databases is not considered a conflict.\n                db_table_models[(alias, db_table)].append(model)\n``` |
| `django/core/checks/model_checks.py` | `check_all_models` – error‑generation loop | Adjust the loop that creates the `Error` objects to use the new composite key and to show the conflicting models (the error text stays the same, only the condition changes). Example patch:<br>```python\n    for (alias, table), model_list in db_table_models.items():\n        if len(model_list) > 1:\n            model_names = ', '.join(f\"{m._meta.app_label}.{m.__name__}\" for m in model_list)\n            errors.append(\n                Error(\n                    f\"db_table '{table}' is used by multiple models on database '{alias}': {model_names}\",\n                    obj=model_list,\n                    id='models.E028',\n                )\n            )\n``` |
| `django/core/checks/model_checks.py` | (optional) keep the original `check_model_db_table_unique` if it exists | If the file also defines a separate `check_model_db_table_unique` function, apply the same database‑aware logic there (same imports, same per‑alias collection, same error generation). |

These modifications make the duplicate‑table check respect Django’s database routing, restoring the pre‑2.2 behaviour where identical table names are allowed as long as they belong to different databases. The fix touches only the single file `django/core/checks/model_checks.py`, keeping the public API unchanged and preserving all existing callers.

**Confidence:** 0.93

## Patch

```diff
diff --git a/django/core/checks/model_checks.py b/django/core/checks/model_checks.py
index 5c2266c..ba01c96 100644
--- a/django/core/checks/model_checks.py
+++ b/django/core/checks/model_checks.py
@@ -5,6 +5,8 @@ from itertools import chain
 
 from django.apps import apps
 from django.core.checks import Error, Tags, register
+from django.conf import settings
+from django.db import router
 
 
 @register(Tags.models)
@@ -19,7 +21,11 @@ def check_all_models(app_configs=None, **kwargs):
         models = chain.from_iterable(app_config.get_models() for app_config in app_configs)
     for model in models:
         if model._meta.managed and not model._meta.proxy:
-            db_table_models[model._meta.db_table].append(model._meta.label)
+            db_table = model._meta.db_table
+            # Determine on which database(s) this model is allowed to migrate.
+            for alias in settings.DATABASES:
+                if router.allow_migrate(alias, model):
+                    db_table_models[(alias, db_table)].append(model._meta.label)
         if not inspect.ismethod(model.check):
             errors.append(
                 Error(
@@ -35,12 +41,12 @@ def check_all_models(app_configs=None, **kwargs):
             indexes[model_index.name].append(model._meta.label)
         for model_constraint in model._meta.constraints:
             constraints[model_constraint.name].append(model._meta.label)
-    for db_table, model_labels in db_table_models.items():
+    for (alias, db_table), model_labels in db_table_models.items():
         if len(model_labels) != 1:
             errors.append(
                 Error(
-                    "db_table '%s' is used by multiple models: %s."
-                    % (db_table, ', '.join(db_table_models[db_table])),
+                    "db_table '%s' is used by multiple models on database '%s': %s."
+                    % (db_table, alias, ', '.join(model_labels)),
                     obj=db_table,
                     id='models.E028',
                 )

```
