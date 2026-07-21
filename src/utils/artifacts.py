"""Generic save/load for 2D feature-matrix artifacts (matrix + metadata + extra arrays).

Used by every analysis pipeline script (build/reduction/clustering) to write and
read its output directory. No caching/hashing: the caller decides the output
path (`output_root/<session_name>`) and whether re-running it is allowed
(`overwrite`) - this module only guarantees the write is atomic and that a
directory is never left half-written.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

MANIFEST_FILENAME = "manifest.json"
MATRIX_FILENAME = "matrix.npy"
METADATA_FILENAME = "metadata.csv"
README_FILENAME = "config.md"

_RESERVED_EXTRA_ARRAY_NAMES = {"matrix", "metadata", "manifest", "README"}


def save_matrix(
    output_dir: Path,
    X: np.ndarray,
    metadata: pd.DataFrame,
    readme_lines: list[str],
    overwrite: bool,
    extra_arrays: dict[str, np.ndarray] | None = None,
) -> Path:
    """Atomically write a matrix artifact to output_dir.

    Writes    `matrix.npy` (or `.npz`), `metadata.parquet`, optionally `extra_arrays.npz`,
    config.md, and manifest.json (last) to a temporary sibling directory, then
    renames it into place - output_dir either doesn't exist, or exists fully
    written, never partially.
    """
    output_dir = Path(output_dir)
    if output_dir.exists() and not overwrite:
        raise FileExistsError(
            f"output directory {output_dir} already exists and overwrite=False "
            "- set overwrite=True to replace it, or choose a different session_name"
        )
    if X.shape[0] != len(metadata):
        raise ValueError(
            f"matrix has {X.shape[0]} rows but metadata has {len(metadata)} rows - must match"
        )

    extra_arrays = extra_arrays or {}
    reserved_clash = _RESERVED_EXTRA_ARRAY_NAMES & extra_arrays.keys()
    if reserved_clash:
        raise ValueError(
            f"extra_arrays uses reserved name(s) {sorted(reserved_clash)}, "
            f"which collide with the artifact's own files ({sorted(_RESERVED_EXTRA_ARRAY_NAMES)})"
        )
    # No shape relationship to X is assumed or checked here: an extra array can be
    # subject-aligned (X.shape[0]), feature-aligned (X.shape[1], or the pre-drop
    # feature count), or something else entirely - that meaning belongs to the
    # caller (e.g. build_lesion_matrix.py's non_constant_mask is feature-aligned,
    # parcel_ids is aligned to X's post-drop columns).

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}_tmp_", dir=output_dir.parent))
    try:
        np.save(tmp_dir / MATRIX_FILENAME, X)
        metadata.to_csv(tmp_dir / METADATA_FILENAME, index=False)
        for name, array in extra_arrays.items():
            np.save(tmp_dir / f"{name}.npy", array)
        (tmp_dir / README_FILENAME).write_text("\n".join(readme_lines) + "\n")

        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "matrix_shape": list(X.shape),
            "matrix_dtype": str(X.dtype),
            "metadata_columns": list(metadata.columns),
            "extra_arrays": {name: list(array.shape) for name, array in extra_arrays.items()},
        }
        (tmp_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2))

        if output_dir.exists():
            shutil.rmtree(output_dir)
        tmp_dir.rename(output_dir)
    except BaseException:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise

    return output_dir


def load_matrix(input_dir: Path) -> tuple[np.ndarray, pd.DataFrame, dict[str, np.ndarray]]:
    """Load a matrix artifact previously written by save_matrix.

    Raises FileNotFoundError if input_dir has no manifest.json - either the
    artifact was never built, or a previous build was interrupted before the
    atomic rename completed (in which case it never appeared here at all).
    """
    input_dir = Path(input_dir)
    manifest_path = input_dir / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"{input_dir} has no {MANIFEST_FILENAME} - this artifact hasn't been built yet "
            "(or the build never completed); run the pipeline script that produces it first"
        )
    manifest = json.loads(manifest_path.read_text())

    X = np.load(input_dir / MATRIX_FILENAME)
    metadata = pd.read_csv(input_dir / METADATA_FILENAME)
    extra_arrays = {
        name: np.load(input_dir / f"{name}.npy") for name in manifest.get("extra_arrays", {})
    }

    return X, metadata, extra_arrays
