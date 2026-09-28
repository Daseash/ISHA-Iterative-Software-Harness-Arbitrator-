# django__django-10914

## Plan

Step 1: What is the root cause
The root cause is that Django's `FileSystemStorage.save()` method does not explicitly set the file permissions based on the `FILE_UPLOAD_PERMISSIONS` setting when moving or copying files from the temporary location to the final destination. Python's `tempfile` module creates temporary files with restrictive permissions (typically `0o600`) for security reasons. When these temporary files are moved (via `os.rename` or similar) to the final storage location, they retain these restrictive permissions unless explicitly changed. If the `FILE_UPLOAD_PERMISSIONS` setting is not defined in a project's settings, Django currently does not have a default value, leading to inconsistent file permissions depending on the upload handler (`TemporaryUploadedFile` vs `MemoryUploadedFile`) or system defaults. This results in uploaded files not having the expected standard permissions (e.g., readable by the web server user but writable by the owner, `0o644`).

Step 2: What exact changes to make
1. **File**: `django/core/files/storage.py`
   **Function**: `FileSystemStorage.__init__`
   **Change**: Add an attribute `self.file_permissions_mode = getattr(settings, 'FILE_UPLOAD_PERMISSIONS', 0o644)`. This sets the default permission to `0o644` if the setting is not provided, but allows user override.

2. **File**: `django/core/files/storage.py`
   **Function**: `FileSystemStorage.save`
   **Change**:
   - Locate the part of the `save` method where the file is finalized (after `fchunk` loop or `os.rename`/`shutil.move`).
   - Add a call to `os.chmod(os.path.abspath(name), self.file_permissions_mode)`.
   - Ensure this is done for both the "move" case (when using `TemporaryUploadedFile` which creates a temp file) and the "copy" case, though typically the temp file path is the main suspect for inheriting `0o600`. The standard Django fix for this ticket (#10914) specifically applied `os.chmod` to the final file path after saving if `self.file_permissions_mode` is set.

*Note: While the bug report mentions documentation issues, the primary code fix requested is the default behavior. The permission change must be applied within `FileSystemStorage` to ensure consistency.*

## Patch

```diff
diff --git a/django/core/files/storage.py b/django/core/files/storage.py
index cbdab1d..10beb66 100644
--- a/django/core/files/storage.py
+++ b/django/core/files/storage.py
@@ -181,6 +181,7 @@ class FileSystemStorage(Storage):
         self._base_url = base_url
         self._file_permissions_mode = file_permissions_mode
         self._directory_permissions_mode = directory_permissions_mode
+        self.file_permissions_mode = getattr(settings, 'FILE_UPLOAD_PERMISSIONS', 0o644)
         setting_changed.connect(self._clear_cached_properties)
 
     def _clear_cached_properties(self, setting, **kwargs):

```
