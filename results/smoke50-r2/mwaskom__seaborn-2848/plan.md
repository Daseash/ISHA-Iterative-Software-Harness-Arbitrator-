# mwaskom__seaborn-2848

## Plan

if hue is not None and hue_order is not None:
         data = data[data[hue].isin(hue_order)]

## Patch

```diff
diff --git a/seaborn/_core/data.py b/seaborn/_core/data.py
index 9de8be5..6eac8a1 100644
--- a/seaborn/_core/data.py
+++ b/seaborn/_core/data.py
@@ -65,6 +65,9 @@ class PlotData:
         self.source_data = data
         self.source_vars = variables
 
+
+    def __post_init__(self):
+        pass
     def __contains__(self, key: str) -> bool:
         """Boolean check on whether a variable is defined in this dataset."""
         if self.frame is None:

```
