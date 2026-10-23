"""Unit tests for src/analysis/tuning_match.py."""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.analysis.tuning_match import find_compatible_tunings, production_combination_key

SUBJECTS = [f"sub-STUNIPD{i:04d}" for i in range(6)]
LABELS = np.array([0, 0, 1, 1, 2, 2])
PARAMS = {"n_clusters": 3, "linkage": "ward", "metric": "euclidean"}
KEY = "n_clusters=3,linkage=ward,metric=euclidean"
INPUT_PATH = "results/sdc/dim_reduction/production/umap/16-10_s2.4-vol_m_euclidean_nc2"


def _config_md(config: dict, params: dict | None = None) -> str:
    text = f"# run\n\n## Config\n\n```json\n{json.dumps(config)}\n```\n"
    return text + (f"\n## Summary\n\nParams used: {json.dumps(params)}\n" if params is not None else "")


def _write_production(
    run_dir: Path, params: dict = PARAMS, labels: np.ndarray = LABELS, input_path: str = INPUT_PATH, method: str = "agglomerative"
) -> Path:
    run_dir.mkdir(parents=True)
    config = {"clustering_method": method, "input_path": input_path, "fine_tuning": False}
    (run_dir / "config.md").write_text(_config_md(config, params))
    pd.DataFrame({"subject_id": SUBJECTS, "dataset": "UNIPD", "cluster_label": labels}).to_csv(run_dir / "metadata.csv", index=False)
    return run_dir


def _write_tuning(
    run_dir: Path,
    input_path: str = INPUT_PATH,
    labels: dict[str, np.ndarray] | None = None,
    subjects: list[str] = SUBJECTS,
    write_npz: bool = True,
) -> Path:
    run_dir.mkdir(parents=True)
    config = {"clustering_method": "agglomerative", "input_path": input_path, "fine_tuning": True}
    (run_dir / "config.md").write_text(_config_md(config))
    labels = {KEY: LABELS, "n_clusters=2,linkage=ward,metric=euclidean": np.array([0, 0, 0, 1, 1, 1])} if labels is None else labels
    rows = [dict(zip(("n_clusters", "linkage", "metric"), key.replace("=", ",").split(",")[1::2])) for key in labels]
    pd.DataFrame(rows).to_csv(run_dir / "tuning_results.csv", index=False)
    pd.DataFrame({"subject_id": subjects, "dataset": "UNIPD"}).to_csv(run_dir / "metadata.csv", index=False)
    if write_npz:
        np.savez(run_dir / "clusterings.npz", **labels)
    return run_dir


@pytest.fixture
def layout(tmp_path: Path) -> tuple[Path, Path, Path]:
    """(production run, tuning root, base dir)."""
    production = _write_production(tmp_path / "production" / "umap" / "16-10_s2.4-vol_nc2_k3_link_ward")
    return production, tmp_path / "tuning", tmp_path


def test_same_matrix_same_labels_is_compatible_even_with_other_label_names(layout):
    production, tuning_root, base_dir = layout
    renamed = {KEY: np.array([7, 7, 4, 4, 9, 9]), "n_clusters=2,linkage=ward,metric=euclidean": np.array([0, 0, 0, 1, 1, 1])}
    tuning = _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2", labels=renamed)

    matches = find_compatible_tunings(production, tuning_root, base_dir)

    assert [(m.run_dir, m.compatible) for m in matches] == [(tuning, True)]


def test_a_tuning_of_another_matrix_is_not_a_candidate(layout):
    production, tuning_root, base_dir = layout
    _write_tuning(tuning_root / "umap" / "10-09_s2.2-vol_nc2", input_path="results/sdc/dim_reduction/production/umap/other")

    assert find_compatible_tunings(production, tuning_root, base_dir) == []


def test_absolute_and_relative_input_path_are_the_same_matrix(layout):
    production, tuning_root, base_dir = layout
    _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2", input_path=str(base_dir / INPUT_PATH))

    matches = find_compatible_tunings(production, tuning_root, base_dir)

    assert [m.compatible for m in matches] == [True]


def test_tuning_without_the_production_combination_is_rejected_with_the_reason(layout):
    production, tuning_root, base_dir = layout
    _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2", labels={"n_clusters=2,linkage=ward,metric=euclidean": np.zeros(6, dtype=int)})

    (match,) = find_compatible_tunings(production, tuning_root, base_dir)

    assert not match.compatible
    assert KEY in match.reason_rejected


def test_same_combination_but_different_partition_is_rejected(layout):
    # Regression guard for "same input_path, so same run": a directory reused by a later run keeps the key and changes the labels.
    production, tuning_root, base_dir = layout
    _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2", labels={KEY: np.array([0, 1, 0, 1, 0, 1])})

    (match,) = find_compatible_tunings(production, tuning_root, base_dir)

    assert not match.compatible
    assert "ARI" in match.reason_rejected


def test_other_subject_order_is_rejected_even_with_identical_labels(layout):
    production, tuning_root, base_dir = layout
    _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2", subjects=SUBJECTS[::-1])

    (match,) = find_compatible_tunings(production, tuning_root, base_dir)

    assert not match.compatible
    assert "subjects" in match.reason_rejected


def test_tuning_without_clusterings_npz_is_returned_as_rejected_not_dropped(layout):
    production, tuning_root, base_dir = layout
    _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2", write_npz=False)

    (match,) = find_compatible_tunings(production, tuning_root, base_dir)

    assert not match.compatible
    assert "clusterings.npz" in match.reason_rejected


def test_truncated_npz_rejects_that_tuning_and_keeps_the_others(layout):
    production, tuning_root, base_dir = layout
    broken = _write_tuning(tuning_root / "umap" / "01-01_broken")
    (broken / "clusterings.npz").write_bytes(b"PK\x03\x04 truncated")
    good = _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2")

    matches = {m.run_dir: m.compatible for m in find_compatible_tunings(production, tuning_root, base_dir)}

    assert matches == {broken: False, good: True}


def test_unreadable_config_of_one_tuning_is_logged_and_does_not_hide_the_others(layout, caplog):
    production, tuning_root, base_dir = layout
    bad = tuning_root / "umap" / "01-01_bad"
    bad.mkdir(parents=True)
    (bad / "config.md").write_text("# no config block here\n")
    good = _write_tuning(tuning_root / "umap" / "16-10_s2.4-vol_nc2")

    with caplog.at_level(logging.WARNING):
        matches = find_compatible_tunings(production, tuning_root, base_dir)

    assert [m.run_dir for m in matches] == [good]
    assert "01-01_bad" in caplog.text


def test_production_without_metric_raises_instead_of_assuming_euclidean(tmp_path):
    production = _write_production(tmp_path / "production" / "umap" / "old", params={"n_clusters": 4, "linkage": "average"})

    with pytest.raises(ValueError, match="metric"):
        find_compatible_tunings(production, tmp_path / "tuning", tmp_path)


def test_production_of_another_method_raises(tmp_path):
    production = _write_production(tmp_path / "production" / "umap" / "hdb", method="hdbscan")

    with pytest.raises(ValueError, match="hdbscan"):
        find_compatible_tunings(production, tmp_path / "tuning", tmp_path)


@pytest.mark.parametrize("n_clusters", [True, 1, 3.0, "3"])
def test_production_combination_key_rejects_a_non_integer_cluster_count(n_clusters):
    with pytest.raises(ValueError, match="n_clusters"):
        production_combination_key({**PARAMS, "n_clusters": n_clusters})


def test_production_combination_key_matches_the_tuning_key_format():
    assert production_combination_key(PARAMS) == KEY
