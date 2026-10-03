# matplotlib__matplotlib-22835

## Plan

-        if np.ndim(data) == 0 and isinstance(self, ScalarMappable):
-            neighbors = self.norm.inverse(
-                np.array([data - 0.5, data + 0.5]))
-            if neighbors is not None:
+        if np.ndim(data) == 0 and isinstance(self, ScalarMappable):
+            # Some norm objects (e.g. BoundaryNorm) are not invertible.
+            # Catch the ValueError/AttributeError so the cursor does not
+            # crash the interaction.  When the inverse is unavailable,
+            # we simply skip the neighbor‑based tooltip logic.
+            try:
+                neighbors = self.norm.inverse(
+                    np.array([data - 0.5, data + 0.5]))
+            except (ValueError, AttributeError):
+                neighbors = None
+            if neighbors is not None:
                 # Determine the neighboring values
                 # (the logic below will be used in the tooltip)
                 ...

## Patch

```diff

```
