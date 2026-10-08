"""Which subject variables distinguish a cluster from the rest: a logistic regression.

For one cluster, the outcome is "the subject is in this cluster" (1) or not (0), and the predictors
are subject variables the clustering never saw (age, sex, NIHSS, lesion volume, dataset...). Each
coefficient is reported as an odds ratio: how many times more (or less) likely a subject is to be in
the cluster when that variable goes up by one standard deviation (numeric), or when it takes a level
instead of the reference level (categorical), with the other variables held fixed.

Backs notebooks/post-results_analysis/cluster_interpretation.ipynb. It is an association, not a
cause, and a variable derived from the clustering input (lesion summaries for a lesion run,
disconnection summaries for an sdc run) is associated with the cluster partly by construction.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

# Rule of thumb (Peduzzi et al. 1996): at least this many subjects in the rarer class per fitted term,
# otherwise the estimates are unstable. Below it the fit is refused, not reported.
MIN_EVENTS_PER_TERM = 10
# A per-standard-deviation log-odds beyond this (odds ratio > ~3e6) means one variable (almost)
# separates the two groups perfectly: the likelihood has no finite maximum and the numbers are meaningless.
MAX_ABS_COEFFICIENT = 15.0
MAX_CONDITION_NUMBER = 1e8
_Z_95 = 1.959964


@dataclass(frozen=True)
class RegressionResult:
    """coefficients is indexed by term, with columns odds_ratio, ci_low, ci_high (95% Wald), p_value (Wald,
    two-sided) and vif (variance inflation factor: how much of the term is explained by the other terms,
    1 = independent, above ~5 = strongly overlapping with the others, so its odds ratio is unstable).

    pseudo_r2 is McFadden's (0 = no better than the cluster's overall rate, 0.2-0.4 is already a good fit);
    auc is the area under the ROC curve on the subjects used (0.5 = chance, 1 = perfect; in-sample, so
    slightly optimistic)."""

    n_used: int
    n_in_cluster: int
    n_dropped_missing: int
    events_per_term: float
    pseudo_r2: float
    auc: float
    coefficients: pd.DataFrame


def cluster_vs_rest_regression(
    features: pd.DataFrame,
    in_cluster: np.ndarray,
    *,
    numeric: list[str],
    categorical: list[str],
    references: dict[str, str] | None = None,
) -> RegressionResult:
    """Logistic regression of `in_cluster` on the `numeric` and `categorical` columns of `features`.

    Numeric columns are standardized (mean 0, standard deviation 1, over the subjects used), so their odds
    ratios are per standard deviation and comparable across variables. Categorical columns become one 0/1
    column per level except the reference level, `references[column]` or, by default, the most frequent one.
    Subjects with a missing value in any used column are dropped (n_dropped_missing says how many).

    Raises ValueError for mismatched lengths, a missing or unknown column, a single class, a constant
    numeric column, an unknown reference level, fewer than MIN_EVENTS_PER_TERM subjects of the rarer class
    per term, collinear terms, or (quasi-)perfect separation.
    """
    in_cluster = np.asarray(in_cluster, dtype=bool)
    references = references or {}
    if len(features) != len(in_cluster):
        raise ValueError(f"features has {len(features)} rows but in_cluster has {len(in_cluster)}")
    unknown = [c for c in [*numeric, *categorical] if c not in features.columns]
    if unknown:
        raise ValueError(f"columns not in features: {unknown}")
    if not numeric and not categorical:
        raise ValueError("no variables to fit")

    used = features[[*numeric, *categorical]].reset_index(drop=True)
    complete = used.notna().all(axis=1).to_numpy()
    n_dropped = int((~complete).sum())
    used, outcome = used[complete].reset_index(drop=True), in_cluster[complete]
    if outcome.all() or not outcome.any():
        raise ValueError("after dropping missing values the outcome has a single class")

    design = pd.DataFrame(index=used.index)
    for column in numeric:
        values = used[column].astype(float)
        if values.std(ddof=0) == 0:
            raise ValueError(f"numeric column {column!r} is constant among the subjects used")
        design[column] = (values - values.mean()) / values.std(ddof=0)
    for column in categorical:
        levels = used[column].astype(str)
        reference = references.get(column, levels.value_counts().idxmax())
        if reference not in set(levels):
            raise ValueError(f"reference level {reference!r} of {column!r} is not among {sorted(set(levels))}")
        for level in sorted(set(levels) - {reference}):
            design[f"{column}: {level} (rif. {reference})"] = (levels == level).astype(float)
    if design.shape[1] == 0:
        raise ValueError("the design has no columns: every categorical column has a single level")

    n_events = int(min(outcome.sum(), (~outcome).sum()))
    events_per_term = n_events / design.shape[1]
    if events_per_term < MIN_EVENTS_PER_TERM:
        raise ValueError(
            f"only {n_events} subjects in the rarer class for {design.shape[1]} terms "
            f"({events_per_term:.1f} per term, need {MIN_EVENTS_PER_TERM}): use fewer variables or a larger cluster"
        )

    matrix = design.to_numpy()
    correlation = np.corrcoef(matrix, rowvar=False).reshape(design.shape[1], design.shape[1])
    if np.linalg.cond(correlation) > MAX_CONDITION_NUMBER:
        raise ValueError("the terms are collinear (one is a combination of the others): drop one of them")
    vif = np.diag(np.linalg.inv(correlation))

    # C=np.inf is scikit-learn 1.8's documented way to ask for no regularization (penalty=None is deprecated),
    # and it still emits a UserWarning saying C is ignored - exactly what is wanted here.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Setting penalty=None will ignore the C and l1_ratio parameters")
        model = LogisticRegression(C=np.inf, max_iter=10000, tol=1e-10).fit(matrix, outcome)
    coefficients = model.coef_[0]
    if np.abs(coefficients).max() > MAX_ABS_COEFFICIENT:
        worst = design.columns[int(np.abs(coefficients).argmax())]
        raise ValueError(f"(quasi-)perfect separation: {worst!r} alone almost separates the cluster from the rest")

    probabilities = model.predict_proba(matrix)[:, 1]
    with_intercept = np.column_stack([np.ones(len(matrix)), matrix])
    information = with_intercept.T @ (with_intercept * (probabilities * (1 - probabilities))[:, None])
    standard_errors = np.sqrt(np.diag(np.linalg.inv(information)))[1:]
    z_scores = coefficients / standard_errors

    table = pd.DataFrame(
        {
            "odds_ratio": np.exp(coefficients),
            "ci_low": np.exp(coefficients - _Z_95 * standard_errors),
            "ci_high": np.exp(coefficients + _Z_95 * standard_errors),
            "p_value": 2 * stats.norm.sf(np.abs(z_scores)),
            "vif": vif,
        },
        index=design.columns,
    )
    rate = outcome.mean()
    log_likelihood = np.sum(outcome * np.log(probabilities) + ~outcome * np.log(1 - probabilities))
    null_log_likelihood = len(outcome) * (rate * np.log(rate) + (1 - rate) * np.log(1 - rate))
    return RegressionResult(
        n_used=len(outcome),
        n_in_cluster=int(outcome.sum()),
        n_dropped_missing=n_dropped,
        events_per_term=events_per_term,
        pseudo_r2=float(1 - log_likelihood / null_log_likelihood),
        auc=float(roc_auc_score(outcome, probabilities)),
        coefficients=table,
    )
