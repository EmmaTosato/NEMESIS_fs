"""Manual fine-tuning sweep for dimensionality-reduction methods that support it
(today: umap, tsne, pca, pca_varimax, pacmap).

No automatic selection: run_tuning_sweep only produces a comparison table -
a human reads it (or the accompanying plot) and picks the best combination by
hand, then writes it into params_reduction.json's "params" for a normal
(fine_tuning=false) run. t-SNE's other parameters (early_exaggeration,
learning_rate, max_iter) still come straight from Thiebaut de Schotten et al.
2020 and are not swept - only perplexity is, on explicit request, since the
paper's own supplementary material sweeps it too (see
docs/knowledge/dim_reduction.md).

Quality metric differs by method, on purpose (see docs/knowledge/dim_reduction.md):
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
"""

from __future__ import annotations

import itertools
from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import trustworthiness

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

# umap/tsne are the only evaluators that can request a precomputed binary
# distance matrix (jaccard/dice) - run_tuning_sweep passes each a shared
# per-sweep cache (keyed by metric name) so a sweep with N combinations at
# the same metric computes that matrix once, not N times (X.astype(float64)
# alone allocates a full-size copy of the feature matrix, plus an O(n^2)
# matmul - see binary_pairwise_distance - neither depends on n_neighbors/
# min_dist/n_components, so redoing it per combination is pure waste).
METHODS_WITH_DISTANCE_CACHE = {"umap", "tsne"}


def evaluate_umap(
    X: np.ndarray, params: dict, trustworthiness_n_neighbors: int, distance_cache: dict[str, np.ndarray] | None = None
) -> tuple[np.ndarray, float]:
    """Embed with UMAP, then score with trustworthiness(X, embedding).

    trustworthiness needs its own notion of "how close were these points
    originally" - if params requests a binary metric (jaccard/dice), that
    notion must be the *same* metric the embedding was actually built with,
    not trustworthiness's own euclidean default (comparing a jaccard-built
    embedding against euclidean neighborhoods isn't a fair test of it, see
    docs/dev/models.md). For those metrics X is replaced by its precomputed
    binary_pairwise_distance matrix for both the embedding and the score, and
    umap's own metric is switched to "precomputed" accordingly - this also
    guarantees an *exact* neighbor graph (umap-learn only computes exact
    k-NN itself for datasets under 4096 samples - `n_index_samples < 4096`
    in `UMAP.fit()`, https://github.com/lmcinnes/umap/blob/master/umap/umap_.py
    - above that it silently switches to the approximate NNDescent/pynndescent
    search; precomputing avoids depending on that undocumented, version-
    dependent threshold at all - see dim_reduction.py's production path,
    which now goes through the same precomputed branch for the same reason).

    `distance_cache`, when given, is read/written by metric name - a repeat
    call for the same metric (e.g. the next n_neighbors/min_dist combination
    in the same sweep) reuses the matrix instead of recomputing it. None
    (default, e.g. a standalone call outside run_tuning_sweep) always
    recomputes - never stale, just uncached.
    """
    metric = params.get("metric", "euclidean")
    if metric in SUPPORTED_BINARY_METRICS:
        if distance_cache is not None and metric in distance_cache:
            X_input = distance_cache[metric]
        else:
            X_input = binary_pairwise_distance(X, metric)
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

    Same binary-metric handling as evaluate_umap, for the same reason: on
    binary voxel data, euclidean is dominated by lesion volume rather than
    topography, so jaccard/dice (precomputed, see binary_pairwise_distance)
    are swept alongside perplexity - both the embedding and its
    trustworthiness score use that same precomputed matrix. sklearn's TSNE
    additionally requires init != "pca" (its own default) whenever
    metric="precomputed" - "pca" needs the raw feature matrix, not a distance
    matrix - so init is forced to "random" in that case, never left at the
    default for a precomputed run.

    `distance_cache` behaves exactly as in evaluate_umap - reused by metric
    name across calls within the same sweep, None (default) always
    recomputes.
    """
    metric = params.get("metric", "euclidean")
    if metric in SUPPORTED_BINARY_METRICS:
        if distance_cache is not None and metric in distance_cache:
            X_input = distance_cache[metric]
        else:
            X_input = binary_pairwise_distance(X, metric)
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
) -> tuple[pd.DataFrame, dict[tuple, np.ndarray]]:
    """Evaluate every combination in the Cartesian product of tuning_grid.

    Each combination overrides base_params for the swept keys only (unswept
    keys, e.g. random_state, stay fixed at base_params' value). Returns
    (results, embeddings_by_combo):
    - results: one row per combination, the swept parameter values plus the
      method's metric column (see TUNING_METRIC_NAMES) - unchanged shape from
      before embeddings were kept, still the only thing written to
      tuning_results.csv.
    - embeddings_by_combo: the embedding actually computed for each
      combination, keyed by the exact `combo` tuple (values in
      tuning_grid.keys() order) - kept in memory only, never serialized, so
      callers that need to *see* an embedding (not just its score) - e.g.
      dim_reduction.py's per-leaf embeddings_grid plot - don't have to refit
      it a second time.

    Raises ValueError for a method with no supported tuning evaluator (only
    the methods in TUNING_METRIC_NAMES are supported today - kmeans/agglomerative/
    gmm/hdbscan/spectral have no tuning_grid to begin with here, see
    clustering_tuning.py instead, and params.py.load_tuning_grid).
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
