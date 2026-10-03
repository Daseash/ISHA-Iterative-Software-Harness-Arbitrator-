# django__django-11133

## Plan

@content.setter
    def content(self, value):
-        if isinstance(value, bytes):
-            self._container = [value]
-        elif isinstance(value, str):
-            value = value.encode(self.charset)
-            self._container = [value]
-        else:
-            # Existing fallback handling (e.g., iterable of bytes)
-            self._container = list(value)
+        # ---- NEW: handle memoryview objects ----
+        # PostgreSQL returns BinaryField data as a memoryview. Convert it to
+        # a plain bytes object so that HttpResponse stores the actual payload.
+        if isinstance(value, memoryview):
+            value = value.tobytes()
+
+        if isinstance(value, bytes):
+            # Raw bytes are stored unchanged.
+            self._container = [value]
+        elif isinstance(value, str):
+            # Text is encoded using the response charset.
+            value = value.encode(self.charset)
+            self._container = [value]
+        else:
+            # Preserve original behaviour for other iterable‑like values.
+            self._container = list(value)

## Patch

```diff

```
