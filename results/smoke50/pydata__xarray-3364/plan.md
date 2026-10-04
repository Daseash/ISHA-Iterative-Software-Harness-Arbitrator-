# pydata__xarray-3364

## Plan

### Step 1: Root Cause
The `xarray.concat` function currently forces all input objects to share the same variables. When datasets with different variables are provided, the internal logic (which uses standard concatenation) fails because it expects consistent shapes and variable sets across the objects being joined. Unlike `pandas.concat`, which handles mismatched columns by performing an outer join (filling missing values with `NaN`), `xarray.concat` does not provide an explicit mechanism to handle this discrepancy, forcing users to manually align datasets by padding them with `NaN` before concatenation.

### Step 2: Exact Changes
To support this, I will add an `ignore_missing_vars` parameter to `xarray.concat` (defaulting to `False` to maintain backward compatibility) and modify the `concat` logic to handle the variable alignment when this is set to `True`.

1.  **`xarray/core/concat.py`**:
    *   Update the signature of `concat` to include `ignore_missing_vars: bool = False`.
    *   Update the docstring to document the new parameter.
    *   Modify the internal logic (likely within the `Dataset` concatenation path) to identify the union of variables across all input datasets.
    *   For datasets missing a variable that exists in others, inject a `Variable` filled with `fill_value` (NaN) of the appropriate shape and coordinate structure before proceeding with the existing concatenation logic.

2.  **`xarray/core/dataset.py` (if necessary)**:
    *   Ensure that the `Dataset.concat` method accepts the new `ignore_missing_vars` keyword and passes it through to the core logic in `xarray/core/concat.py`.

## Patch

```diff
diff --git a/xarray/core/concat.py b/xarray/core/concat.py
index ecae256..6c78215 100644
--- a/xarray/core/concat.py
+++ b/xarray/core/concat.py
@@ -16,6 +16,7 @@ def concat(
     positions=None,
     fill_value=dtypes.NA,
     join="outer",
+    ignore_missing_vars=False,
 ):
     """Concatenate xarray objects along a new or existing dimension.
 
@@ -33,6 +34,8 @@ def concat(
         is used as the dimension to concatenate along and the values are added
         as a coordinate.
     data_vars : {'minimal', 'different', 'all' or list of str}, optional
+        ignore_missing_vars : bool, optional
+            If True, ignore variables that are missing in some datasets.
         These data variables will be concatenated together:
           * 'minimal': Only data variables in which the dimension already
             appears are included.
@@ -101,6 +104,18 @@ def concat(
     --------
     merge
     auto_combine
+        )
+    elif ignore_missing_vars:
+        from .dataset import Dataset
+
+        objs = list(objs)
+        names = set().union(*(obj.data_vars for obj in objs))
+        for i, obj in enumerate(objs):
+            missing = names - set(obj.data_vars)
+            if missing:
+                objs[i] = obj.assign({k: obj.get(k, fill_value) for k in missing})
+        return _dataset_concat(
+            objs, dim, data_vars, coords, compat, positions, fill_value, join
     """
     # TODO: add ignore_index arguments copied from pandas.concat
     # TODO: support concatenating scalar coordinates even if the concatenated

```
