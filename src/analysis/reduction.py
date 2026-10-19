"""Dimensionality-reduction strategies: a plain dict[str, Callable] registry, not a class hierarchy.

Each function is a pure array-in/array-out transform: **params is unpacked
straight into the estimator's constructor (`pca` is the one exception: it has its own
params contract, src/analysis/pca_method.py), no in-code defaults - every
hyperparameter (e.g. UMAP's n_neighbors, t-SNE's perplexity) comes from
config/registry/params_reduction.json (see src/analysis/params.py), never hardcoded
here. Same "explicit registry over hardcoded dispatch" precedent as the metadata
sources registry (config/registry/metadata_sources.json).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pacmap
import umap
from sklearn.manifold import TSNE

from src.analysis.distances import PRECOMPUTABLE_METRICS, SUPPORTED_BINARY_METRICS, precomputed_distance, require_binary_matrix
from src.analysis.pca_method import fit_pca_embedding


def umap_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return umap.UMAP(**params).fit_transform(X)


def tsne_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return TSNE(**params).fit_transform(X)


def pca_embed(X: np.ndarray, params: dict) -> np.ndarray:
    """The `pca` method: solver, standardization, rotation and component count all come from `params`
    (src/analysis/pca_method.py); returns only the embedding."""
    return fit_pca_embedding(X, params)[0]


def pacmap_embed(X: np.ndarray, params: dict) -> np.ndarray:
    return pacmap.PaCMAP(**params).fit_transform(X)


REDUCTION_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "umap": umap_embed,
    "tsne": tsne_embed,
    "pca": pca_embed,
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
    pca/pacmap, whose params never carry a "metric" key. Forces
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
# slice). Deliberately narrow (2026-08-17, on request) - pca and pacmap are
# both excluded too, each for a different reason - see
# docs/dev/models.md's embedding_for_viz entry for the full per-method
# rationale.
_REFITTABLE_FOR_VIZ: frozenset[str] = frozenset({"umap", "tsne"})


def _columns_ordered_by_variance(reduction_method: str, reduction_params: dict) -> bool:
    """True for a pca whose columns come out most variance first: an unrotated one, or a rotated one that
    picked its kept components from `rotation_n_components` rotated ones (pca_method.py). A rotated pca
    that kept the components it rotated has columns with no order."""
    return reduction_method == "pca" and (
        reduction_params.get("rotation") == "none" or "rotation_n_components" in reduction_params
    )


def _leading_components(embedding: np.ndarray, viz_n_components: int) -> np.ndarray:
    """The first `viz_n_components` columns of a PCA embedding whose columns are ordered by variance. Unlike
    any other method's output, the first two are the two directions that separate the subjects most: a
    slice is a legitimate 2D view of the same fit, not an arbitrary cut (lessons_learned.md #16 names
    PCA's variance-ranked components as the one exception)."""
    if embedding.shape[1] < viz_n_components:
        raise ValueError(
            f"the pca embedding has {embedding.shape[1]} component(s), fewer than viz_n_components={viz_n_components} - "
            "keep at least that many components, or lower viz_n_components"
        )
    return embedding[:, :viz_n_components]


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

    A pca whose columns are ordered by variance (unrotated, or rotated with `rotation_n_components`:
    `_columns_ordered_by_variance`) is the exception to the "never a slice" rule: its leading columns
    are its leading components (`_leading_components`).

    Raises ValueError if `reduction_method` isn't in _REFITTABLE_FOR_VIZ (nor such a pca) and
    `embedding` doesn't already have viz_n_components columns (see that
    frozenset's own comment for why each excluded method is excluded) - the
    caller must rerun with viz_n_components == n_components for that method
    instead. `precompute_distance_metric` is forwarded as-is to `embed`
    above, so the refit follows the same raw-vs-precomputed choice as the
    original fit.
    """
    if embedding.shape[1] == viz_n_components:
        return embedding
    if _columns_ordered_by_variance(reduction_method, reduction_params):
        return _leading_components(embedding, viz_n_components)
    if reduction_method not in _REFITTABLE_FOR_VIZ:
        raise ValueError(
            f"{reduction_method!r} has no valid viz-refit at a different dimensionality - "
            f"the production embedding has {embedding.shape[1]} components but "
            f"viz_n_components={viz_n_components} was requested. Only {sorted(_REFITTABLE_FOR_VIZ)} "
            "support a same-metric refit at a different n_components (see this function's own "
            "docstring for why pca/pacmap don't) - rerun with viz_n_components equal "
            "to n_components for this method instead"
        )
    viz_params = {**reduction_params, "n_components": viz_n_components}
    return embed(reduction_method, X, viz_params, distance_cache, precompute_distance_metric)
