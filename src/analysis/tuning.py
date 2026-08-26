"""Manual fine-tuning sweep for dimensionality-reduction methods that support it
(today: umap, tsne, pca, pca_varimax, pacmap). No automatic selection:
run_tuning_sweep only produces a comparison table - a human reads it (or the
accompanying plot) and writes the chosen combination into params_reduction.json's
"params" by hand. See docs/dev/models.md and
knowledge/dim_reduction_clustering/dim_reduction_tuning_guide.md for why the
quality metric differs by method family (TUNING_METRIC_NAMES) and why only
t-SNE's perplexity is swept, not its other params.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import trustworthiness

from src.analysis.distances import PRECOMPUTABLE_METRICS, precomputed_distance
from src.analysis.reduction import _pca_varimax_fit, pacmap_embed, tsne_embed, umap_embed

TUNING_METRIC_NAMES = {
    "umap": "trustworthiness",
    "tsne": "trustworthiness",
    "pca": "cumulative_explained_variance",
    "pca_varimax": "cumulative_explained_variance",
    "pacmap": "trustworthiness",
}

METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS = {"umap", "tsne", "pacmap"}

# umap/tsne are the only evaluators that can request a precomputed distance
# matrix (jaccard/dice/euclidean, see src/analysis/distances.py) -
# run_tuning_sweep passes each a shared per-sweep cache (keyed by metric
# name) so a sweep with N combinations at the same metric computes that
# matrix once, not N times - none of jaccard/dice/euclidean's precomputed
# distance depends on n_neighbors/min_dist/n_components, so redoing it per
# combination is pure waste (for euclidean specifically, that waste is
# umap-learn's own neighbor search, not the distance computation itself -
# see distances.py's module docstring).
METHODS_WITH_DISTANCE_CACHE = {"umap", "tsne"}


def evaluate_umap(
    X: np.ndarray, params: dict, trustworthiness_n_neighbors: int, distance_cache: dict[str, np.ndarray] | None = None
) -> tuple[np.ndarray, float]:
    """Embed with UMAP, then score with trustworthiness(X, embedding).

    For a precomputable metric (jaccard/dice/euclidean, see
    src/analysis/distances.py), X is replaced by its precomputed distance
    matrix for *both* the embedding and the trustworthiness score, and
    umap's metric switched to "precomputed" - trustworthiness must be scored
    against the same notion of "originally close" the embedding was actually
    built with, not its own euclidean-on-raw-X default (see docs/dev/models.md
    for why, the exactness/speed rationale, and the measured numbers).

    `distance_cache`, when given, is read/written by metric name - a repeat
    call for the same metric within the same sweep reuses the matrix instead
    of recomputing it. None (default) always recomputes.
    """
    metric = params.get("metric", "euclidean")
    if metric in PRECOMPUTABLE_METRICS:
        if distance_cache is not None and metric in distance_cache:
            X_input = distance_cache[metric]
        else:
            X_input = precomputed_distance(X, metric)
            if distance_cache is not None:
                distance_cache[metric] = X_input
        umap_params = {k: v for k, v in params.items() if k != "metric"}
        umap_params["metric"] = "precomputed"
        trustworthiness_metric = "precomputed"
    else:
        X_input = X
        umap_params = dict(params)
        trustworthiness_metric = metric

    embedding = umap_embed(X_input, umap_params)
    score = float(trustworthiness(X_input, embedding, n_neighbors=trustworthiness_n_neighbors, metric=trustworthiness_metric))
    return embedding, score


def evaluate_tsne(
    X: np.ndarray, params: dict, trustworthiness_n_neighbors: int, distance_cache: dict[str, np.ndarray] | None = None
) -> tuple[np.ndarray, float]:
    """Embed with t-SNE, then score with trustworthiness(X, embedding).

    Same precomputed-metric handling as evaluate_umap (see its docstring and
    docs/dev/models.md) - additionally forces init="random" whenever
    metric="precomputed", since sklearn TSNE's own default init="pca" can't
    run on a distance matrix. `distance_cache` behaves exactly as in
    evaluate_umap. Caveat: the euclidean speedup magnitude is only measured
    for evaluate_umap - correct and safe for t-SNE either way (same
    already-validated mechanism), but don't assume the same order of
    magnitude until it's actually measured on a real sweep.
    """
    metric = params.get("metric", "euclidean")
    if metric in PRECOMPUTABLE_METRICS:
        if distance_cache is not None and metric in distance_cache:
            X_input = distance_cache[metric]
        else:
            X_input = precomputed_distance(X, metric)
            if distance_cache is not None:
                distance_cache[metric] = X_input
        tsne_params = {k: v for k, v in params.items() if k != "metric"}
        tsne_params["metric"] = "precomputed"
        tsne_params["init"] = "random"
        trustworthiness_metric = "precomputed"
    else:
        X_input = X
        tsne_params = dict(params)
        trustworthiness_metric = metric

    embedding = tsne_embed(X_input, tsne_params)
    score = float(trustworthiness(X_input, embedding, n_neighbors=trustworthiness_n_neighbors, metric=trustworthiness_metric))
    return embedding, score


def evaluate_pca(X: np.ndarray, params: dict) -> tuple[np.ndarray, float]:
    fitted = PCA(**params)
    embedding = fitted.fit_transform(X)
    score = float(fitted.explained_variance_ratio_.sum())
    return embedding, score


def evaluate_pca_varimax(X: np.ndarray, params: dict) -> tuple[np.ndarray, float]:
    """AUDIT_FINDINGS.md #57: used to fit PCA twice per combination - once here just to
    read explained_variance_ratio_, once again inside pca_varimax_embed for the actual
    embedding. _pca_varimax_fit (shared with pca_varimax_embed) now fits once and returns
    both."""
    embedding, fitted = _pca_varimax_fit(X, params)
    score = float(fitted.explained_variance_ratio_.sum())
    return embedding, score


def evaluate_pacmap(X: np.ndarray, params: dict, trustworthiness_n_neighbors: int) -> tuple[np.ndarray, float]:
    embedding = pacmap_embed(X, params)
    score = float(trustworthiness(X, embedding, n_neighbors=trustworthiness_n_neighbors))
    return embedding, score


_EVALUATORS: dict[str, Callable] = {
    "umap": evaluate_umap,
    "tsne": evaluate_tsne,
    "pca": evaluate_pca,
    "pca_varimax": evaluate_pca_varimax,
    "pacmap": evaluate_pacmap,
}


def run_tuning_sweep(
    method: str,
    X: np.ndarray,
    base_params: dict,
    tuning_grid: dict[str, list],
    trustworthiness_n_neighbors: int | None,
) -> tuple[pd.DataFrame, dict[tuple, np.ndarray]]:
    """Evaluate every combination in the Cartesian product of tuning_grid.

    Each combination overrides base_params for the swept keys only. Returns
    (results, embeddings_by_combo): results is one row per combination (swept
    values + the method's metric column, see TUNING_METRIC_NAMES), the only
    thing written to tuning_results.csv; embeddings_by_combo keys each
    combination's actual embedding by its exact `combo` tuple, in-memory only
    - lets a caller that needs to *see* an embedding (e.g. dim_reduction.py's
    per-leaf embeddings_grid plot) avoid refitting it a second time.

    Raises ValueError for a method with no supported tuning evaluator - only
    TUNING_METRIC_NAMES' methods are supported here (clustering methods go
    through clustering_tuning.py instead).
    """
    if method not in TUNING_METRIC_NAMES:
        raise ValueError(f"fine-tuning not supported for method {method!r} - known: {sorted(TUNING_METRIC_NAMES)}")

    metric_name = TUNING_METRIC_NAMES[method]
    evaluator = _EVALUATORS[method]
    keys = list(tuning_grid.keys())
    rows = []
    embeddings_by_combo: dict[tuple, np.ndarray] = {}
    distance_cache: dict[str, np.ndarray] = {}
    import logging

    combinations = list(itertools.product(*tuning_grid.values()))
    total = len(combinations)
    logging.info("Starting fine-tuning sweep for %s (%d combinations)", method, total)

    for i, combo in enumerate(combinations, 1):
        swept = dict(zip(keys, combo))
        combo_params = {**base_params, **swept}
        logging.info("Evaluating combination %d/%d: %s", i, total, swept)
        if method in METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS:
            if trustworthiness_n_neighbors is None:
                raise ValueError(f"trustworthiness_n_neighbors is required to fine-tune {method!r}")
            if method in METHODS_WITH_DISTANCE_CACHE:
                embedding, score = evaluator(X, combo_params, trustworthiness_n_neighbors, distance_cache)
            else:
                embedding, score = evaluator(X, combo_params, trustworthiness_n_neighbors)
        else:
            embedding, score = evaluator(X, combo_params)
        rows.append({**swept, metric_name: score})
        embeddings_by_combo[combo] = embedding

    return pd.DataFrame(rows), embeddings_by_combo
