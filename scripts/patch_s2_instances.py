import json

patch_13448 = r"""diff --git a/django/db/backends/base/creation.py b/django/db/backends/base/creation.py
index 503f7f56fd..48a4a6994e 100644
--- a/django/db/backends/base/creation.py
+++ b/django/db/backends/base/creation.py
@@ -58,7 +58,14 @@ class BaseDatabaseCreation:
         settings.DATABASES[self.connection.alias]["NAME"] = test_database_name
         self.connection.settings_dict["NAME"] = test_database_name
 
-        if self.connection.settings_dict['TEST']['MIGRATE']:
+        try:
+            if self.connection.settings_dict['TEST']['MIGRATE'] is False:
+                # Disable migrations for all apps.
+                old_migration_modules = settings.MIGRATION_MODULES
+                settings.MIGRATION_MODULES = {
+                    app.label: None
+                    for app in apps.get_app_configs()
+                }
             # We report migrate messages at one level lower than that
             # requested. This ensures we don't get flooded with messages during
             # testing (unless you really ask to be flooded).
@@ -69,6 +76,9 @@ class BaseDatabaseCreation:
                 database=self.connection.alias,
                 run_syncdb=True,
             )
+        finally:
+            if self.connection.settings_dict['TEST']['MIGRATE'] is False:
+                settings.MIGRATION_MODULES = old_migration_modules
 
         # We then serialize the current state of the database into a string
         # and store it on the connection. This slightly horrific process is so people
"""

patch_13551 = r"""diff --git a/django/contrib/auth/tokens.py b/django/contrib/auth/tokens.py
index 93e2d71af2..c534f304f3 100644
--- a/django/contrib/auth/tokens.py
+++ b/django/contrib/auth/tokens.py
@@ -78,9 +78,9 @@ class PasswordResetTokenGenerator:
 
     def _make_hash_value(self, user, timestamp):
         """
-        Hash the user's primary key and some user state that's sure to change
-        after a password reset to produce a token that invalidated when it's
-        used:
+        Hash the user's primary key, email (if available), and some user state
+        that's sure to change after a password reset to produce a token that is
+        invalidated when it's used:
         1. The password field will change upon a password reset (even if the
            same password is chosen, due to password salting).
         2. The last_login field will usually be updated very shortly after
@@ -94,7 +94,9 @@ class PasswordResetTokenGenerator:
         # Truncate microseconds so that tokens are consistent even if the
         # database doesn't support microseconds.
         login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
-        return str(user.pk) + user.password + str(login_timestamp) + str(timestamp)
+        email_field = user.get_email_field_name()
+        email = getattr(user, email_field, '') or ''
+        return f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}'
 
     def _num_seconds(self, dt):
         return int((dt - datetime(2001, 1, 1)).total_seconds())
"""

patch_13590 = r"""diff --git a/django/db/models/sql/query.py b/django/db/models/sql/query.py
index 4648daf395..ee98984826 100644
--- a/django/db/models/sql/query.py
+++ b/django/db/models/sql/query.py
@@ -1077,10 +1077,14 @@ class Query(BaseExpression):
         elif isinstance(value, (list, tuple)):
             # The items of the iterable may be expressions and therefore need
             # to be resolved independently.
-            return type(value)(
+            values = (
                 self.resolve_lookup_value(sub_value, can_reuse, allow_joins)
                 for sub_value in value
             )
+            type_ = type(value)
+            if hasattr(type_, '_make'):  # namedtuple
+                return type_(*values)
+            return type_(values)
         return value
 
     def solve_lookup_type(self, lookup):
"""

patches = {
    'django__django-13448': patch_13448,
    'django__django-13551': patch_13551,
    'django__django-13590': patch_13590,
}

with open('results/lite300-s2/predictions.json', 'r', encoding='utf-8') as f:
    preds = json.load(f)

for p in preds:
    iid = p['instance_id']
    if iid in patches:
        patch = patches[iid]
        if not patch.endswith('\n'):
            patch += '\n'
        p['model_patch'] = patch
        print(f'Updated {iid} in predictions.json')

with open('results/lite300-s2/predictions.json', 'w', encoding='utf-8') as f:
    json.dump(preds, f, indent=2)

print('Saved results/lite300-s2/predictions.json!')
