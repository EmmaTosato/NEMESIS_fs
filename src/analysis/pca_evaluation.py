"""What the PCA evaluation notebook reads from an already-written `pca` run of dim_reduction.py.

notebooks/post-results_analysis/pca_evaluation.ipynb judges the components of one PCA, from either of the two
places dim_reduction.py leaves one:

- a production run (`matrix.npy` holds the scores, `eigenvalues.npy` the variance spectrum, `config.md` the
  params the run used);
- a tuning run (`embeddings.npz` holds the scores of every swept combination, `eigenvalues.npz` the spectrum of
  its decomposition). One combination of it is the run to judge: a PCA does not depend on how many components
  are kept, nor on the rotation, so the combinations are views of one decomposition.

Both are read into the same `PcaRun`. What is computed from it that the pipeline does not write is here, apart
from the voxel-wise maps, which are src/analysis/component_maps.py's.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.covariance_pca import DEFAULT_CHUNK_COLUMNS, NO_ROTATION, column_statistics
from src.analysis.tuning_embeddings import EMBEDDINGS_FILENAME, parse_combo_key
from src.utils.artifacts import (
    MATRIX_FILENAME,
    METADATA_FILENAME,
    read_dim_reduction_method,
    read_run_config,
    read_run_params,
)
from src.utils.participants import load_participants_registry

EIGENVALUES_PRODUCTION_FILENAME = "eigenvalues.npy"
EIGENVALUES_TUNING_FILENAME = "eigenvalues.npz"

# The scores of a rotated run have variance 1 by construction (src/analysis/covariance_pca.py::rotated_scores).
_UNIT_VARIANCE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class PcaRun:
    """One PCA to judge: its scores (subjects x components), the whole variance spectrum, and where it came from.

    `source_dir` is the feature matrix the PCA was computed on (its `input_path`): the rotated variance shares
    and the brain maps are computed from it, the scores alone do not hold them."""

    run_dir: Path
    kind: str  # "production" or "tuning"
    rotation: str
    n_components: int
    standardize: bool
    scores: np.ndarray
    eigenvalues: np.ndarray
    subject_ids: list[str]
    source_dir: Path


def load_pca_run(run_dir: Path, rotation: str | None = None, n_components: int | None = None) -> PcaRun:
    """The PCA in `run_dir`, a production run or a tuning run of dim_reduction.py with `pca`.

    A production run is read whole: `rotation` and `n_components` must not be given, they are the run's own.
    A tuning run has many combinations: `rotation` and `n_components` pick one, and a combination that was not
    swept raises with the ones that were. Raises ValueError for a directory that is neither, a run of another
    method, a tuning that swept anything else than rotation and n_components, or one with nested leaves."""
    run_dir = Path(run_dir)
    if (run_dir / MATRIX_FILENAME).is_file():
        if rotation is not None or n_components is not None:
            raise ValueError(f"{run_dir} is a production run: rotation and n_components are the run's own, do not pass them")
        return _load_production(run_dir)
    if (run_dir / EMBEDDINGS_FILENAME).is_file():
        if rotation is None or n_components is None:
            raise ValueError(f"{run_dir} is a tuning run: say which combination to judge with rotation and n_components")
        return _load_tuning(run_dir, rotation, n_components)
    raise ValueError(f"{run_dir} holds neither {MATRIX_FILENAME} (a production run) nor {EMBEDDINGS_FILENAME} (a tuning run with save_tuning_embeddings)")


def _load_production(run_dir: Path) -> PcaRun:
    method = read_dim_reduction_method(run_dir)
    if method != "pca":
        raise ValueError(f"{run_dir} is a {method!r} run, not a 'pca' one")
    params = read_run_params(run_dir)
    scores = np.load(run_dir / MATRIX_FILENAME)
    if scores.shape[1] != params["n_components"]:
        raise ValueError(f"{run_dir}: {scores.shape[1]} score columns but the run's params say n_components={params['n_components']}")
    return PcaRun(
        run_dir=run_dir,
        kind="production",
        rotation=params["rotation"],
        n_components=int(params["n_components"]),
        standardize=bool(params["standardize"]),
        scores=scores,
        eigenvalues=np.load(run_dir / EIGENVALUES_PRODUCTION_FILENAME),
        subject_ids=_subject_ids(run_dir, scores.shape[0]),
        source_dir=_source_dir(run_dir, read_run_config(run_dir)),
    )


def _load_tuning(run_dir: Path, rotation: str, n_components: int) -> PcaRun:
    config = read_run_config(run_dir)
    if config["reduction_method"] != "pca":
        raise ValueError(f"{run_dir} is a {config['reduction_method']!r} tuning, not a 'pca' one")
    if config["nested_params"]:
        raise ValueError(f"{run_dir} has nested leaves ({config['nested_params']}): point at one leaf folder, or run the tuning without nesting")
    swept = set(config["tuning_grid"])
    if not swept <= {"rotation", "n_components"}:
        raise ValueError(f"{run_dir} swept {sorted(swept - {'rotation', 'n_components'})} too: only rotation and n_components are supported, the other combinations are other decompositions")
    embeddings = np.load(run_dir / EMBEDDINGS_FILENAME)
    key = _combination_key(embeddings.files, config["base_params"], rotation, n_components, run_dir)
    scores = embeddings[key]
    return PcaRun(
        run_dir=run_dir,
        kind="tuning",
        rotation=rotation,
        n_components=n_components,
        standardize=bool(config["base_params"]["standardize"]),
        scores=scores,
        eigenvalues=_tuning_eigenvalues(run_dir),
        subject_ids=_subject_ids(run_dir, scores.shape[0]),
        source_dir=_source_dir(run_dir, config),
    )


def _combination_key(keys: list[str], base_params: dict, rotation: str, n_components: int, run_dir: Path) -> str:
    """The key of embeddings.npz for this combination: a parameter the grid did not sweep is not in the key, it is the base one."""
    wanted = {"rotation": rotation, "n_components": str(n_components)}
    matches = []
    for key in keys:
        effective = {name: str(base_params[name]) for name in wanted} | parse_combo_key(key)
        if effective == wanted:
            matches.append(key)
    if len(matches) != 1:
        raise ValueError(f"{run_dir}: {len(matches)} combinations match rotation={rotation!r}, n_components={n_components}; swept: {sorted(keys)}")
    return matches[0]


def _tuning_eigenvalues(run_dir: Path) -> np.ndarray:
    spectra = np.load(run_dir / EIGENVALUES_TUNING_FILENAME)
    if len(spectra.files) != 1:
        raise ValueError(f"{run_dir}'s {EIGENVALUES_TUNING_FILENAME} holds {len(spectra.files)} decompositions ({spectra.files}): only a tuning with one is supported")
    return spectra[spectra.files[0]]


def _subject_ids(run_dir: Path, n_subjects: int) -> list[str]:
    subject_ids = pd.read_csv(run_dir / METADATA_FILENAME)["subject_id"].tolist()
    if len(subject_ids) != n_subjects:
        raise ValueError(f"{run_dir}: {len(subject_ids)} subjects in {METADATA_FILENAME} but {n_subjects} score rows")
    return subject_ids


def _source_dir(run_dir: Path, config: dict) -> Path:
    source = Path(config["input_path"])
    if not source.is_dir():
        raise FileNotFoundError(f"{run_dir} was computed on {source}, which is not on this disk")
    return source


def load_source_matrix(run: PcaRun) -> np.ndarray:
    """The feature matrix `run` was computed on, memory-mapped, after checking that its rows are the run's subjects
    in the run's order: the scores and the matrix are paired row by row, so another order would give results that
    look fine and are wrong. Raises ValueError, naming the first difference, for a matrix that is not the run's."""
    matrix = np.load(run.source_dir / MATRIX_FILENAME, mmap_mode="r")
    source_ids = pd.read_csv(run.source_dir / METADATA_FILENAME)["subject_id"].tolist()
    if matrix.shape[0] != len(run.subject_ids) or source_ids != run.subject_ids:
        first = next((i for i, (a, b) in enumerate(zip(source_ids, run.subject_ids)) if a != b), min(len(source_ids), len(run.subject_ids)))
        raise ValueError(
            f"{run.source_dir} has {matrix.shape[0]} rows, the run {len(run.subject_ids)} subjects, and they are not the "
            f"same in the same order (first difference at row {first}): it is not the matrix this run was computed from"
        )
    return matrix


def rotated_variance_shares(
    X: np.ndarray, scores: np.ndarray, eigenvalues: np.ndarray, standardize: bool = False, chunk_columns: int = DEFAULT_CHUNK_COLUMNS
) -> np.ndarray:
    """The share of the total variance each rotated component explains, shape (n_components,).

    The scores of a rotated run are uncorrelated and have variance 1, so the loading of a voxel on a
    component is its covariance with that component's scores; the share is the sum of the squared loadings
    of the component over the total variance (the sum of `eigenvalues`). `X` is read a block of columns at
    a time, centered (and scaled if `standardize`) like the PCA did. Raises ValueError for scores that
    do not have variance 1 (an unrotated run's: their variance is the eigenvalue, and this is not their share)."""
    n_subjects = scores.shape[0]
    if X.ndim != 2 or X.shape[0] != n_subjects:
        raise ValueError(f"X {X.shape} does not have the {n_subjects} subjects of the scores")
    variances = scores.var(axis=0, ddof=1)
    if not np.allclose(variances, 1.0, atol=_UNIT_VARIANCE_TOLERANCE):
        raise ValueError(f"the scores do not have variance 1 (from {variances.min():.4g} to {variances.max():.4g}): they are not a rotated run's")
    means, scales = column_statistics(X, standardize, chunk_columns)
    centered_scores = scores - scores.mean(axis=0)
    squared_loadings = np.zeros(scores.shape[1])
    for start in range(0, X.shape[1], chunk_columns):
        stop = min(start + chunk_columns, X.shape[1])
        block = (np.asarray(X[:, start:stop], dtype=np.float64) - means[start:stop]) / scales[start:stop]
        squared_loadings += ((block.T @ centered_scores / (n_subjects - 1)) ** 2).sum(axis=0)
    return squared_loadings / eigenvalues.sum()


def default_embedding_components(rotation: str, rotated_shares: np.ndarray | None) -> tuple[int, int]:
    """The two components (0-based) to draw by default: the first two of an unrotated PCA (the directions that
    separate the subjects most), the two explaining most variance of a rotated one (its columns have no order).
    Raises ValueError for a rotated run without its shares."""
    if rotation == NO_ROTATION:
        return 0, 1
    if rotated_shares is None:
        raise ValueError(f"a {rotation!r} run's columns have no order: pass its rotated variance shares to pick the two to draw")
    first, second = np.argsort(rotated_shares)[::-1][:2]
    return int(first), int(second)


def registry_values(subject_ids: list[str], column: str) -> np.ndarray:
    """`column` of assets/metadata/participants.csv for these subjects, as floats, in this order.

    Raises ValueError for a subject that is not in the registry or has no value: a covariate with gaps would
    shift every correlation computed from it without any sign of it."""
    registry = load_participants_registry().set_index("subject_id")
    if column not in registry.columns:
        raise ValueError(f"participants.csv has no {column!r} column")
    missing = sorted(set(subject_ids) - set(registry.index))
    if missing:
        raise ValueError(f"{len(missing)} subjects are not in the registry: {missing[:5]}")
    values = pd.to_numeric(registry.loc[subject_ids, column], errors="raise").to_numpy(dtype=float)
    if np.isnan(values).any():
        raise ValueError(f"{int(np.isnan(values).sum())} subjects have no {column!r}")
    return values
