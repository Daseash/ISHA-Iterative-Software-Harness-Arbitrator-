# sympy__sympy-13031

## Plan

Step 1: The root cause is that `Matrix.hstack` and `Matrix.vstack` in `sympy/matrices/matrices.py` filter out matrices that have 0 columns (for `hstack`) or 0 rows (for `vstack`) from the argument list before processing. This causes valid matrices with shape (0, N) or (M, 0) to be ignored, resulting in an incorrect final shape when the empty matrices are part of a concatenation that should contribute to the total dimension. Specifically, the filtering logic assumes that any matrix with a 0-dimension component is "empty" and can be discarded, which is incorrect when the other dimension is non-zero.

Step 2: Modify `sympy/matrices/matrices.py` in the `hstack` and `vstack` functions.
- In `hstack(self, *args)`: Change the line `args = [m for m in args if m.cols > 0]` to `args = [m for m in args if m.rows > 0 or m.cols > 0]`.
- In `vstack(self, *args)`: Change the line `args = [m for m in args if m.rows > 0]` to `args = [m for m in args if m.rows > 0 or m.cols > 0]`.

This ensures that matrices that contribute to the dimensions (even if one dimension is 0) are kept for the concatenation logic.

## Patch

```diff

```
