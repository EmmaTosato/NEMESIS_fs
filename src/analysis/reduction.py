"""Dimensionality-reduction strategies: a plain dict[str, Callable] registry, not a class hierarchy.

Each function is a pure array-in/array-out transform: **params is unpacked
straight into the estimator's constructor, no in-code defaults - every
hyperparameter (e.g. UMAP's n_neighbors, t-SNE's perplexity) comes from
config/registry/params_reduction.json (see src/analysis/params.py), never hardcoded
here. Mirrors the "explicit registry over hardcoded dispatch" precedent
already used for config/registry/file_patterns.json.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pacmap
import umap
from factor_analyzer import Rotator
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from src.analysis.distances import SUPPORTED_BINARY_METRICS, binary_pairwise_distance, require_binary_matrix


def umap_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return umap.UMAP(**params).fit_transform(X)


def tsne_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return TSNE(**params).fit_transform(X)


def pca_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return PCA(**params).fit_transform(X)


def pca_varimax_embed(X: np.ndarray, params: dict) -> np.ndarray:
    """PCA (covariance-matrix eigendecomposition) + varimax-rotated loadings +
    component scores via multiple regression - Thiebaut de Schotten et al. 2020
    methodology ("Data compression", knowledge/nemesis/Thiebaut de Schotten et al -
    2020 - .../Thiebaut de Schotten et al - 2020.md).

    Unlike the other strategies here, params is not unpacked blindly into a
    single constructor: this wraps two distinct estimators (PCA, then
    Rotator), so 'n_components'/'rotation_max_iter' are read explicitly.

    Loadings vs. raw eigenvectors (bug fixed 2026-08, caught during a
    literature-validation review before this method ever had a
    params_reduction.json entry, so no production run is affected):
    `PCA.components_` are unit-norm eigenvectors, NOT factor loadings - the
    quantity `Rotator(method="varimax")` expects (its own docs: "The factor
    loading matrix, shape (n_features, n_factors)", same convention as
    `FactorAnalyzer.loadings_`) is `components_.T * sqrt(explained_variance_)`.
    Varimax maximizes the variance of squared loadings *across variables*;
    fed unit-norm eigenvectors instead, every component is weighted as if it
    explained equal variance, so the rotation found is not the one the
    paper's methodology (or SPSS/R, which always rotate scaled loadings)
    would produce. A second, silent consequence of the same bug: since
    `components_` is orthonormal and varimax is an orthogonal rotation, the
    *unscaled* `rotated_loadings.T @ rotated_loadings == I`, which collapses
    the "multiple regression" step below into a plain projection (`Λᵀ X`) -
    with real loadings `ΛᵀΛ != I`, and `lstsq` performs the actual multiple
    regression the paper describes ("Component scores were systematically
    extracted for all components... by means of multiple regression").
    """
    if "n_components" not in params:
        raise ValueError("pca_varimax requires 'n_components' in params")
    if "rotation_max_iter" not in params:
        raise ValueError("pca_varimax requires 'rotation_max_iter' in params")
    if params["n_components"] < 2:
        raise ValueError(
            f"pca_varimax requires n_components >= 2 (varimax rotates *between* components - "
            f"there is nothing to rotate with a single one), got {params['n_components']!r}"
        )

    X_centered = X - X.mean(axis=0)
    fitted = PCA(n_components=params["n_components"]).fit(X)
    # Factor loadings (eigenvector * sqrt(eigenvalue)), not raw eigenvectors - see docstring above.
    loadings = fitted.components_.T * np.sqrt(fitted.explained_variance_)  # (n_features, n_components)
    rotated_loadings = Rotator(method="varimax", max_iter=params["rotation_max_iter"]).fit_transform(loadings)
    # "component scores were... extracted... by means of multiple regression":
    # regress each centered row onto the rotated loadings -> (n_samples, n_components)
    scores, *_ = np.linalg.lstsq(rotated_loadings, X_centered.T, rcond=None)
    return scores.T


def pacmap_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return pacmap.PaCMAP(**params).fit_transform(X)


REDUCTION_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "umap": umap_embed,
    "tsne": tsne_embed,
    "pca": pca_embed,
    "pca_varimax": pca_varimax_embed,
    "pacmap": pacmap_embed,
}


def embed(
    reduction_method: str, X: np.ndarray, params: dict, distance_cache: dict[str, np.ndarray] | None = None
) -> np.ndarray:
    """Wraps REDUCTION_METHODS[reduction_method], replacing X with its
    precomputed Jaccard/Dice distance matrix (src/analysis/distances.py)
    whenever params["metric"] is one of SUPPORTED_BINARY_METRICS - no effect
    for any other metric/method (pca, pacmap, or umap/tsne at
    metric="euclidean"), X/params pass through unchanged.

    Why this exists (2026-08, literature-validation review): umap-learn only
    computes an *exact* k-NN graph itself for datasets under 4096 samples
    (`n_index_samples < 4096` in `UMAP.fit()`, sets `self._small_data = True`
    - see umap/umap_.py in the umap-learn source); above that threshold it
    silently switches to the approximate NNDescent/pynndescent search. Before
    this function existed, only src/analysis/tuning.py's fine-tuning sweep
    (evaluate_umap/evaluate_tsne) went through binary_pairwise_distance +
    metric="precomputed" (built as a *speed* optimization for sweeping many
    combinations, never ported to the single-run production path) - meaning
    the tuning table used to choose production hyperparameters was scored
    against an exact neighbor graph, while dim_reduction.py/
    dim_reduction_clustering.py's production path passed the metric string
    straight to umap.UMAP/sklearn.TSNE on raw X. This project's cohort is
    currently under 4096 subjects, so umap-learn's own <4096 branch likely
    already computed an exact graph in production too - but Task 1's stated
    target is ~4000 subjects (README.md), right at that undocumented,
    version-dependent threshold. Routing every REDUCTION_METHODS call through
    this function removes the dependency on that threshold entirely, so
    production is guaranteed to use the exact same neighbor graph the tuning
    sweep it was chosen from actually evaluated, regardless of cohort size.

    sklearn's TSNE additionally requires init != "pca" (its own default)
    whenever metric="precomputed" ("pca" needs the raw feature matrix, not a
    distance matrix) - forced to "random" here for reduction_method="tsne",
    same as tuning.py's evaluate_tsne.

    `distance_cache`, when given, is read/written by metric name - lets a
    caller that computes an embedding and then a viz refit (embedding_for_viz
    below) at the same metric reuse the same precomputed matrix instead of
    recomputing it. None (default) always recomputes.
    """
    metric = params.get("metric")
    if metric in SUPPORTED_BINARY_METRICS:
        require_binary_matrix(X, metric)
        if distance_cache is not None and metric in distance_cache:
            X = distance_cache[metric]
        else:
            X = binary_pairwise_distance(X, metric)
            if distance_cache is not None:
                distance_cache[metric] = X
        params = {k: v for k, v in params.items() if k != "metric"}
        params["metric"] = "precomputed"
        if reduction_method == "tsne":
            params["init"] = "random"
    return REDUCTION_METHODS[reduction_method](X, params)


def embedding_for_viz(
    reduction_method: str,
    X: np.ndarray,
    reduction_params: dict,
    embedding: np.ndarray,
    viz_n_components: int,
    distance_cache: dict[str, np.ndarray] | None = None,
) -> np.ndarray:
    """Returns an embedding with exactly `viz_n_components` columns, suitable
    to plot - reused unmodified if `embedding` already has that many columns
    (every production config today: n_components == viz_n_components == 2,
    zero extra cost), otherwise refit from scratch on the same raw `X` with
    only `n_components` overridden to `viz_n_components` (via `embed` above,
    so a jaccard/dice refit gets the same precomputed-distance treatment as
    the original fit).

    Why a refit and not embedding[:, :viz_n_components]: for umap/tsne/pacmap,
    the output dimensions of a single fit have no ordering by importance
    (unlike PCA's variance-ranked components) - they're jointly optimized to
    satisfy one objective in the full n_components-dimensional space, so
    slicing 2 or 3 of them out is an arbitrary cut, not a meaningful summary,
    and can make a real cluster structure look artificially merged or split.
    A second fit at n_components=viz_n_components, same metric/n_neighbors/
    min_dist/random_state, shares the same neighbor graph as the original fit
    (that graph depends only on metric/n_neighbors, not n_components) and is
    UMAP/t-SNE's own best-effort layout for exactly that many dimensions. For
    PCA this second fit is mathematically equivalent to slicing (greedy
    variance ordering means the top components don't change when more are
    requested), so the same rule is correct for every REDUCTION_METHODS
    entry without a per-method branch.
    """
    if embedding.shape[1] == viz_n_components:
        return embedding
    viz_params = {**reduction_params, "n_components": viz_n_components}
    return embed(reduction_method, X, viz_params, distance_cache)
