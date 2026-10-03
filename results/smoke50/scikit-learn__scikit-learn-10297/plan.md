# scikit-learn__scikit-learn-10297

## Plan

Step 1: The root cause is that `RidgeClassifierCV` does not define a `store_cv_values` parameter in its `__init__` method, yet it inherits from `_BaseRidgeCV` which likely handles the logic for storing cross-validation values if the parameter is passed correctly. The class `RidgeClassifierCV` is missing this argument in its signature and it is not being passed to the `super().__init__` call.

Step 2: Modify `sklearn/linear_model/ridge.py`:
- In the `RidgeClassifierCV.__init__` method, add the argument `store_cv_values=False` to the function signature.
- Pass this `store_cv_values` argument to the `super(RidgeClassifierCV, self).__init__(...)` call to ensure it is properly initialized in the base class.

## Patch

```diff
diff --git a/sklearn/linear_model/ridge.py b/sklearn/linear_model/ridge.py
index 911c74a..02f23c2 100644
--- a/sklearn/linear_model/ridge.py
+++ b/sklearn/linear_model/ridge.py
@@ -1336,7 +1336,7 @@ class RidgeClassifierCV(LinearClassifierMixin, _BaseRidgeCV):
                  normalize=False, scoring=None, cv=None, class_weight=None):
         super(RidgeClassifierCV, self).__init__(
             alphas=alphas, fit_intercept=fit_intercept, normalize=normalize,
-            scoring=scoring, cv=cv)
+            scoring=scoring, cv=cv, store_cv_values=False)
         self.class_weight = class_weight
 
     def fit(self, X, y, sample_weight=None):

```
