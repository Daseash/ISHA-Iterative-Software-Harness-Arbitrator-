# astropy__astropy-12907

## Plan

def _separable(transform):
    if isinstance(transform, CompoundModel):
        if transform.oper == '&':
            mats = [_separable(item) for item in transform.operands]
            # handles the case where there is a nested compound model
            offset = 0
            for m in mats:
                if isinstance(m, list):
                    mats[mats.index(m)] = np.hstack(m)
            # ...

## Patch

```diff
diff --git a/astropy/modeling/separable.py b/astropy/modeling/separable.py
index a308e27..b07bbb6 100644
--- a/astropy/modeling/separable.py
+++ b/astropy/modeling/separable.py
@@ -132,6 +132,14 @@ def _arith_oper(left, right):
     Function corresponding to one of the arithmetic operators
     ['+', '-'. '*', '/', '**'].
 
+def _cstack_from_list(mats):
+    flat_mats = []
+    for mat in mats:
+        if isinstance(mat, list):
+            flat_mats.extend(mat)
+        else:
+            flat_mats.append(mat)
+    return np.hstack(flat_mats)
     This always returns a nonseparable output.
 
 

```
