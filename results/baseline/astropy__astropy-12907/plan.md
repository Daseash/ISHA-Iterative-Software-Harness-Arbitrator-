# astropy__astropy-12907

## Plan

-    separable_matrix = _separable(transform)
        -    is_separable = separable_matrix.sum(1)
        -    is_separable = np.where(is_separable != 1, False, True)
        +    separable_matrix = separability_matrix(transform)
        +    is_separable = separable_matrix.any(axis=1)

## Patch

```diff
diff --git a/astropy/modeling/separable.py b/astropy/modeling/separable.py
index a308e27..adc9e95 100644
--- a/astropy/modeling/separable.py
+++ b/astropy/modeling/separable.py
@@ -57,9 +57,8 @@ def is_separable(transform):
     if transform.n_inputs == 1 and transform.n_outputs > 1:
         is_separable = np.array([False] * transform.n_outputs).T
         return is_separable
-    separable_matrix = _separable(transform)
-    is_separable = separable_matrix.sum(1)
-    is_separable = np.where(is_separable != 1, False, True)
+    separable_matrix = separability_matrix(transform)
+    is_separable = separable_matrix.any(axis=1)
     return is_separable
 
 

```
