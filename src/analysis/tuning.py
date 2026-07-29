"""Manual fine-tuning sweep for dimensionality-reduction methods that support it
(today: umap, tsne, pca, pca_varimax, pacmap).

No automatic selection: run_tuning_sweep only produces a comparison table -
a human reads it (or the accompanying plot) and picks the best combination by
hand, then writes it into params_reduction.json's "params" for a normal
(fine_tuning=false) run. t-SNE's other parameters (early_exaggeration,
learning_rate, max_iter) still come straight from Thiebaut de Schotten et al.
2020 and are not swept - only perplexity is, on explicit request, since the
paper's own supplementary material sweeps it too (see
docs/methods/dimensionality_reduction.md).

Quality metric differs by method, on purpose (see docs/methods/dimensionality_reduction.md):
- umap/tsne/pacmap: trustworthiness(X, embedding) - how well local
  neighborhoods survive the projection. Generic across any neighbor-based
  non-linear embedding, not umap-specific, so tsne/pacmap reuse it unchanged.
  For umap/tsne, a binary metric (jaccard/dice) in the swept "metric" is
  scored with that *same* metric (see evaluate_umap/evaluate_tsne) - never
  silently compared against trustworthiness's own euclidean default. pacmap
  has no such branch - its tuning_grid only ever sweeps n_neighbors.
- pca/pca_varimax: cumulative explained variance ratio - PCA's own natural,
  standard criterion, and the exact one the paper uses to choose a component
  count. Varimax rotation is orthogonal, so it doesn't change the total
  variance explained by the underlying (unrotated) components - the same
  criterion applies unchanged to pca_varimax.

`regress_out_volume` (umap/tsne only today) can be swept in tuning_grid
alongside `metric`: evaluate_umap/evaluate_tsne apply it to the embedding
before scoring, exactly like the production path in dim_reduction.py. Some
combinations are impossible by construction (regress_out_volume=True with
metric=jaccard/dice - see src/analysis/covariates.py, which already documents
why) - run_tuning_sweep excludes that combination from the returned table
entirely (a WARNING is logged when it happens, so it's not silent - but the
incompatibility is a known, documented fact, not a per-run finding worth a
placeholder row in every tuning_results.csv) rather than crashing the whole
sweep.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import trustworthiness

from src.analysis.covariates import (
    VolumeRegressionIncompatibleError,
    check_volume_regression_compatible,
    regress_out_covariate,
)
from src.analysis.distances import SUPPORTED_BINARY_METRICS, binary_pairwise_distance
from src.analysis.reduction import pacmap_embed, pca_varimax_embed, tsne_embed, umap_embed

TUNING_METRIC_NAMES = {
    "umap": "trustworthiness",
    "tsne": "trustworthiness",
    "pca": "cumulative_explained_variance",
    "pca_varimax": "cumulative_explained_variance",
    "pacmap": "trustworthiness",
}

METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS = {"umap", "tsne", "pacmap"}


def evaluate_umap(X: np.ndarray, params: dict, trustworthiness_n_neighbors: int) -> tuple[np.ndarray, float]:
    """Embed with UMAP, optionally regress out lesion volume, then score with
    trustworthiness(X, embedding).

    trustworthiness needs its own notion of "how close were these points
    originally" - if params requests a binary metric (jaccard/dice), that
    notion must be the *same* metric the embedding was actually built with,
    not trustworthiness's own euclidean default (comparing a jaccard-built
    embedding against euclidean neighborhoods isn't a fair test of it, see
    docs/dev/analysis.md). For those metrics X is replaced by its precomputed
    binary_pairwise_distance matrix for both the embedding and the score, and
    umap's own metric is switched to "precomputed" accordingly (also avoids
    umap/sklearn each recomputing pairwise distances the slow, non-vectorized
    way on raw high-dimensional binary features).

    "regress_out_volume" (default False) is not a UMAP constructor argument -
    stripped from params before embedding, applied to the embedding
    afterwards exactly like the production path in dim_reduction.py (OLS
    residuals against each subject's voxel count, X.sum(axis=1)), and the
    score is computed on that residualized embedding since that is what a
    production run with the same flag would actually save. Raises
    VolumeRegressionIncompatibleError if combined with metric=jaccard/dice -
    checked here (not only in run_tuning_sweep) so this holds regardless of
    caller, per the project's "single always-run validation point" rule.
    """
    regress_out_volume = params.get("regress_out_volume", False)
    check_volume_regression_compatible(regress_out_volume, params)

    metric = params.get("metric", "euclidean")
    if metric in SUPPORTED_BINARY_METRICS:
        X_input = binary_pairwise_distance(X, metric)
        umap_params = {k: v for k, v in params.items() if k not in ("metric", "regress_out_volume")}
        umap_params["metric"] = "precomputed"
        trustworthiness_metric = "precomputed"
    else:
        X_input = X
        umap_params = {k: v for k, v in params.items() if k != "regress_out_volume"}
        trustworthiness_metric = metric

    embedding = umap_embed(X_input, umap_params)
    if regress_out_volume:
        embedding = regress_out_covariate(embedding, X.sum(axis=1))
    score = float(trustworthiness(X_input, embedding, n_neighbors=trustworthiness_n_neighbors, metric=trustworthiness_metric))
    return embedding, score


def evaluate_tsne(X: np.ndarray, params: dict, trustworthiness_n_neighbors: int) -> tuple[np.ndarray, float]:
    """Embed with t-SNE, optionally regress out lesion volume, then score with
    trustworthiness(X, embedding).

    Same binary-metric handling as evaluate_umap, for the same reason: on
    binary voxel data, euclidean is dominated by lesion volume rather than
    topography, so jaccard/dice (precomputed, see binary_pairwise_distance)
    are swept alongside perplexity - both the embedding and its
    trustworthiness score use that same precomputed matrix. sklearn's TSNE
    additionally requires init != "pca" (its own default) whenever
    metric="precomputed" - "pca" needs the raw feature matrix, not a distance
    matrix - so init is forced to "random" in that case, never left at the
    default for a precomputed run.

    Same "regress_out_volume" handling as evaluate_umap too (see its
    docstring): stripped from params, applied to the embedding after fitting,
    scored on the residualized embedding, validated here regardless of caller.
    """
    regress_out_volume = params.get("regress_out_volume", False)
    check_volume_regression_compatible(regress_out_volume, params)

    metric = params.get("metric", "euclidean")
    if metric in SUPPORTED_BINARY_METRICS:
        X_input = binary_pairwise_distance(X, metric)
        tsne_params = {k: v for k, v in params.items() if k not in ("metric", "regress_out_volume")}
        tsne_params["metric"] = "precomputed"
        tsne_params["init"] = "random"
        trustworthiness_metric = "precomputed"
    else:
        X_input = X
        tsne_params = {k: v for k, v in params.items() if k != "regress_out_volume"}
        trustworthiness_metric = metric

    embedding = tsne_embed(X_input, tsne_params)
    if regress_out_volume:
        embedding = regress_out_covariate(embedding, X.sum(axis=1))
    score = float(trustworthiness(X_input, embedding, n_neighbors=trustworthiness_n_neighbors, metric=trustworthiness_metric))
    return embedding, score


def evaluate_pca(X: np.ndarray, params: dict) -> tuple[np.ndarray, float]:
    fitted = PCA(**params)
    embedding = fitted.fit_transform(X)
    score = float(fitted.explained_variance_ratio_.sum())
    return embedding, score


def evaluate_pca_varimax(X: np.ndarray, params: dict) -> tuple[np.ndarray, float]:
    fitted = PCA(n_components=params["n_components"]).fit(X)
    embedding = pca_varimax_embed(X, params)
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
) -> pd.DataFrame:
    """Evaluate every combination in the Cartesian product of tuning_grid.

    Each combination overrides base_params for the swept keys only (unswept
    keys, e.g. random_state, stay fixed at base_params' value). Returns one
    row per combination: the swept parameter values plus the method's metric
    column (see TUNING_METRIC_NAMES).

    Raises ValueError for a method with no supported tuning evaluator (only
    the methods in TUNING_METRIC_NAMES are supported today - kmeans/agglomerative/
    gmm/dbscan/spectral have no tuning_grid to begin with here, see
    clustering_tuning.py instead, and params.py.load_tuning_grid).

    If a combination has regress_out_volume=True together with metric=jaccard/dice
    (umap/tsne only - see evaluate_umap/evaluate_tsne), that specific combination
    is excluded entirely from the returned table - no embedding is computed, no
    row is added. A WARNING is logged when this happens (so it's not silent),
    but the incompatibility itself is a known, documented fact
    (src/analysis/covariates.py, docs/methods/dimensionality_reduction.md), not
    a per-run result worth a placeholder row in every tuning_results.csv.
    """
    if method not in TUNING_METRIC_NAMES:
        raise ValueError(f"fine-tuning not supported for method {method!r} - known: {sorted(TUNING_METRIC_NAMES)}")

    metric_name = TUNING_METRIC_NAMES[method]
    evaluator = _EVALUATORS[method]
    keys = list(tuning_grid.keys())
    rows = []
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
            try:
                _embedding, score = evaluator(X, combo_params, trustworthiness_n_neighbors)
            except VolumeRegressionIncompatibleError as exc:
                logging.warning(
                    "excluding combination %d/%d (%s) from results - impossible by construction: %s",
                    i,
                    total,
                    swept,
                    exc,
                )
                continue
        else:
            _embedding, score = evaluator(X, combo_params)
        rows.append({**swept, metric_name: score})

    return pd.DataFrame(rows)
