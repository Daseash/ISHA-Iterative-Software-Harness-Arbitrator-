# sympy__sympy-11400

## Plan

def _print_sinc(self, expr):
         from sympy import Piecewise, sin, Ne
         x = expr.args[0]
         return self._print(Piecewise((sin(x)/x, Ne(x, 0)), (1, True)))

## Patch

```diff
diff --git a/sympy/printing/ccode.py b/sympy/printing/ccode.py
index 30a07a7..109f67c 100644
--- a/sympy/printing/ccode.py
+++ b/sympy/printing/ccode.py
@@ -231,6 +231,11 @@ def _print_Symbol(self, expr):
         else:
             return name
 
+    def _print_sinc(self, expr):
+        from sympy import Piecewise, sin, Ne
+        x = expr.args[0]
+        return self._print(Piecewise((sin(x)/x, Ne(x, 0)), (1, True)))
+
     def _print_AugmentedAssignment(self, expr):
         lhs_code = self._print(expr.lhs)
         op = expr.rel_op

```
