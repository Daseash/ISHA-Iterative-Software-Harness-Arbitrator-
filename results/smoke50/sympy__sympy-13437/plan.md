# sympy__sympy-13437

## Plan

@classmethod
    def eval(cls, n, k=None):
        if n is S.Infinity:
            return S.Infinity
        # ... existing logic for evaluation ...

## Patch

```diff
diff --git a/sympy/functions/combinatorial/numbers.py b/sympy/functions/combinatorial/numbers.py
index 896729a..59c62c7 100644
--- a/sympy/functions/combinatorial/numbers.py
+++ b/sympy/functions/combinatorial/numbers.py
@@ -345,6 +345,8 @@ class bell(Function):
                 \left(\frac{x_2}{2!} \right)^{j_2} \dotsb
                 \left(\frac{x_{n-k+1}}{(n-k+1)!} \right) ^{j_{n-k+1}}.
 
+            return S.Infinity
+        if n is S.NegativeInfinity:
     * bell(n) gives the `n^{th}` Bell number, `B_n`.
     * bell(n, x) gives the `n^{th}` Bell polynomial, `B_n(x)`.
     * bell(n, k, (x1, x2, ...)) gives Bell polynomials of the second kind,

```
