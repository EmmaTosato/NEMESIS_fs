"""Manual fine-tuning sweep for dimensionality-reduction methods that support it
(today: umap, pca, pca_varimax, pacmap).

No automatic selection: run_tuning_sweep only produces a comparison table -
a human reads it (or the accompanying plot) and picks the best combination by
hand, then writes it into params_reduction.json's "params" for a normal
(fine_tuning=false) run. t-SNE is deliberately excluded - its parameters come
straight from Thiebaut de Schotten et al. 2020, not from a sweep (see
docs/methods/dimensionality_reduction.md).

Quality metric differs by method, on purpose (see docs/methods/dimensionality_reduction.md):
- umap/pacmap: trustworthiness(X, embedding) - how well local neighborhoods
  survive the projection. Generic across any neighbor-based non-linear
  embedding, not umap-specific, so pacmap reuses it unchanged.
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

from src.analysis.reduction import pacmap_embed, pca_varimax_embed, umap_embed

TUNING_METRIC_NAMES = {
    "umap": "trustworthiness",
    "pca": "cumulative_explained_variance",
    "pca_varimax": "cumulative_explained_variance",
    "pacmap": "trustworthiness",
}

METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS = {"umap", "pacmap"}


def evaluate_umap(X: np.ndarray, params: dict, trustworthiness_n_neighbors: int) -> tuple[np.ndarray, float]:
    embedding = umap_embed(X, params)
    score = float(trustworthiness(X, embedding, n_neighbors=trustworthiness_n_neighbors))
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
    the methods in TUNING_METRIC_NAMES are supported today - t-SNE/kmeans have
    no tuning_grid to begin with, see params.py.load_tuning_grid).
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
        combo_params = {**base_params, **dict(zip(keys, combo))}
        logging.info("Evaluating combination %d/%d: %s", i, total, dict(zip(keys, combo)))
        if method in METHODS_REQUIRING_TRUSTWORTHINESS_N_NEIGHBORS:
            if trustworthiness_n_neighbors is None:
                raise ValueError(f"trustworthiness_n_neighbors is required to fine-tune {method!r}")
            _embedding, score = evaluator(X, combo_params, trustworthiness_n_neighbors)
        else:
            _embedding, score = evaluator(X, combo_params)
        rows.append({**dict(zip(keys, combo)), metric_name: score})

    return pd.DataFrame(rows)
