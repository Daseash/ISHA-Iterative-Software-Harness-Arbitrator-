# django__django-11039

## Plan

### Step 1: What is the root cause
The `sqlmigrate` management command incorrectly assumes that if a migration is marked as `atomic`, it should be wrapped in `BEGIN` and `COMMIT` SQL statements. However, wrapping migrations in a transaction is only valid if the underlying database backend supports transactional DDL (`connection.features.can_rollback_ddl`). Currently, `sqlmigrate` ignores this feature flag, leading to invalid SQL being generated for databases (like MySQL/MariaDB for certain operations) that do not support transactional schema changes.

### Step 2: What exact changes to make
1.  **Modify `django/core/management/commands/sqlmigrate.py`**:
    *   Update the logic assigning `self.output_transaction`. Change it from `self.output_transaction = migration.atomic` to `self.output_transaction = migration.atomic and connection.features.can_rollback_ddl`.

2.  **Modify `tests/migrations/test_commands.py`**:
    *   Add a test case that verifies the `sqlmigrate` output does not contain `BEGIN` and `COMMIT` when `migration.atomic` is `True` but `connection.features.can_rollback_ddl` is `False`.
    *   This test should use `unittest.mock.patch` to mock `connection.features.can_rollback_ddl` to `False` while running a command on an atomic migration.

## Patch

```diff
diff --git a/django/core/management/commands/sqlmigrate.py b/django/core/management/commands/sqlmigrate.py
index f0b6632..b51d173 100644
--- a/django/core/management/commands/sqlmigrate.py
+++ b/django/core/management/commands/sqlmigrate.py
@@ -56,7 +56,7 @@ class Command(BaseCommand):
         targets = [(app_label, migration.name)]
 
         # Show begin/end around output only for atomic migrations
-        self.output_transaction = migration.atomic
+        self.output_transaction = migration.atomic and connection.features.can_rollback_ddl
 
         # Make a plan that represents just the requested migrations and show SQL
         # for it

```
