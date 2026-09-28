# astropy__astropy-12907

## Plan

separable_matrix = _separable(transform)
    separable_matrix = np.where(separable_matrix != 0, True, False)
    if isinstance(transform, CompoundModel) and transform.op == '&':
        return separable_matrix
    return separable_matrix

## Patch

```diff

```
