# sympy__sympy-13043

## Plan

if separate:
        return [poly_dict[key] for key in sorted(poly_dict.keys())]

## Patch

```diff
diff --git a/sympy/integrals/intpoly.py b/sympy/integrals/intpoly.py
index fc72bd2..e1ffc57 100644
--- a/sympy/integrals/intpoly.py
+++ b/sympy/integrals/intpoly.py
@@ -593,7 +593,7 @@ def decompose(expr, separate=False):
         poly_dict[0] = expr
 
     if separate:
-        return list(poly_dict.values())
+        return [poly_dict[key] for key in sorted(poly_dict.keys())]
     return poly_dict
 
 

```
