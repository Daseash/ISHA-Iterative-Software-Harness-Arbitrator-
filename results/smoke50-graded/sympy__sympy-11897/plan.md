# sympy__sympy-11897

## Plan

def _print_Pow(self, expr):
    p = expr.exp
    if p == S.Half:
        ...
    elif p == -S.Half:
        ...
    # ...
    if expr.base == E:
        # This is a special case for exp()
        # ...
        if p.is_negative:
            # Currently it converts exp(-x) to 1/e^x
            return self.doprint(1) + r"\left(" + self._print(expr.base**(-p)) + r"\right)"[-4:] # Pseudo-code

## Patch

```diff
diff --git a/sympy/printing/latex.py b/sympy/printing/latex.py
index 1edc712..0a4da41 100644
--- a/sympy/printing/latex.py
+++ b/sympy/printing/latex.py
@@ -1,4 +1,5 @@
 """
+
 A Printer which converts an expression into its LaTeX equivalent.
 """
 
@@ -295,6 +296,7 @@ def _print_Add(self, expr, order=None):
             elif _coeff_isneg(term):
                 tex += " - "
                 term = -term
+                term = -term
             else:
                 tex += " + "
             term_tex = self._print(term)

```
