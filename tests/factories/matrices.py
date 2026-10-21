"""Matrici sintetiche per riduzione dimensionale e clustering (tutte deterministiche per seed)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.artifacts import save_matrix
from tests.factories.ids import DEFAULT_SITE, subject_ids


def gaussian_blobs(
    n_per_blob: int = 10,
    centers: tuple[tuple[float, ...], ...] = ((0.0, 0.0), (8.0, 8.0), (0.0, 8.0)),
    scale: float = 0.3,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """(X, true_labels): blob ben separati, per cui ogni metodo sensato ritrova i cluster veri."""
    rng = np.random.default_rng(seed)
    X = np.vstack([rng.normal(loc=c, scale=scale, size=(n_per_blob, len(c))) for c in centers])
    labels = np.repeat(np.arange(len(centers)), n_per_blob)
    return X, labels


def binary_matrix(n_rows: int = 12, n_cols: int = 40, density: float = 0.2, seed: int = 0) -> np.ndarray:
    """Matrice 0/1 float32 come `lesion_matrix`; ogni riga ha almeno un 1 (una lesione vuota non esiste)."""
    rng = np.random.default_rng(seed)
    X = (rng.random((n_rows, n_cols)) < density).astype(np.float32)
    empty = ~X.any(axis=1)
    X[empty, rng.integers(0, n_cols, size=int(empty.sum()))] = 1.0
    return X


def metadata_frame(n: int, site: str = DEFAULT_SITE, dataset: str = "siteA") -> pd.DataFrame:
    return pd.DataFrame({"subject_id": subject_ids(n, site), "dataset": [dataset] * n})


def write_matrix_artifact(directory, X: np.ndarray, metadata: pd.DataFrame | None = None, title: str = "# fixture"):
    """Scrive `matrix.npy` + `metadata.csv` + manifest con il vero `save_matrix` e ritorna la cartella."""
    metadata = metadata_frame(len(X)) if metadata is None else metadata
    save_matrix(directory, X, metadata, [title], overwrite=False)
    return directory
