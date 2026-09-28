# django__django-11133

## Plan

@@
-        # Original handling (simplified)
-        if isinstance(content, bytes):
-            self._container = [content]
-        elif isinstance(content, str):
-            self._container = [content.encode(self.charset)]
-        elif hasattr(content, '__iter__'):
-            self._container = list(content)
-        else:
-            raise TypeError(...)
+        # New handling – recognise any object that supports the buffer
+        # protocol (bytes, bytearray, memoryview, etc.) as raw binary data.
+        # This mirrors the behaviour of ``bytes()`` on a memoryview.
+        if isinstance(content, (bytes, bytearray)):
+            # ``bytes`` already gives us the correct type; ``bytearray`` is
+            # converted to an immutable ``bytes`` instance.
+            self._container = [bytes(content)]
+        elif isinstance(content, memoryview):
+            # Convert the memoryview to bytes without copying more than needed.
+            self._container = [content.tobytes()]
+        elif isinstance(content, str):
+            # Encode text using the response charset.
+            self._container = [content.encode(self.charset)]
+        elif hasattr(content, '__iter__'):
+            # Fallback for an iterable of byte‑chunks.
+            self._container = list(content)
+        else:
+            raise TypeError(
+                "Content must be a string, bytes, bytearray, memoryview, or an "
+                "iterable yielding bytes."
+            )

## Patch

```diff

```
