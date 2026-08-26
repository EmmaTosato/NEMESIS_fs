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

from src.analysis.distances import PRECOMPUTABLE_METRICS, SUPPORTED_BINARY_METRICS, precomputed_distance, require_binary_matrix


def umap_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return umap.UMAP(**params).fit_transform(X)


def tsne_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return TSNE(**params).fit_transform(X)


def pca_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return PCA(**params).fit_transform(X)


def pca_varimax_embed(X: np.ndarray, params: dict) -> np.ndarray:
    """PCA + varimax-rotated loadings + component scores via multiple
    regression - Thiebaut de Schotten et al. 2020's "Data compression"
    methodology (see docs/dev/models.md for the full derivation).

    Unlike the other strategies here, params is not unpacked blindly into a
    single constructor: this wraps two distinct estimators (PCA, then
    Rotator), so 'n_components'/'rotation_max_iter' are read explicitly.

    Loadings passed to Rotator are `components_.T * sqrt(explained_variance_)`
    (factor loadings), never the raw `components_` (unit-norm eigenvectors) -
    using the latter silently both mis-weights the rotation and degrades the
    "multiple regression" score step below into a plain projection (bug
    fixed 2026-08, before any production run - see docs/dev/models.md and
    tests/unit/test_reduction.py::test_pca_varimax_embed_rotates_scaled_loadings_not_raw_eigenvectors).
    """
    embedding, _fitted = _pca_varimax_fit(X, params)
    return embedding


def _pca_varimax_fit(X: np.ndarray, params: dict) -> tuple[np.ndarray, PCA]:
    """Shared implementation for pca_varimax_embed above and
    tuning.py::evaluate_pca_varimax (AUDIT_FINDINGS.md #57) - also returns the
    fitted PCA object so a caller that needs `explained_variance_ratio_` (the
    tuning sweep's own score) doesn't have to fit a second, separate PCA on
    the same X/n_components just to read it.
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
    return scores.T, fitted


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
    reduction_method: str,
    X: np.ndarray,
    params: dict,
    distance_cache: dict[str, np.ndarray] | None = None,
    precompute_distance_metric: bool = True,
) -> np.ndarray:
    """Wraps REDUCTION_METHODS[reduction_method]. When precompute_distance_metric
    is True (default) and params["metric"] is in PRECOMPUTABLE_METRICS
    (jaccard/dice/euclidean), X is replaced by its precomputed distance
    matrix (src/analysis/distances.py) and metric switched to "precomputed" -
    guarantees an exact neighbor graph regardless of cohort size and, for
    euclidean specifically, is also a large speed win at this project's scale
    (see docs/dev/models.md for why and the measured numbers). No effect for
    pca/pca_varimax/pacmap, whose params never carry a "metric" key. Forces
    init="random" for reduction_method="tsne" when precomputing - sklearn's
    own default init="pca" can't run on a distance matrix.

    `distance_cache`, when given, is read/written by metric name - lets a
    caller that computes an embedding and then a viz refit (embedding_for_viz
    below) at the same metric reuse the same precomputed matrix instead of
    recomputing it. None (default) always recomputes.

    `precompute_distance_metric=False` skips the whole precomputed-distance
    path and passes params["metric"] straight to REDUCTION_METHODS on raw X -
    a "vanilla" call with no precompute machinery, for reproducibility
    against literature/external UMAP runs (see docs/dev/config.md's
    `precompute_distance_metric` entry for the full rationale/default).
    `require_binary_matrix` still runs regardless of this flag - jaccard/dice
    being meaningless on non-binary data is a fact about the data, not about
    which computation path is chosen.
    """
    metric = params.get("metric")
    if metric in SUPPORTED_BINARY_METRICS:
        require_binary_matrix(X, metric)
    if precompute_distance_metric and metric in PRECOMPUTABLE_METRICS:
        if distance_cache is not None and metric in distance_cache:
            X = distance_cache[metric]
        else:
            X = precomputed_distance(X, metric)
            if distance_cache is not None:
                distance_cache[metric] = X
        params = {k: v for k, v in params.items() if k != "metric"}
        params["metric"] = "precomputed"
        if reduction_method == "tsne":
            params["init"] = "random"
    return REDUCTION_METHODS[reduction_method](X, params)


# Methods where a same-metric/same-n_neighbors/same-random_state refit at a
# different n_components is a legitimate view in its own right (umap/tsne's
# output dimensions have no fixed meaning - lessons_learned.md #16, never a
# slice). Deliberately narrow (2026-08-17, on request) - pca_varimax, pca and
# pacmap are all excluded too, each for a different reason - see
# docs/dev/models.md's embedding_for_viz entry for the full per-method
# rationale.
_REFITTABLE_FOR_VIZ: frozenset[str] = frozenset({"umap", "tsne"})


def embedding_for_viz(
    reduction_method: str,
    X: np.ndarray,
    reduction_params: dict,
    embedding: np.ndarray,
    viz_n_components: int,
    distance_cache: dict[str, np.ndarray] | None = None,
    precompute_distance_metric: bool = True,
) -> np.ndarray:
    """Returns an embedding with exactly `viz_n_components` columns, for
    plotting - reused unmodified if `embedding` already has that many columns
    (zero extra cost), otherwise refit from scratch via `embed` above with
    only `n_components` overridden - but only for `reduction_method` in
    _REFITTABLE_FOR_VIZ (umap/tsne). Never `embedding[:, :viz_n_components]`:
    a single fit's output dimensions have no ordering by importance (unlike
    PCA's variance-ranked components), so a slice is an arbitrary cut that
    can make real cluster structure look artificially merged or split - see
    lessons_learned.md #16 and docs/dev/models.md.

    Raises ValueError if `reduction_method` isn't in _REFITTABLE_FOR_VIZ and
    `embedding` doesn't already have viz_n_components columns (see that
    frozenset's own comment for why each excluded method is excluded) - the
    caller must rerun with viz_n_components == n_components for that method
    instead. `precompute_distance_metric` is forwarded as-is to `embed`
    above, so the refit follows the same raw-vs-precomputed choice as the
    original fit.
    """
    if embedding.shape[1] == viz_n_components:
        return embedding
    if reduction_method not in _REFITTABLE_FOR_VIZ:
        raise ValueError(
            f"{reduction_method!r} has no valid viz-refit at a different dimensionality - "
            f"the production embedding has {embedding.shape[1]} components but "
            f"viz_n_components={viz_n_components} was requested. Only {sorted(_REFITTABLE_FOR_VIZ)} "
            "support a same-metric refit at a different n_components (see this function's own "
            "docstring for why pca/pca_varimax/pacmap don't) - rerun with viz_n_components equal "
            "to n_components for this method instead"
        )
    viz_params = {**reduction_params, "n_components": viz_n_components}
    return embed(reduction_method, X, viz_params, distance_cache, precompute_distance_metric)
