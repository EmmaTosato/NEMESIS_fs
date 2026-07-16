"""Serialization of a StepResult to/from a cache directory on disk.

A saved step directory always has this layout:
    X.npy
    metadata.csv
    extra_arrays/<name>.npy       (one file per StepResult.extra_arrays entry)
    extra_tables/<name>.csv       (one file per StepResult.extra_tables entry)
    manifest.json                 (written last - its presence marks the directory complete)

Writing is atomic at the directory level: everything is written into a
sibling temporary directory first, then that directory is renamed into place
in one step. A directory left behind by an interrupted write (e.g. the
process was killed mid-save) therefore never has a manifest.json, and is
never mistaken for a valid, complete cache entry - see is_valid_cache_dir().
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.step import StepResult

MANIFEST_FILENAME = "manifest.json"


def is_valid_cache_dir(step_dir: Path, expected_chain_hash: str) -> bool:
    """A cache hit requires the directory to exist AND contain a manifest
    whose chain_hash matches exactly - a truncated-hash directory-name
    collision or a leftover directory from an interrupted write must never
    be treated as a hit."""
    manifest_path = step_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return manifest.get("chain_hash") == expected_chain_hash


def save(step_dir: Path, result: StepResult, chain_hash: str) -> None:
    """Writes `result` into `step_dir`, atomically. Any existing content at
    `step_dir` is only replaced once the new content has been fully written
    to a temporary sibling directory."""
    step_dir.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(dir=step_dir.parent, prefix=f".{step_dir.name}.tmp-"))
    try:
        np.save(tmp_dir / "X.npy", result.X)
        result.metadata.to_csv(tmp_dir / "metadata.csv", index=False)

        if result.extra_arrays:
            (tmp_dir / "extra_arrays").mkdir()
            for name, array in result.extra_arrays.items():
                np.save(tmp_dir / "extra_arrays" / f"{name}.npy", array)

        if result.extra_tables:
            (tmp_dir / "extra_tables").mkdir()
            for name, table in result.extra_tables.items():
                table.to_csv(tmp_dir / "extra_tables" / f"{name}.csv", index=False)

        manifest = {
            "step_name": result.step_name,
            "chain_hash": chain_hash,
            "params_used": result.params_used,
            "X_shape": list(result.X.shape),
            "X_dtype": str(result.X.dtype),
            "metadata_columns": list(result.metadata.columns),
            "extra_arrays": sorted(result.extra_arrays),
            "extra_tables": sorted(result.extra_tables),
        }
        # written last on purpose: its presence is what marks this directory complete
        (tmp_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2))

        if step_dir.exists():
            shutil.rmtree(step_dir)
        shutil.move(str(tmp_dir), str(step_dir))
    except BaseException:
        # broad on purpose: this except exists only to guarantee the temp
        # directory is cleaned up regardless of failure, then re-raises
        # unchanged - it never swallows an error.
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


def load(step_dir: Path) -> StepResult:
    """Loads a previously-saved StepResult.

    Raises FileNotFoundError if `step_dir` has no manifest.json (not a valid
    cache directory - callers that only want a soft hit/miss check should
    call is_valid_cache_dir() first instead of catching this). Raises
    ValueError if the saved metadata's columns no longer match what the
    manifest recorded, which would otherwise let a step silently receive a
    metadata frame shaped differently than whatever produced it.
    """
    manifest_path = step_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"no manifest found at {manifest_path} - not a valid cache directory")
    manifest = json.loads(manifest_path.read_text())

    X = np.load(step_dir / "X.npy")
    metadata = pd.read_csv(step_dir / "metadata.csv")
    if list(metadata.columns) != manifest["metadata_columns"]:
        raise ValueError(
            f"{step_dir}: metadata.csv columns {list(metadata.columns)} do not match "
            f"manifest's recorded columns {manifest['metadata_columns']}"
        )

    extra_arrays = {
        name: np.load(step_dir / "extra_arrays" / f"{name}.npy") for name in manifest["extra_arrays"]
    }
    extra_tables = {
        name: pd.read_csv(step_dir / "extra_tables" / f"{name}.csv") for name in manifest["extra_tables"]
    }

    return StepResult(
        X=X,
        metadata=metadata,
        params_used=manifest["params_used"],
        step_name=manifest["step_name"],
        extra_arrays=extra_arrays,
        extra_tables=extra_tables,
    )
