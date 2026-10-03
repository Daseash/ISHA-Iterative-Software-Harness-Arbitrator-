# scikit-learn__scikit-learn-10508

## Plan

y = column_or_1d(y, warn=True)

        # Check if y is empty to avoid issues with np.unique dtype casting
        if len(y) == 0:
            return np.array([], dtype=self.classes_.dtype)

        classes = np.unique(y)
        if len(np.intersect1d(classes, self.classes_, assume_unique=True)) < len(classes):
            diff = np.setdiff1d(classes, self.classes_, assume_unique=True)
            raise ValueError(
                    "y contains previously unseen labels: %s" % str(diff))
        return np.searchsorted(self.classes_, y)

## Patch

```diff
diff --git a/sklearn/preprocessing/label.py b/sklearn/preprocessing/label.py
index 61b8d4a..0c64fa8 100644
--- a/sklearn/preprocessing/label.py
+++ b/sklearn/preprocessing/label.py
@@ -93,6 +93,10 @@ class LabelEncoder(BaseEstimator, TransformerMixin):
         self : returns an instance of self.
         """
         y = column_or_1d(y, warn=True)
+        # Check if y is empty to avoid issues with np.unique dtype casting
+        if len(y) == 0:
+            return np.array([], dtype=self.classes_.dtype)
+
         self.classes_ = np.unique(y)
         return self
 

```
