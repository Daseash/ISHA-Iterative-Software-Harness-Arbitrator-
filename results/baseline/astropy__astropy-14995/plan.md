# astropy__astropy-14995

## Plan

# Correction logic inside arithmetic method
    if self.mask is None and operand.mask is None:
        result_mask = None
    elif operand.mask is None:
        result_mask = self.mask
    elif self.mask is None:
        result_mask = operand.mask
    else:
        result_mask = handle_mask(self.mask, operand.mask)

## Patch

```diff

```
