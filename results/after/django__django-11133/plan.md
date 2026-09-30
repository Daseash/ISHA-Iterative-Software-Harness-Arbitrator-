# django__django-11133

## Plan

@content.setter
    def content(self, value):
        # Convert memoryview to bytes
        if isinstance(value, memoryview):
            value = value.tobytes()
            
        if isinstance(value, bytes):
            self._container = [value]
        elif isinstance(value, str):
            value = value.encode(self.charset)
            self._container = [value]
        else:
            # Assume an iterable of bytestrings.
            self._container = list(value)

## Patch

```diff
diff --git a/django/http/response.py b/django/http/response.py
index 6a84e19..ebbdfb0 100644
--- a/django/http/response.py
+++ b/django/http/response.py
@@ -308,6 +308,9 @@ class HttpResponse(HttpResponseBase):
 
     @content.setter
     def content(self, value):
+        # Convert memoryview to bytes
+        if isinstance(value, memoryview):
+            value = value.tobytes()
         # Consume iterators upon assignment to allow repeated iteration.
         if hasattr(value, '__iter__') and not isinstance(value, (bytes, str)):
             content = b''.join(self.make_bytes(chunk) for chunk in value)

```
