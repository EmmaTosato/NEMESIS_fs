"""PCA on the covariance (or correlation) matrix, for matrices too wide to center in memory.

Replicates the "Data compression" step of Thiebaut de Schotten et al. 2020 (PCA on the covariance
matrix - centered, not scaled - then varimax rotation, scores by multiple regression) on matrices
like the voxel-wise SDC one (5845 x 291345 float32 = 6.8 GB), where `sklearn.decomposition.PCA`
cannot run: it makes several full float64 copies of X. Every pass over X reads a block at a time,
so peak memory is one block plus one square matrix, not the matrix.

Two equivalent ways to the same components, picked with `dual`:

- dual=True (the snapshot method): with Z = (X - column mean) [/ column std], the eigenvectors of
  Z^T Z / (n-1) with non-zero eigenvalue are Z^T u / s for the eigenvectors u (and singular values
  s) of the n x n Gram matrix Z Z^T, with the same eigenvalues s^2 / (n-1). Right when features
  outnumber subjects: the feature x feature matrix (291345 x 291345) is never built.
- dual=False: the p x p covariance matrix is built and decomposed directly. Right when subjects
  outnumber features (parcellated matrices).

`standardize` divides every column by its standard deviation first (PCA on the correlation matrix).
tests/unit/test_covariance_pca.py checks every combination against sklearn.decomposition.PCA.

Component maps (`component_t_maps`) are the voxel-wise counterpart of the scores, as in the paper's
Supplementary section B: for each voxel, a multiple regression of its values on the component scores,
reported as the t-statistic of each component's coefficient, computed in independent halves of the
subjects so the two maps of a component can be correlated (its reproducibility).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from factor_analyzer.rotator import ORTHOGONAL_ROTATIONS, Rotator

DEFAULT_CHUNK_COLUMNS = 16384
# The square matrix that is built and decomposed (n x n if dual, p x p if not), in float64. A request
# above this raises instead of trying to allocate it.
DEFAULT_MAX_MATRIX_GIB = 8.0
# An eigenvalue under this share of the largest one is numerical noise (after centering, n subjects
# have at most n-1 non-zero eigenvalues), not a component.
_RANK_TOLERANCE = 1e-10

NO_ROTATION = "none"
# Only orthogonal rotations: the regression scores below assume uncorrelated rotated components.
SUPPORTED_ROTATIONS = (NO_ROTATION, *ORTHOGONAL_ROTATIONS)


def nonzero_component_count(eigenvalues: np.ndarray) -> int:
    """How many components have variance above numerical noise (`eigenvalues` descending)."""
    return int((eigenvalues > _RANK_TOLERANCE * eigenvalues[0]).sum())


def components_for_share(eigenvalues: np.ndarray, share: float) -> int:
    """Smallest number of components whose cumulative explained variance reaches `share`."""
    if not 0.0 < share <= 1.0:
        raise ValueError(f"share must be in (0, 1], got {share!r}")
    cumulative = np.cumsum(eigenvalues / eigenvalues.sum())
    # The cumulative sum can stop a hair short of 1.0 (round-off), which would put share=1.0
    # one past the last component with variance.
    return min(int(np.searchsorted(cumulative, share) + 1), nonzero_component_count(eigenvalues))


@dataclass(frozen=True)
class CovariancePca:
    """The PCA of X: everything needed to rotate or project, without holding X.

    eigenvalues: variance of each component (denominator n-1), descending; length n if dual, p if not.
    column_means / column_scales: (p,) what was subtracted from / divided out of every column
        (scales are all 1.0 unless `standardized`).
    left_vectors: dual only, (n, n) eigenvectors of the Gram matrix; column i belongs to eigenvalues[i].
    right_vectors: not dual only, (p, p) eigenvectors of the covariance matrix, same convention.
    """

    eigenvalues: np.ndarray
    column_means: np.ndarray
    column_scales: np.ndarray
    standardized: bool
    n_samples: int
    left_vectors: np.ndarray | None = None
    right_vectors: np.ndarray | None = None

    def __post_init__(self) -> None:
        if (self.left_vectors is None) == (self.right_vectors is None):
            raise ValueError("give exactly one of left_vectors (dual PCA) and right_vectors (PCA on the covariance matrix)")
        n_features = len(self.column_means)
        if self.column_scales.shape != (n_features,):
            raise ValueError(f"column_scales has shape {self.column_scales.shape}, expected ({n_features},)")
        side = self.n_samples if self.dual else n_features
        vectors = self.left_vectors if self.dual else self.right_vectors
        if vectors.shape != (side, side) or self.eigenvalues.shape != (side,):
            raise ValueError(
                f"{'dual' if self.dual else 'covariance'} PCA needs {side} eigenvalues and a ({side}, {side}) "
                f"eigenvector matrix, got {self.eigenvalues.shape} and {vectors.shape}"
            )

    @property
    def dual(self) -> bool:
        return self.left_vectors is not None

    @property
    def n_features(self) -> int:
        return len(self.column_means)

    @property
    def explained_variance_ratio(self) -> np.ndarray:
        return self.eigenvalues / self.eigenvalues.sum()

    @property
    def cumulative_variance_ratio(self) -> np.ndarray:
        return np.cumsum(self.explained_variance_ratio)

    def n_nonzero_components(self) -> int:
        return nonzero_component_count(self.eigenvalues)

    def n_components_for(self, share: float) -> int:
        """Smallest number of components whose cumulative explained variance reaches `share`."""
        return components_for_share(self.eigenvalues, share)

    def save(self, path: Path) -> None:
        """Write the model to `path` (a .npz), temp file then rename so a killed run leaves no half file."""
        arrays = {
            "eigenvalues": self.eigenvalues,
            "column_means": self.column_means,
            "column_scales": self.column_scales,
            "standardized": np.array(self.standardized),
            "n_samples": np.array(self.n_samples),
        }
        arrays["left_vectors" if self.dual else "right_vectors"] = self.left_vectors if self.dual else self.right_vectors
        temporary = path.with_name(path.name + ".tmp")
        with temporary.open("wb") as handle:
            np.savez(handle, **arrays)
        temporary.replace(path)

    @classmethod
    def load(cls, path: Path) -> CovariancePca:
        with np.load(path) as stored:
            return cls(
                eigenvalues=stored["eigenvalues"],
                column_means=stored["column_means"],
                column_scales=stored["column_scales"],
                standardized=bool(stored["standardized"]),
                n_samples=int(stored["n_samples"]),
                left_vectors=stored["left_vectors"] if "left_vectors" in stored else None,
                right_vectors=stored["right_vectors"] if "right_vectors" in stored else None,
            )


def fit_covariance_pca(
    X: np.ndarray,
    standardize: bool = False,
    dual: bool = True,
    chunk_columns: int = DEFAULT_CHUNK_COLUMNS,
    max_matrix_gib: float = DEFAULT_MAX_MATRIX_GIB,
) -> CovariancePca:
    """PCA of the covariance matrix of X (or its correlation matrix if `standardize`).

    X may be a memory-mapped array: it is read `chunk_columns` columns at a time (dual) or in row
    chunks of the same size (not dual), and never copied whole.
    """
    _require_matrix(X, chunk_columns)
    n_samples, n_features = X.shape
    _require_square_matrix_fits(n_samples, n_features, dual, max_matrix_gib)
    means, scales = column_statistics(X, standardize, chunk_columns)
    if dual:
        eigenvalues, vectors = _descending_eigh(_gram_matrix(X, means, scales, chunk_columns), n_samples - 1)
        return CovariancePca(eigenvalues, means, scales, standardize, n_samples, left_vectors=vectors)
    eigenvalues, vectors = _descending_eigh(_covariance_matrix(X, means, scales, chunk_columns), n_samples - 1)
    return CovariancePca(eigenvalues, means, scales, standardize, n_samples, right_vectors=vectors)


def resolve_n_components(eigenvalues: np.ndarray, n_components: int | None, variance_share: float | None) -> int:
    """How many components to keep: `n_components` as given, or as many as `variance_share` of the variance needs.
    Exactly one of the two must be given. `eigenvalues` are the PCA's, descending."""
    if (n_components is None) == (variance_share is None):
        raise ValueError(
            f"give exactly one of n_components and variance_share, got n_components={n_components!r} "
            f"and variance_share={variance_share!r}"
        )
    if variance_share is not None:
        return components_for_share(eigenvalues, variance_share)
    available = nonzero_component_count(eigenvalues)
    if isinstance(n_components, bool) or not isinstance(n_components, int) or not 1 <= n_components <= available:
        raise ValueError(
            f"n_components must be an integer between 1 and {available} (components with non-zero variance), "
            f"got {n_components!r}"
        )
    return n_components


def pca_scores(X: np.ndarray, pca: CovariancePca, n_components: int, chunk_columns: int = DEFAULT_CHUNK_COLUMNS) -> np.ndarray:
    """Scores of the first `n_components` (unrotated) components, shape (n_samples, n_components): the
    same values as sklearn's PCA.transform (of X scaled by `pca.column_scales`), up to the sign of each column."""
    _require_fitted_matrix(X, pca, chunk_columns)
    _require_component_count(pca, n_components)
    if pca.dual:
        scale = np.sqrt(pca.eigenvalues[:n_components] * (pca.n_samples - 1))
        return pca.left_vectors[:, :n_components] * scale
    scores = np.empty((pca.n_samples, n_components), dtype=np.float64)
    for start, stop in _row_chunks(pca.n_samples, pca.n_features, chunk_columns):
        scores[start:stop] = _scaled_rows(X, start, stop, pca) @ pca.right_vectors[:, :n_components]
    return scores


def rotated_scores(
    X: np.ndarray,
    pca: CovariancePca,
    n_components: int,
    rotation: str,
    max_iter: int,
    chunk_columns: int = DEFAULT_CHUNK_COLUMNS,
) -> tuple[np.ndarray, np.ndarray]:
    """Rotate the first `n_components` components and extract their scores.

    Same steps as the paper: factor loadings (eigenvector * sqrt(eigenvalue), not the raw unit-norm
    eigenvectors) are rotated, then each subject's score is the multiple-regression coefficient of
    its centered (and scaled) row onto the rotated loadings.

    Returns (scores (n_samples, n_components), rotated_loadings (n_features, n_components)).
    """
    _require_fitted_matrix(X, pca, chunk_columns)
    if rotation not in ORTHOGONAL_ROTATIONS:
        raise ValueError(
            f"rotation {rotation!r} is not an orthogonal rotation, supported: {list(ORTHOGONAL_ROTATIONS)} "
            f"(use {NO_ROTATION!r} for no rotation; oblique rotations need a different score formula)"
        )
    if n_components < 2:
        raise ValueError(
            f"a rotation needs n_components >= 2 (it rotates *between* components - there is nothing to "
            f"rotate with a single one), got {n_components!r}"
        )
    _require_component_count(pca, n_components)

    rotated = Rotator(method=rotation, max_iter=max_iter).fit_transform(_loadings(X, pca, n_components, chunk_columns))

    # lstsq(rotated, Z^T) in normal-equation form, accumulated block by block:
    # (R^T R) B = R^T Z^T, with R^T Z^T summed over column blocks.
    projection = np.zeros((n_components, pca.n_samples), dtype=np.float64)
    for start, stop in _column_blocks(pca.n_features, chunk_columns):
        projection += rotated[start:stop].T @ _scaled_columns(X, start, stop, pca).T
    coefficients = np.linalg.solve(rotated.T @ rotated, projection)
    return coefficients.T, rotated


def leading_rotated_scores(
    X: np.ndarray,
    pca: CovariancePca,
    n_rotated: int,
    n_kept: int,
    rotation: str,
    max_iter: int,
    chunk_columns: int = DEFAULT_CHUNK_COLUMNS,
) -> tuple[np.ndarray, float]:
    """Rotate the first `n_rotated` components, keep the `n_kept` rotated ones that explain the most variance.

    A rotated component has no place in the PCA's order (its score has variance 1 whatever it explains), so the
    kept ones are picked by the variance they explain - the sum of the squared loadings of the component over
    the total variance - and returned most first, the order an unrotated PCA has.

    Returns (scores (n_samples, n_kept), the share of the total variance the kept components explain)."""
    if not 1 <= n_kept <= n_rotated:
        raise ValueError(f"n_kept must be between 1 and n_rotated={n_rotated!r} (the components rotated), got {n_kept!r}")
    scores, loadings = rotated_scores(X, pca, n_rotated, rotation, max_iter, chunk_columns)
    shares = (loadings**2).sum(axis=0) / pca.eigenvalues.sum()
    kept = np.argsort(-shares, kind="stable")[:n_kept]
    return scores[:, kept], float(shares[kept].sum())


def pca_embedding(
    X: np.ndarray,
    pca: CovariancePca,
    n_components: int,
    rotation: str,
    max_iter: int,
    chunk_columns: int = DEFAULT_CHUNK_COLUMNS,
) -> np.ndarray:
    """The subjects x components matrix: unrotated scores if `rotation` is "none", else rotated scores."""
    if rotation not in SUPPORTED_ROTATIONS:
        raise ValueError(f"rotation must be one of {list(SUPPORTED_ROTATIONS)}, got {rotation!r}")
    if rotation == NO_ROTATION:
        return pca_scores(X, pca, n_components, chunk_columns)
    return rotated_scores(X, pca, n_components, rotation, max_iter, chunk_columns)[0]


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


def _require_square_matrix_fits(n_samples: int, n_features: int, dual: bool, max_matrix_gib: float) -> None:
    side = n_samples if dual else n_features
    gib = side * side * 8 / 2**30
    if gib > max_matrix_gib:
        other = "dual=False" if dual else "dual=True"
        raise ValueError(
            f"dual={dual} builds a {side} x {side} float64 matrix ({gib:.1f} GiB), above max_matrix_gib={max_matrix_gib}: "
            f"X has {n_samples} subjects and {n_features} features - try {other}, or raise max_matrix_gib"
        )


def column_statistics(X: np.ndarray, standardize: bool, chunk_columns: int = DEFAULT_CHUNK_COLUMNS) -> tuple[np.ndarray, np.ndarray]:
    """Column means, and column standard deviations (ddof=1) if `standardize` else ones. Raises on NaN/inf,
    and on a constant column when standardizing."""
    n_features = X.shape[1]
    means = np.empty(n_features, dtype=np.float64)
    scales = np.ones(n_features, dtype=np.float64)
    for start, stop in _column_blocks(n_features, chunk_columns):
        block = np.asarray(X[:, start:stop], dtype=np.float64)
        if not np.isfinite(block).all():
            raise ValueError(
                f"X has {int((~np.isfinite(block)).sum())} NaN or infinite value(s) in columns {start}:{stop} - "
                "a PCA is undefined on them, drop or fill those subjects/columns first"
            )
        means[start:stop] = block.mean(axis=0)
        if standardize:
            scales[start:stop] = block.std(axis=0, ddof=1)
    constant = np.flatnonzero(scales == 0)
    if len(constant):
        raise ValueError(
            f"standardize=True needs every column to vary across subjects, but {len(constant)} column(s) are "
            f"constant (first indices: {constant[:10].tolist()}) - drop them first, or use standardize=False"
        )
    return means, scales


def _gram_matrix(X: np.ndarray, means: np.ndarray, scales: np.ndarray, chunk_columns: int) -> np.ndarray:
    gram = np.zeros((X.shape[0], X.shape[0]), dtype=np.float64)
    for start, stop in _column_blocks(X.shape[1], chunk_columns):
        block = (np.asarray(X[:, start:stop], dtype=np.float64) - means[start:stop]) / scales[start:stop]
        gram += block @ block.T
    return gram


def _covariance_matrix(X: np.ndarray, means: np.ndarray, scales: np.ndarray, chunk_columns: int) -> np.ndarray:
    n_samples, n_features = X.shape
    covariance = np.zeros((n_features, n_features), dtype=np.float64)
    for start, stop in _row_chunks(n_samples, n_features, chunk_columns):
        rows = (np.asarray(X[start:stop], dtype=np.float64) - means) / scales
        covariance += rows.T @ rows
    return covariance


def _descending_eigh(symmetric: np.ndarray, divisor: int) -> tuple[np.ndarray, np.ndarray]:
    # eigh returns ascending order; tiny negative eigenvalues are round-off on a positive
    # semi-definite matrix.
    eigenvalues, vectors = np.linalg.eigh(symmetric)
    order = np.argsort(eigenvalues)[::-1]
    return np.clip(eigenvalues[order], 0.0, None) / divisor, vectors[:, order]


def _loadings(X: np.ndarray, pca: CovariancePca, n_components: int, chunk_columns: int) -> np.ndarray:
    """Factor loadings (n_features, n_components): eigenvector * sqrt(eigenvalue)."""
    variances = pca.eigenvalues[:n_components]
    if not pca.dual:
        return pca.right_vectors[:, :n_components] * np.sqrt(variances)
    singular_values = np.sqrt(variances * (pca.n_samples - 1))
    left = pca.left_vectors[:, :n_components]
    loadings = np.empty((pca.n_features, n_components), dtype=np.float64)
    for start, stop in _column_blocks(pca.n_features, chunk_columns):
        eigenvectors = _scaled_columns(X, start, stop, pca).T @ left / singular_values
        loadings[start:stop] = eigenvectors * np.sqrt(variances)
    return loadings


def _scaled_columns(X: np.ndarray, start: int, stop: int, pca: CovariancePca) -> np.ndarray:
    return (np.asarray(X[:, start:stop], dtype=np.float64) - pca.column_means[start:stop]) / pca.column_scales[start:stop]


def _scaled_rows(X: np.ndarray, start: int, stop: int, pca: CovariancePca) -> np.ndarray:
    return (np.asarray(X[start:stop], dtype=np.float64) - pca.column_means) / pca.column_scales


def _require_fitted_matrix(X: np.ndarray, pca: CovariancePca, chunk_columns: int) -> None:
    _require_matrix(X, chunk_columns)
    if X.shape != (pca.n_samples, pca.n_features):
        raise ValueError(f"X has shape {X.shape} but the PCA was fitted on ({pca.n_samples}, {pca.n_features})")


def _require_component_count(pca: CovariancePca, n_components: int) -> None:
    if not 1 <= n_components <= pca.n_nonzero_components():
        raise ValueError(
            f"n_components must be between 1 and {pca.n_nonzero_components()} (components with "
            f"non-zero variance), got {n_components!r}"
        )


def _row_chunks(n_samples: int, n_features: int, chunk_columns: int):
    """Row ranges holding about as many values as a block of `chunk_columns` columns."""
    rows = max(1, chunk_columns * n_samples // n_features)
    for start in range(0, n_samples, rows):
        yield start, min(start + rows, n_samples)
