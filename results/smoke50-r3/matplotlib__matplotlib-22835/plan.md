# matplotlib__matplotlib-22835

## Plan

@@
-        if np.ndim(data) == 0 and isinstance(self, ScalarMappable):
-            # Get the colors for the neighboring values.
-            neighbors = self.norm.inverse(
-                np.array([data - 0.5, data + 0.5]))
-            if neighbors is not None:
-                # format the value using the neighbor colors …
+        if np.ndim(data) == 0 and isinstance(self, ScalarMappable):
+            # Get the colors for the neighboring values.
+            # Some norm objects (e.g. BoundaryNorm) are not invertible and
+            # raise a ValueError.  In that case we simply skip the neighbor
+            # colour lookup so that cursor formatting still works.
+            try:
+                neighbors = self.norm.inverse(
+                    np.array([data - 0.5, data + 0.5]))
+            except (ValueError, AttributeError):
+                neighbors = None
+            if neighbors is not None:
+                # format the value using the neighbor colors …

## Patch

```diff

```
