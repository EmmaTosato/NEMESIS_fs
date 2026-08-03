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


def umap_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return umap.UMAP(**params).fit_transform(X)


def tsne_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return TSNE(**params).fit_transform(X)


def pca_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return PCA(**params).fit_transform(X)


def pca_varimax_embed(X: np.ndarray, params: dict) -> np.ndarray:
    """PCA (covariance-matrix eigendecomposition) + varimax-rotated loadings +
    component scores via multiple regression - Thiebaut de Schotten et al. 2020
    methodology ("Data compression", papers/Thiebaut de Schotten et al -
    2020 - .../markdown/_full.md).

    Unlike the other strategies here, params is not unpacked blindly into a
    single constructor: this wraps two distinct estimators (PCA, then
    Rotator), so 'n_components'/'rotation_max_iter' are read explicitly.
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
    loadings = fitted.components_.T  # (n_features, n_components)
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


def embedding_for_viz(
    reduction_method: str, X: np.ndarray, reduction_params: dict, embedding: np.ndarray, viz_n_components: int
) -> np.ndarray:
    """Returns an embedding with exactly `viz_n_components` columns, suitable
    to plot - reused unmodified if `embedding` already has that many columns
    (every production config today: n_components == viz_n_components == 2,
    zero extra cost), otherwise refit from scratch on the same raw `X` with
    only `n_components` overridden to `viz_n_components`.

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
    return REDUCTION_METHODS[reduction_method](X, viz_params)
