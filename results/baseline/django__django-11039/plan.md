# django__django-11039

## Plan

**Step 1 – Root cause**
`django/core/management/commands/sqlmigrate.py` decides whether to wrap the generated SQL in a transaction by setting `self.output_transaction` (or a local variable) to `migration.atomic`.
The decision ignores the database’s capability to roll back DDL. For back‑ends that cannot perform transactional DDL (`connection.features.can_rollback_ddl` is False) the command still prints `BEGIN; … COMMIT;`, which is incorrect and causes the failing test.

**Step 2 – Exact code change**

| File | Location | Change |
|------|----------|--------|
| `django/core/management/commands/sqlmigrate.py` | Inside `Command.handle` (after the migration object is retrieved, where `self.output_transaction` / `output_transaction` is assigned) | Replace the existing assignment that uses only `migration.atomic` with a conjunction that also checks the DB feature: <br><br>`self.output_transaction = migration.atomic` → `self.output_transaction = migration.atomic and connection.features.can_rollback_ddl` <br><br>If the code uses a local variable `output_transaction` instead of an attribute, apply the same change to that variable. No other modifications are required. |

*No change to public APIs or other files is needed; the single‑line fix makes the transaction wrapper respect both the migration’s atomic flag **and** the backend’s ability to roll back DDL.*

---

## Patch

```diff
diff --git a/django/core/management/commands/sqlmigrate.py b/django/core/management/commands/sqlmigrate.py
index f0b6632..9f6ff99 100644
--- a/django/core/management/commands/sqlmigrate.py
+++ b/django/core/management/commands/sqlmigrate.py
@@ -56,7 +56,9 @@ class Command(BaseCommand):
         targets = [(app_label, migration.name)]
 
         # Show begin/end around output only for atomic migrations
-        self.output_transaction = migration.atomic
+        # Only wrap the output in a transaction if the migration is atomic
+        # and the current database backend supports transactional DDL.
+        self.output_transaction = migration.atomic and connection.features.can_rollback_ddl
 
         # Make a plan that represents just the requested migrations and show SQL
         # for it

```
