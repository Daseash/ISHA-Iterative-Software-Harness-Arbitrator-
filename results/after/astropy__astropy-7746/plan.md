# astropy__astropy-7746

## Plan

if len(xy[0]) == 0:
        return [np.array([], dtype=np.float64) for _ in xy]

## Patch

```diff
diff --git a/astropy/wcs/wcs.py b/astropy/wcs/wcs.py
index d3a06f2..1608ae0 100644
--- a/astropy/wcs/wcs.py
+++ b/astropy/wcs/wcs.py
@@ -1222,6 +1222,8 @@ reduce these to 2 dimensions using the naxis kwarg.
 
             if ra_dec_order and sky == 'input':
                 xy = self._denormalize_sky(xy)
+            if len(xy[0]) == 0:
+                return [np.array([], dtype=np.float64) for _ in xy]
             output = func(xy, origin)
             if ra_dec_order and sky == 'output':
                 output = self._normalize_sky(output)

```
