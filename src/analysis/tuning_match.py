"""Which stored clustering tuning runs reproduce a given agglomerative production run.

A production run and a tuning run are not the same run: they have different dates, and the tuning sweeps many
combinations while production fits one. What ties them is the matrix both clustered, recorded as `input_path` in each
config.md (the dim_reduction production run for a reduced run, the feature matrix for a raw one). A tuning run is
compatible with a production run when it

1. clustered the same `input_path`,
2. stored the production run's combination (`n_clusters`, `linkage`, `metric`) in clusterings.npz,
3. covers the same subjects, in the same order, and
4. its stored labels for that combination are the production labels (same partition, label names free).

The last two are checked on the files, not assumed from the first: a tuning directory reused by a later run (lessons
learned #18) or a production run refitted with another seed would otherwise be shown as a faithful picture of it.
"""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from src.analysis.clustering_tuning_analysis import (
    AGGLOMERATIVE,
    SWEPT_COLUMNS,
    ClusteringTuningRun,
    combo_key,
    load_clustering_tuning_run,
    read_run_config as read_tuning_config,
)
from src.utils.artifacts import read_run_config, read_run_params

CLUSTER_LABEL_COLUMN = "cluster_label"
METADATA_FILENAME = "metadata.csv"


@dataclass(frozen=True)
class TuningMatch:
    """A tuning run that clustered the same matrix as a production run: `reason_rejected` is None when it also
    reproduces the production labels, otherwise why it does not."""

    run_dir: Path
    reason_rejected: str | None

    @property
    def compatible(self) -> bool:
        return self.reason_rejected is None


def production_combination_key(params: dict) -> str:
    """The clusterings.npz key of the combination an agglomerative production run was fitted with. Raises ValueError
    when `params` lacks a swept column or holds a value of the wrong type: a run that does not record its `metric`
    cannot be matched, and its metric is not guessed from the library default."""
    columns = SWEPT_COLUMNS[AGGLOMERATIVE]
    missing = [column for column in columns if column not in params]
    if missing:
        raise ValueError(f"production params {params} lack {missing}: the combination cannot be matched to a tuning")
    n_clusters = params["n_clusters"]
    if not isinstance(n_clusters, int) or isinstance(n_clusters, bool) or n_clusters < 2:
        raise ValueError(f"production params: n_clusters must be an integer >= 2, got {n_clusters!r}")
    for column in ("linkage", "metric"):
        if not isinstance(params[column], str) or not params[column]:
            raise ValueError(f"production params: {column} must be a non-empty string, got {params[column]!r}")
    return combo_key(params, columns)


def _normalized(path: str | Path, base_dir: Path) -> Path:
    """`path` as an absolute path: config.md paths are relative to the working directory (`base_dir`), but an
    absolute one is legitimate and must still match its relative spelling."""
    return (base_dir / path).resolve()


def _read_subject_ids(run_dir: Path) -> list[str]:
    frame = pd.read_csv(run_dir / METADATA_FILENAME, dtype=str, keep_default_na=False)
    if "subject_id" not in frame.columns:
        raise ValueError(f"{run_dir / METADATA_FILENAME} has no subject_id column")
    return frame["subject_id"].tolist()


def _production_labels(production_dir: Path) -> tuple[list[str], np.ndarray]:
    path = production_dir / METADATA_FILENAME
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    for column in ("subject_id", CLUSTER_LABEL_COLUMN):
        if column not in frame.columns:
            raise ValueError(f"{path} has no {column} column: not a clustering production run")
    return frame["subject_id"].tolist(), frame[CLUSTER_LABEL_COLUMN].astype(int).to_numpy()


def _rejection_reason(
    tuning: ClusteringTuningRun, key: str, subjects: list[str], labels: np.ndarray
) -> str | None:
    """Why `tuning` does not reproduce the production labels of combination `key`, or None when it does."""
    if key not in tuning.labels:
        return f"combination {key} is not in clusterings.npz"
    if _read_subject_ids(tuning.run_dir) != subjects:
        return "its subjects (metadata.csv) are not the production subjects, in the same order"
    stored = tuning.labels[key]
    if len(stored) != len(labels):
        return f"{key} has {len(stored)} labels, the production run {len(labels)}"
    ari = adjusted_rand_score(labels, stored)
    if ari != 1.0:
        return f"its labels for {key} are not the production partition (ARI={ari:.4f})"
    return None


def find_compatible_tunings(production_dir: Path, tuning_root: Path, base_dir: Path) -> list[TuningMatch]:
    """Every agglomerative tuning run under `tuning_root` (results/<modality>/clustering/tuning/agglomerative) that
    clustered the same `input_path` as `production_dir`, each marked compatible or with why not, sorted by name.

    `base_dir` is the working directory the `input_path`s of the config.md files are relative to. A tuning run that
    clustered another matrix is not a candidate and is not returned; a candidate that cannot be read (no
    clusterings.npz, truncated archive) is returned as rejected, never dropped, so the caller can say why. A
    directory whose config.md cannot be parsed at all cannot be told apart from a candidate: it is logged and
    skipped, so one bad run does not hide the others.

    Raises ValueError when `production_dir` is not an agglomerative production run or its params cannot be matched
    (see production_combination_key).
    """
    config = read_run_config(production_dir)
    if config.get("clustering_method") != AGGLOMERATIVE:
        raise ValueError(f"{production_dir}: clustering_method is {config.get('clustering_method')!r}, expected {AGGLOMERATIVE!r}")
    input_path = config.get("input_path")
    if not isinstance(input_path, str) or not input_path:
        raise ValueError(f"{production_dir}: config.md has no usable input_path, got {input_path!r}")
    key = production_combination_key(read_run_params(production_dir))
    subjects, labels = _production_labels(production_dir)
    production_input = _normalized(input_path, base_dir)

    matches = []
    for run_dir in sorted(tuning_root.glob("*/*")):
        if not (run_dir / "config.md").is_file():
            continue
        try:
            tuning_config = read_tuning_config(run_dir)
            if not isinstance(tuning_config["input_path"], str) or not tuning_config["input_path"]:
                raise ValueError(f"input_path must be a non-empty string, got {tuning_config['input_path']!r}")
        except ValueError as exc:
            logging.warning("%s: cannot read its config.md, not considered as a tuning for %s: %s", run_dir, production_dir, exc)
            continue
        if tuning_config["clustering_method"] != AGGLOMERATIVE or _normalized(tuning_config["input_path"], base_dir) != production_input:
            continue
        try:
            reason = _rejection_reason(load_clustering_tuning_run(run_dir), key, subjects, labels)
        except (FileNotFoundError, ValueError, zipfile.BadZipFile, EOFError) as exc:
            reason = f"cannot be read ({type(exc).__name__}: {exc})"
        matches.append(TuningMatch(run_dir=run_dir, reason_rejected=reason))
    return matches
