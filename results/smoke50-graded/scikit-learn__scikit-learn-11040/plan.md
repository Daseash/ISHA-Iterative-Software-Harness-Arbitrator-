# scikit-learn__scikit-learn-11040

## Plan

Step 1: The root cause
The `NearestNeighbors` estimator (and its `kneighbors` method) expects the `n_neighbors` parameter to be an integer because it is passed directly into C-level code (`KDTree` / `BallTree` / `NeighborsHeap`) that performs index calculations and memory allocation. When a float is passed (e.g., `3.0`), these underlying structures raise a `TypeError` because they expect an integer. The validation logic in `sklearn.neighbors` is not currently enforcing that `n_neighbors` be an integer, leading to this low-level exception instead of a user-friendly `ValueError`.

Step 2: Exact changes to make
I need to modify the `sklearn/neighbors/base.py` file, which contains the shared logic for neighbors-based estimators.

1.  **File:** `sklearn/neighbors/base.py`
    *   **In `NeighborsBase.__init__`**: Add a validation check for `n_neighbors`. If `n_neighbors` is provided, verify it is an integer. If it is a float that can be cast to an integer (e.g., `3.0`), cast it; otherwise, raise a `ValueError` with a helpful message.
    *   **In `KNeighborsMixin.kneighbors`**: Add similar validation for the `n_neighbors` parameter to ensure that if a user overrides the default at runtime, the provided value is also an integer.

    Specifically, use `isinstance(n_neighbors, numbers.Integral)` and perform a cast if necessary, or raise a `ValueError` explaining that `n_neighbors` must be an integer.

## Patch

```diff
diff --git a/sklearn/neighbors/base.py b/sklearn/neighbors/base.py
index 3e5e729..4ba50b0 100644
--- a/sklearn/neighbors/base.py
+++ b/sklearn/neighbors/base.py
@@ -8,6 +8,7 @@
 # License: BSD 3 clause (C) INRIA, University of Amsterdam
 import warnings
 from abc import ABCMeta, abstractmethod
+import numbers
 
 import numpy as np
 from scipy.sparse import csr_matrix, issparse
@@ -115,6 +116,10 @@ class NeighborsBase(six.with_metaclass(ABCMeta, BaseEstimator)):
         self.metric_params = metric_params
         self.p = p
         self.n_jobs = n_jobs
+        if self.n_neighbors is not None:
+            if not isinstance(self.n_neighbors, numbers.Integral):
+                raise ValueError("n_neighbors must be an integer, got %s" %
+                                 type(self.n_neighbors))
         self._check_algorithm_metric()
 
     def _check_algorithm_metric(self):
@@ -327,6 +332,11 @@ class KNeighborsMixin(object):
 
         if n_neighbors is None:
             n_neighbors = self.n_neighbors
+        else:
+            if not isinstance(n_neighbors, numbers.Integral):
+                raise ValueError("n_neighbors must be an integer, got %s" %
+                                 type(n_neighbors))
+
 
         if X is not None:
             query_is_train = False

```
