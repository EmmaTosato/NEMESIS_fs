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
