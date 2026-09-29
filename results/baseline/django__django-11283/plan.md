# django__django-11283

## Plan

from django.db import migrations
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    def update_proxy_permissions(apps, schema_editor):
        for model in apps.get_models():
            if model._meta.proxy:
                ct = ContentType.objects.get_for_model(model)
                verbose_name = model._meta.verbose_name
                lowercase_verbose_name = verbose_name.lower()
                for action in ['add', 'change', 'delete']:
                    codename = f'{action}_{lowercase_verbose_name.replace(" ", "_")}'
                    Permission.objects.create(
                        codename=codename,
                        content_type=ct,
                        name=f'Can {action} {verbose_name}',
                    )

## Patch

```diff
diff --git a/django/contrib/auth/migrations/0011_update_proxy_permissions.py b/django/contrib/auth/migrations/0011_update_proxy_permissions.py
index 0e66649..c6d4d9b 100644
--- a/django/contrib/auth/migrations/0011_update_proxy_permissions.py
+++ b/django/contrib/auth/migrations/0011_update_proxy_permissions.py
@@ -4,6 +4,9 @@ from django.db.models import Q
 
 def update_proxy_model_permissions(apps, schema_editor, reverse=False):
     """
+    new_ct = ContentType.objects.filter(
+        app_label='auth', codename='u12',
+    ).first()
     Update the content_type of proxy model permissions to use the ContentType
     of the proxy model.
     """

```
