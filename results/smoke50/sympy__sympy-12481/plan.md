# sympy__sympy-12481

## Plan

if has_dups(flatten(args)):
    p = Permutation(args[0])
    for i in range(1, len(args)):
        p = p * Permutation(args[i])
    # Now set self properties based on the computed p
    self.size = p.size
    self._array_form = p._array_form
    return

## Patch

```diff

```
