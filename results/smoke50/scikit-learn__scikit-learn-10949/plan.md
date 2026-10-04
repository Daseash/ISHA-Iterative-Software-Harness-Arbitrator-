# scikit-learn__scikit-learn-10949

## Plan

# Specifically in sklearn/utils/validation.py:
# Inside check_array, look for where array-likes are converted to np.ndarray.
# 1. Capture original dtype if hasattr(X, "dtype")
# 2. Perform the standard conversion to ensure it's an ndarray.
# 3. If warn_on_dtype is True and input_dtype != array.dtype, issue the warning.

## Patch

```diff
diff --git a/sklearn/utils/validation.py b/sklearn/utils/validation.py
index fe1f723..6652dae 100644
--- a/sklearn/utils/validation.py
+++ b/sklearn/utils/validation.py
@@ -429,6 +429,16 @@ def check_array(array, accept_sparse=False, accept_large_sparse=True,
         Make sure that the 2D array has some minimum number of features
         (columns). The default value of 1 rejects empty datasets.
         This check is only enforced when the input data has effectively 2
+        if warn_on_dtype and hasattr(array, 'dtype'):
+            input_dtype = array.dtype
+        else:
+            input_dtype = None
+
+
+        if warn_on_dtype and input_dtype is not None and \
+           input_dtype != array.dtype:
+            warnings.warn("Data with input dtype %s was converted to %s."
+                          % (input_dtype, array.dtype), DataConversionWarning)
         dimensions or is originally 1D and ``ensure_2d`` is True. Setting to 0
         disables this check.
 

```
