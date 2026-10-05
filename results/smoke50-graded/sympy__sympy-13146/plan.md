# sympy__sympy-13146

## Plan

import sympy
from sympy import *
x = Symbol('x')
expr1 = S(1)/2*x**2.5
expr2 = S(1)*x**(S(5)/2)/2
res = simplify(expr1 - expr2) # Simplify symbolically first
print(res.evalf(5))          # Then evaluate numerically

## Patch

```diff
diff --git a/sympy/simplify/simplify.py b/sympy/simplify/simplify.py
index f1609aa..6eb62f9 100644
--- a/sympy/simplify/simplify.py
+++ b/sympy/simplify/simplify.py
@@ -483,6 +483,9 @@ def simplify(expr, ratio=1.7, measure=count_ops, fu=False):
     >>> print(count_ops(h, visual=True))
     2*LOG + MUL + POW + SUB
 
+    # Simplify the expression to handle floating point exponents
+    expr = powsimp(expr, combine='exp', deep=True)
+
     >>> from sympy import Symbol, S
     >>> def my_measure(expr):
     ...     POW = Symbol('POW')

```
