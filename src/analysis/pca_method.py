"""The `pca` reduction method: reads its params_reduction.json entry and runs the chosen solver.

One method, many choices - all of them are params, none hardcoded (code_standards.md §5):

- solver: "blocks" (src/analysis/covariance_pca.py: reads X a block at a time, runs on matrices that
  do not fit sklearn) or "sklearn" (sklearn.decomposition.PCA on an in-memory copy of X: the
  standard implementation, for small matrices and cross-checks).
- standardize: divide every column by its standard deviation (PCA on the correlation matrix).
- dual / chunk_columns / max_matrix_gib: how the "blocks" solver builds its matrix (see
  covariance_pca.py); they mean nothing to sklearn, so giving them with solver "sklearn" raises.
- rotation: "none" or an orthogonal rotation (varimax...); rotation_max_iter is required with one.
  The sklearn solver does not rotate.
- n_components or variance_share (exactly one): how many components to keep, as a count or as the
  share of the variance they must reach.

A param is either present with a value or absent - never null: a null would travel into the run's
recorded params (config.md, runs.csv) and be read back as a value by whatever consumes them.

Returns the embedding and the share of the total variance the kept components explain (the
fine-tuning score of src/analysis/tuning.py).

The decomposition does not depend on how many components are kept, nor on the rotation: a sweep over
n_components, variance_share or rotation can share one fit through `model_cache` (a dict the caller
owns, keyed by what the fit does depend on), instead of repeating the expensive part per combination.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np
from sklearn.decomposition import PCA

from src.analysis.covariance_pca import (
    NO_ROTATION,
    SUPPORTED_ROTATIONS,
    column_statistics,
    fit_covariance_pca,
    pca_embedding,
    resolve_n_components,
)

SOLVERS = ("blocks", "sklearn")
_REQUIRED = ("solver", "standardize", "rotation")
_BLOCKS_ONLY = ("dual", "chunk_columns", "max_matrix_gib")
_ALLOWED = {*_REQUIRED, *_BLOCKS_ONLY, "rotation_max_iter", "n_components", "variance_share"}


class PcaFit(NamedTuple):
    """What a `pca` run produced: the embedding, how many components it kept (the answer to
    variance_share), the share of the total variance they explain, and the whole variance spectrum
    (descending, one value per component) - the curve to read when choosing variance_share."""

    embedding: np.ndarray
    n_components: int
    explained_share: float
    eigenvalues: np.ndarray


def fit_pca(X: np.ndarray, params: dict, model_cache: dict | None = None) -> PcaFit:
    """Run the `pca` method described by `params` on X.

    `model_cache`, when given, is read/written by what the decomposition depends on (solver,
    standardize, dual, resource knobs) - it must only be shared between calls on the same X."""
    _validate(params)
    cache = {} if model_cache is None else model_cache
    if params["solver"] == "sklearn":
        return _fit_sklearn(X, params, cache)
    return _fit_blocks(X, params, cache)


def fit_pca_embedding(X: np.ndarray, params: dict, model_cache: dict | None = None) -> tuple[np.ndarray, float]:
    """(embedding, share of the variance explained by the kept components): the view of `fit_pca`
    the registry and the tuning sweep need."""
    fit = fit_pca(X, params, model_cache)
    return fit.embedding, fit.explained_share


def decomposition_spectra(model_cache: dict) -> dict[str, np.ndarray]:
    """The variance spectrum (eigenvalues, descending) of every decomposition `fit_pca` fitted into `model_cache`.

    A sweep over n_components/variance_share/rotation fits one decomposition, so one spectrum; a sweep over
    standardize, dual or solver fits several, one per combination. Each is keyed by what defines it
    (e.g. "solver=blocks,standardize=False,dual=True"). Two cache entries that differ only in the resource
    knobs (chunk_columns, max_matrix_gib) would share a key and raise: they cannot be told apart by name."""
    spectra: dict[str, np.ndarray] = {}
    for key, fitted in model_cache.items():
        if key[0] == "blocks":
            _solver, standardize, dual, _resources = key
            label, eigenvalues = f"solver=blocks,standardize={standardize},dual={dual}", fitted.eigenvalues
        elif key[0] == "sklearn":
            label, eigenvalues = f"solver=sklearn,standardize={key[1]}", fitted[0].explained_variance_
        else:
            raise ValueError(f"model_cache entry {key!r} is not a pca decomposition")
        if label in spectra:
            raise ValueError(f"two pca decompositions share the spectrum key {label!r} (they differ only in chunk_columns/max_matrix_gib)")
        spectra[label] = eigenvalues
    if not spectra:
        raise ValueError("model_cache holds no pca decomposition - no spectrum to report")
    return spectra


def _fit_blocks(X: np.ndarray, given: dict, cache: dict) -> PcaFit:
    resources = {key: given[key] for key in ("chunk_columns", "max_matrix_gib") if key in given}
    key = ("blocks", given["standardize"], given["dual"], tuple(sorted(resources.items())))
    if key not in cache:
        cache[key] = fit_covariance_pca(X, standardize=given["standardize"], dual=given["dual"], **resources)
    pca = cache[key]
    n_components = resolve_n_components(pca.eigenvalues, given.get("n_components"), given.get("variance_share"))
    chunk = {"chunk_columns": given["chunk_columns"]} if "chunk_columns" in given else {}
    embedding = pca_embedding(X, pca, n_components, given["rotation"], given.get("rotation_max_iter"), **chunk)
    return PcaFit(embedding, n_components, float(pca.explained_variance_ratio[:n_components].sum()), pca.eigenvalues)


def _fit_sklearn(X: np.ndarray, given: dict, cache: dict) -> PcaFit:
    key = ("sklearn", given["standardize"])
    if key not in cache:
        means, scales = column_statistics(X, given["standardize"])
        scaled = (np.asarray(X, dtype=np.float64) - means) / scales
        cache[key] = (PCA(svd_solver="full").fit(scaled), scaled)
    fitted, scaled = cache[key]
    n_components = resolve_n_components(fitted.explained_variance_, given.get("n_components"), given.get("variance_share"))
    embedding = fitted.transform(scaled)[:, :n_components]
    return PcaFit(embedding, n_components, float(fitted.explained_variance_ratio_[:n_components].sum()), fitted.explained_variance_)


def _validate(given: dict) -> None:
    unknown = sorted(set(given) - _ALLOWED)
    if unknown:
        raise ValueError(f"pca: unknown param(s) {unknown} - allowed: {sorted(_ALLOWED)}")
    null = sorted(key for key, value in given.items() if value is None)
    if null:
        raise ValueError(f"pca: {null} are null - remove the key instead of setting it to null")
    missing = [key for key in _REQUIRED if key not in given]
    if missing:
        raise ValueError(f"pca requires {missing} in params")
    if given["solver"] not in SOLVERS:
        raise ValueError(f"pca: solver must be one of {list(SOLVERS)}, got {given['solver']!r}")
    if not isinstance(given["standardize"], bool):
        raise ValueError(f"pca: standardize must be true or false, got {given['standardize']!r}")
    if given["rotation"] not in SUPPORTED_ROTATIONS:
        raise ValueError(f"pca: rotation must be one of {list(SUPPORTED_ROTATIONS)}, got {given['rotation']!r}")
    if given["rotation"] != NO_ROTATION and "rotation_max_iter" not in given:
        raise ValueError(f"pca: rotation {given['rotation']!r} requires 'rotation_max_iter' in params")
    if given["solver"] == "sklearn":
        _validate_sklearn(given)
    else:
        _validate_blocks(given)


def _validate_sklearn(given: dict) -> None:
    blocks_only = [key for key in _BLOCKS_ONLY if key in given]
    if blocks_only:
        raise ValueError(f"pca: {blocks_only} only apply to solver 'blocks' - remove them for solver 'sklearn'")
    if given["rotation"] != NO_ROTATION:
        raise ValueError(f"pca: solver 'sklearn' does not rotate, rotation must be {NO_ROTATION!r}, got {given['rotation']!r} - use solver 'blocks'")


def _validate_blocks(given: dict) -> None:
    if "dual" not in given:
        raise ValueError("pca: solver 'blocks' requires 'dual' (true or false) in params - see docs/guides/dim_reduction.md for how to choose")
    if not isinstance(given["dual"], bool):
        raise ValueError(f"pca: dual must be true or false, got {given['dual']!r}")
