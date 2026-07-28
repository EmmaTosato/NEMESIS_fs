"""Pure lesion-deficit / FC-deficit prediction algorithms (Siegel et al. 2016).

Array-in/array-out, no I/O - src/pipeline/predict_deficit.py owns loading
matrices, joining participants.tsv, and writing output. Mirrors the
separation already used by reduction.py/clustering.py (see docs/dev/analysis.md).

Method, step by step, matching docs/knowledge/Siegel2016_Reproduction.md
("Experimental Procedures" -> "Multivariate Ridge Regression"):
1. PCA per feature type (lesion, FC), independently, retaining a fixed
   fraction of variance (95% in the paper) - pca_variance_retained.
2. Ridge regression with an outer leave-one-out loop; the regularization
   lambda is chosen, per outer fold, via an *inner* leave-one-out search over
   the training set only (never touching the held-out subject) - ridge_loocv.
3. Accuracy = squared Pearson correlation between observed and predicted
   scores (Siegel's r^2 - NOT sklearn.metrics.r2_score, a different
   quantity) - accuracy_r2.
4. Per-model significance via permutation test (shuffle y, refit, compare) -
   permutation_test.
5. Head-to-head lesion-vs-FC comparison via a paired Wilcoxon signed-rank
   test on squared prediction error - compare_lesion_fc.
6. Multiple-comparison correction across behavioral targets - benjamini_hochberg
   (hand-rolled: statsmodels is not a project dependency, and one well-known
   ~10-line algorithm doesn't justify adding it).
"""

from __future__ import annotations

import numpy as np
from scipy.stats import pearsonr, wilcoxon
from sklearn.decomposition import PCA
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import LeaveOneOut


def pca_variance_retained(X: np.ndarray, variance_retained: float) -> tuple[np.ndarray, PCA]:
    """Fit PCA retaining variance_retained fraction of variance; return (X_pca, fitted_pca).

    Fits sklearn.decomposition.PCA directly (n_components as a float ratio),
    not through src.analysis.reduction.pca_embed's registry - that one is
    wired for a fixed integer component count today
    (config/registry/params_reduction.json has no "n_components": 0.95 mode).
    The fitted PCA is returned so consensus ridge weights (computed in PCA
    space) can later be projected back into the original voxel/edge space
    via pca.components_.
    """
    if not 0.0 < variance_retained <= 1.0:
        raise ValueError(f"variance_retained must be in (0.0, 1.0], got {variance_retained!r}")
    fitted = PCA(n_components=variance_retained)
    X_pca = fitted.fit_transform(X)
    return X_pca, fitted


def ridge_loocv(X: np.ndarray, y: np.ndarray, lambda_grid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Outer leave-one-out ridge regression; lambda tuned per fold via an inner LOO search.

    Returns (y_pred, consensus_weights): y_pred[i] is the held-out prediction
    for subject i (never seen during that fold's fit or lambda selection),
    consensus_weights is the mean of every fold's fitted .coef_ (Siegel:
    "the weight matrix was averaged across all n leave-one-out loops").

    Raises ValueError if X/y have mismatched subject counts, or fewer than 3
    subjects (leave-one-out needs at least 2 remaining subjects to still form
    an inner train/validation split).

    scoring="neg_mean_squared_error" is passed explicitly to the inner
    RidgeCV: each *inner* LOO fold holds out exactly 1 sample, and RidgeCV's
    default scoring (R^2) is mathematically undefined for a single test point
    (undefined variance -> NaN, silently degenerate lambda selection). MSE is
    well-defined for a single point and matches Siegel's own description of
    this step ("lambda... that minimized leave-one-out prediction error").
    """
    if X.shape[0] != len(y):
        raise ValueError(f"X has {X.shape[0]} rows but y has {len(y)} values - must match")
    if X.shape[0] < 3:
        raise ValueError(f"ridge_loocv needs at least 3 subjects, got {X.shape[0]}")

    n = X.shape[0]
    y_pred = np.empty(n, dtype=float)
    weights = np.empty((n, X.shape[1]), dtype=float)
    for train_idx, test_idx in LeaveOneOut().split(X):
        model = RidgeCV(alphas=lambda_grid, cv=LeaveOneOut(), scoring="neg_mean_squared_error")
        model.fit(X[train_idx], y[train_idx])
        y_pred[test_idx] = model.predict(X[test_idx])
        weights[test_idx[0]] = model.coef_

    return y_pred, weights.mean(axis=0)


def accuracy_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Squared Pearson correlation between observed and predicted scores (Siegel's r^2).

    Deliberately not sklearn.metrics.r2_score - a different quantity (fraction
    of variance explained relative to a mean-only baseline, can be negative).
    """
    r, _ = pearsonr(y_true, y_pred)
    return float(r**2)


def permutation_test(
    X: np.ndarray, y: np.ndarray, lambda_grid: np.ndarray, n_permutations: int, rng: np.random.Generator
) -> float:
    """Empirical p-value: is the observed r^2 better than chance?

    Shuffles y (never X - the null hypothesis is "this behavioral score is
    unrelated to this subject's features", not "the features are random"),
    refits the full LOOCV loop each time, and compares against the observed
    r^2. Returns (1 + n_null_at_least_as_good) / (1 + n_permutations) - never
    exactly 0, since a p-value of 0 from a finite permutation count would be
    a claim about infinite resampling this procedure cannot actually support.
    """
    y_pred_observed, _ = ridge_loocv(X, y, lambda_grid)
    observed_r2 = accuracy_r2(y, y_pred_observed)

    n_at_least_as_good = 0
    for _ in range(n_permutations):
        y_shuffled = rng.permutation(y)
        y_pred_null, _ = ridge_loocv(X, y_shuffled, lambda_grid)
        if accuracy_r2(y_shuffled, y_pred_null) >= observed_r2:
            n_at_least_as_good += 1

    return (1 + n_at_least_as_good) / (1 + n_permutations)


def compare_lesion_fc(err_lesion: np.ndarray, err_fc: np.ndarray) -> tuple[float, float]:
    """Paired two-tailed Wilcoxon signed-rank test on squared prediction error.

    err_lesion/err_fc must be aligned (same subject at the same index) and
    already squared - Siegel: "Wilcoxon signed rank test of prediction errors"
    on (y_pred - y_true)^2, not the raw signed error.
    """
    if len(err_lesion) != len(err_fc):
        raise ValueError(f"err_lesion has {len(err_lesion)} values but err_fc has {len(err_fc)} - must match")
    statistic, p_value = wilcoxon(err_lesion, err_fc, alternative="two-sided")
    return float(statistic), float(p_value)


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR-corrected p-values, in the original input order.

    Hand-rolled rather than depending on statsmodels (not a project
    dependency - environment.yml - and not worth adding for one well-known,
    ~10-line algorithm).
    """
    p_values = np.asarray(p_values, dtype=float)
    n = len(p_values)
    order = np.argsort(p_values)
    ranked = p_values[order]
    corrected = ranked * n / np.arange(1, n + 1)
    # Enforce monotonicity (standard BH step-up procedure): a smaller p-value's
    # corrected value can never end up larger than a bigger p-value's.
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected = np.clip(corrected, 0.0, 1.0)

    result = np.empty(n, dtype=float)
    result[order] = corrected
    return result
