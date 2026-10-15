"""Covariance PCA + varimax for a subjects x features matrix too wide to center in memory.

Replicates the "Data compression" step of Thiebaut de Schotten et al. 2020 (PCA on the covariance
matrix - centered, not scaled - then varimax rotation, scores by multiple regression) on matrices
like the voxel-wise SDC one (5845 x 291345 float32 = 6.8 GB), where `pca_varimax_embed`
(src/analysis/reduction.py) cannot run: it makes several full float64 copies of X.

The covariance matrix over features (291345 x 291345) is never built. With Xc = X - column mean,
the eigenvectors of Xc^T Xc / (n-1) with non-zero eigenvalue are Xc^T u / s for the eigenvectors u
(and singular values s) of the small Gram matrix Xc Xc^T (n x n), with the same eigenvalues
s^2 / (n-1): the same components as PCA, to numerical precision (tests/unit/test_covariance_pca.py
checks it against sklearn.decomposition.PCA). Every pass over X reads a block of columns at a time,
so peak memory is one block, not the matrix.

Component maps (`component_t_maps`) are the voxel-wise counterpart of the scores, as in the paper's
Supplementary section B: for each voxel, a multiple regression of its values on the component scores,
reported as the t-statistic of each component's coefficient, computed in independent halves of the
subjects so the two maps of a component can be correlated (its reproducibility).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from factor_analyzer import Rotator

DEFAULT_CHUNK_COLUMNS = 16384
# An eigenvalue under this share of the largest one is numerical noise (the Gram matrix of n
# subjects has at most n-1 non-zero eigenvalues after centering), not a component.
_RANK_TOLERANCE = 1e-10


@dataclass(frozen=True)
class CovariancePca:
    """The PCA of X: everything needed to rotate or project, without holding X.

    eigenvalues: variance of each component (denominator n-1), descending, length n.
    left_vectors: (n, n) eigenvectors of the Gram matrix; column i belongs to eigenvalues[i].
    column_means: (n_features,) mean subtracted from every column.
    """

    eigenvalues: np.ndarray
    left_vectors: np.ndarray
    column_means: np.ndarray

    @property
    def n_samples(self) -> int:
        return len(self.eigenvalues)

    @property
    def explained_variance_ratio(self) -> np.ndarray:
        return self.eigenvalues / self.eigenvalues.sum()

    @property
    def cumulative_variance_ratio(self) -> np.ndarray:
        return np.cumsum(self.explained_variance_ratio)

    def n_components_for(self, share: float) -> int:
        """Smallest number of components whose cumulative explained variance reaches `share`."""
        if not 0.0 < share <= 1.0:
            raise ValueError(f"share must be in (0, 1], got {share!r}")
        # The cumulative sum can stop a hair short of 1.0 (round-off), which would put share=1.0
        # one past the last component.
        return min(int(np.searchsorted(self.cumulative_variance_ratio, share) + 1), self.n_samples)

    def pca_scores(self, n_components: int) -> np.ndarray:
        """Scores of the first `n_components` (unrotated) components, shape (n_samples, n_components):
        the same values as sklearn's PCA.transform, up to the sign of each column."""
        if not 1 <= n_components <= self.n_nonzero_components():
            raise ValueError(
                f"n_components must be between 1 and {self.n_nonzero_components()} (components with "
                f"non-zero variance), got {n_components!r}"
            )
        scale = np.sqrt(self.eigenvalues[:n_components] * (self.n_samples - 1))
        return self.left_vectors[:, :n_components] * scale

    def n_nonzero_components(self) -> int:
        return int((self.eigenvalues > _RANK_TOLERANCE * self.eigenvalues[0]).sum())


def fit_covariance_pca(X: np.ndarray, chunk_columns: int = DEFAULT_CHUNK_COLUMNS) -> CovariancePca:
    """PCA of the covariance matrix of X (centered, not scaled), from X's Gram matrix.

    X may be a memory-mapped array: it is read `chunk_columns` columns at a time and never copied
    whole.
    """
    _require_matrix(X, chunk_columns)
    n_samples, n_features = X.shape
    means = np.empty(n_features, dtype=np.float64)
    for start, stop in _column_blocks(n_features, chunk_columns):
        means[start:stop] = np.asarray(X[:, start:stop], dtype=np.float64).mean(axis=0)

    gram = np.zeros((n_samples, n_samples), dtype=np.float64)
    for start, stop in _column_blocks(n_features, chunk_columns):
        block = np.asarray(X[:, start:stop], dtype=np.float64) - means[start:stop]
        gram += block @ block.T

    # eigh returns ascending order; tiny negative eigenvalues are round-off on a positive
    # semi-definite matrix.
    eigenvalues, vectors = np.linalg.eigh(gram)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.clip(eigenvalues[order], 0.0, None) / (n_samples - 1)
    return CovariancePca(eigenvalues=eigenvalues, left_vectors=vectors[:, order], column_means=means)


def varimax_scores(
    X: np.ndarray,
    pca: CovariancePca,
    n_components: int,
    max_iter: int,
    chunk_columns: int = DEFAULT_CHUNK_COLUMNS,
) -> tuple[np.ndarray, np.ndarray]:
    """Varimax-rotate the first `n_components` components and extract their scores.

    Same steps as `pca_varimax_embed` (src/analysis/reduction.py), without ever centering X as a
    whole: factor loadings (eigenvector * sqrt(eigenvalue), not the raw unit-norm eigenvectors)
    are rotated with varimax, then each subject's score is the multiple-regression coefficient of
    its centered row onto the rotated loadings.

    Returns (scores (n_samples, n_components), rotated_loadings (n_features, n_components)).
    """
    _require_matrix(X, chunk_columns)
    if X.shape[0] != pca.n_samples or X.shape[1] != len(pca.column_means):
        raise ValueError(f"X has shape {X.shape} but the PCA was fitted on ({pca.n_samples}, {len(pca.column_means)})")
    if n_components < 2:
        raise ValueError(
            f"varimax needs n_components >= 2 (it rotates *between* components - there is nothing to "
            f"rotate with a single one), got {n_components!r}"
        )
    if n_components > pca.n_nonzero_components():
        raise ValueError(
            f"n_components={n_components} exceeds the {pca.n_nonzero_components()} components with "
            "non-zero variance in this matrix"
        )

    variances = pca.eigenvalues[:n_components]
    left = pca.left_vectors[:, :n_components]
    singular_values = np.sqrt(variances * (pca.n_samples - 1))
    loadings = np.empty((X.shape[1], n_components), dtype=np.float64)
    for start, stop in _column_blocks(X.shape[1], chunk_columns):
        centered = np.asarray(X[:, start:stop], dtype=np.float64) - pca.column_means[start:stop]
        eigenvectors = centered.T @ left / singular_values
        loadings[start:stop] = eigenvectors * np.sqrt(variances)

    rotated = Rotator(method="varimax", max_iter=max_iter).fit_transform(loadings)

    # lstsq(rotated, Xc^T) in normal-equation form, accumulated block by block:
    # (R^T R) B = R^T Xc^T, with R^T Xc^T summed over column blocks.
    projection = np.zeros((n_components, pca.n_samples), dtype=np.float64)
    for start, stop in _column_blocks(X.shape[1], chunk_columns):
        centered = np.asarray(X[:, start:stop], dtype=np.float64) - pca.column_means[start:stop]
        projection += rotated[start:stop].T @ centered.T
    coefficients = np.linalg.solve(rotated.T @ rotated, projection)
    return coefficients.T, rotated


def squared_correlation(scores: np.ndarray, covariate: np.ndarray) -> np.ndarray:
    """R^2 of a one-variable linear regression of `covariate` on each column of `scores`
    (the squared Pearson correlation), shape (n_components,)."""
    if scores.ndim != 2 or covariate.shape != (scores.shape[0],):
        raise ValueError(f"scores {scores.shape} and covariate {covariate.shape} do not align")
    if np.isnan(covariate).any():
        raise ValueError("covariate contains NaN - drop or fill those subjects before correlating")
    if np.ptp(covariate) == 0:
        raise ValueError("covariate is constant - a correlation is undefined")
    centered_scores = scores - scores.mean(axis=0)
    centered_covariate = covariate - covariate.mean()
    covariance = centered_scores.T @ centered_covariate
    denominator = np.sqrt((centered_scores**2).sum(axis=0) * (centered_covariate**2).sum())
    return (covariance / denominator) ** 2


@dataclass(frozen=True)
class ComponentMaps:
    """t-statistic maps of the components, from one subset of subjects.

    t: (n_components, n_features). n_rows: how many subjects the regression used.
    n_degenerate_voxels: voxels with no residual variance within this subset (constant there, or
    fitted exactly), where a t-statistic is undefined; their t is set to 0.0 and they are counted
    here, never dropped.
    """

    t: np.ndarray
    n_rows: int
    n_degenerate_voxels: int


def component_t_maps(
    X: np.ndarray,
    scores: np.ndarray,
    row_sets: list[np.ndarray],
    chunk_columns: int = DEFAULT_CHUNK_COLUMNS,
) -> list[ComponentMaps]:
    """For each subset of subjects in `row_sets`, the voxel-wise t-map of every component.

    For every voxel, `values ~ intercept + all component scores` is fitted by least squares on the
    subset's rows (a multiple regression: the components enter together, not one at a time) and the
    t-statistic of each component's coefficient is returned. One pass over X serves every subset.
    The scores are the ones from the whole sample (`varimax_scores`): a half-sample map explains
    the same components, it does not re-derive them.
    """
    _require_matrix(X, chunk_columns)
    if scores.ndim != 2 or scores.shape[0] != X.shape[0]:
        raise ValueError(f"scores {scores.shape} do not match X with {X.shape[0]} rows")
    n_components = scores.shape[1]
    designs = [_RegressionDesign(scores, rows, n_components) for rows in row_sets]
    t_maps = [np.zeros((n_components, X.shape[1])) for _ in row_sets]
    degenerate = [0] * len(row_sets)
    for start, stop in _column_blocks(X.shape[1], chunk_columns):
        block = np.asarray(X[:, start:stop], dtype=np.float64)
        for i, design in enumerate(designs):
            t_block, n_degenerate = design.t_statistics(block[design.rows])
            t_maps[i][:, start:stop] = t_block
            degenerate[i] += n_degenerate
    return [
        ComponentMaps(t=t_map, n_rows=len(design.rows), n_degenerate_voxels=n)
        for t_map, design, n in zip(t_maps, designs, degenerate)
    ]


def map_reproducibility(maps_a: np.ndarray, maps_b: np.ndarray) -> np.ndarray:
    """Pearson correlation, across voxels, between the two maps of each component, shape (n_components,).

    A component whose map is constant in either half has no defined correlation and raises."""
    if maps_a.shape != maps_b.shape or maps_a.ndim != 2:
        raise ValueError(f"the two sets of maps must have the same 2D shape, got {maps_a.shape} and {maps_b.shape}")
    centered_a = maps_a - maps_a.mean(axis=1, keepdims=True)
    centered_b = maps_b - maps_b.mean(axis=1, keepdims=True)
    denominator = np.sqrt((centered_a**2).sum(axis=1) * (centered_b**2).sum(axis=1))
    if (denominator == 0).any():
        raise ValueError(f"component(s) {np.flatnonzero(denominator == 0).tolist()} have a constant map in one half")
    return (centered_a * centered_b).sum(axis=1) / denominator


def positive_peak_signs(t_maps: np.ndarray) -> np.ndarray:
    """+1/-1 per component, so that multiplying a map by it makes its largest-magnitude voxel positive.

    The sign of a component is arbitrary (flipping a component and its scores changes nothing), so
    maps are oriented by their strongest voxel, as the paper reports only positive correlations."""
    peak = np.argmax(np.abs(t_maps), axis=1)
    return np.where(t_maps[np.arange(t_maps.shape[0]), peak] >= 0, 1.0, -1.0)


class _RegressionDesign:
    """The regression `voxel ~ intercept + scores` on one subset of rows, ready to be applied to blocks of voxels."""

    def __init__(self, scores: np.ndarray, rows: np.ndarray, n_components: int) -> None:
        rows = np.asarray(rows)
        if rows.ndim != 1 or len(rows) <= n_components + 1:
            raise ValueError(f"a subset needs more than {n_components + 1} rows to fit {n_components} components, got {len(rows)}")
        if len(np.unique(rows)) != len(rows):
            raise ValueError("a subset lists the same row more than once")
        self.rows = rows
        self.scores = scores[rows] - scores[rows].mean(axis=0)
        gram = self.scores.T @ self.scores
        self.gram_inverse = np.linalg.inv(gram)
        self.degrees_of_freedom = len(rows) - n_components - 1

    def t_statistics(self, values: np.ndarray) -> tuple[np.ndarray, int]:
        centered = values - values.mean(axis=0)
        projection = self.scores.T @ centered
        coefficients = self.gram_inverse @ projection
        residual_ss = (centered**2).sum(axis=0) - (coefficients * projection).sum(axis=0)
        # Round-off can leave a residual a hair below zero on a voxel that is fitted perfectly.
        degenerate = residual_ss <= 1e-12 * np.maximum((centered**2).sum(axis=0), 1e-300)
        residual_variance = np.where(degenerate, 1.0, residual_ss / self.degrees_of_freedom)
        standard_error = np.sqrt(np.diag(self.gram_inverse)[:, None] * residual_variance[None, :])
        t = coefficients / standard_error
        t[:, degenerate] = 0.0
        return t, int(degenerate.sum())


def _require_matrix(X: np.ndarray, chunk_columns: int) -> None:
    if X.ndim != 2 or X.shape[0] < 3:
        raise ValueError(f"X must be a 2D matrix with at least 3 rows, got shape {X.shape}")
    if chunk_columns < 1:
        raise ValueError(f"chunk_columns must be >= 1, got {chunk_columns!r}")


def _column_blocks(n_features: int, chunk_columns: int):
    for start in range(0, n_features, chunk_columns):
        yield start, min(start + chunk_columns, n_features)
