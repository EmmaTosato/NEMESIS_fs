"""Unit tests for src/analysis/embedding_coloring.py."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.embedding_coloring import COLOR_MODES, resolve_color_mode
from src.features import clinical


def _metadata():
    return pd.DataFrame({"subject_id": ["sub-1", "sub-2", "sub-3"], "dataset": ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR"]})


def test_registry_has_expected_modes():
    assert set(COLOR_MODES) == {"dataset", "side", "volume", "nihss"}


def test_dataset_mode_is_categorical_and_reads_metadata_column():
    mode = resolve_color_mode("dataset")
    assert mode.kind == "categorical"
    values = mode.compute(_metadata(), np.zeros((3, 5)))
    assert list(values) == ["UNIPD/WashU", "UNIPD/WashU", "UKLFR/stroke_UKLFR"]


def test_volume_mode_is_continuous_and_sums_X_rows():
    mode = resolve_color_mode("volume")
    assert mode.kind == "continuous"
    X = np.array([[1, 1, 0], [1, 0, 0], [1, 1, 1]])
    values = mode.compute(_metadata(), X)
    assert list(values) == [2, 1, 3]


def test_volume_mode_uses_log_scale():
    assert resolve_color_mode("volume").log_scale is True


def test_nihss_mode_uses_linear_scale():
    assert resolve_color_mode("nihss").log_scale is False


def test_categorical_modes_default_log_scale_false():
    assert resolve_color_mode("dataset").log_scale is False
    assert resolve_color_mode("side").log_scale is False


def test_side_mode_is_categorical_and_reads_participants_tsv(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    path = tmp_path / "UNIPD_WashU_participants_lesions.tsv"
    pd.DataFrame([{"participant_id": "sub-1", "lesion_side": "left"}, {"participant_id": "sub-2", "lesion_side": "right"}]).to_csv(
        path, sep="\t", index=False
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    mode = resolve_color_mode("side")
    assert mode.kind == "categorical"
    values = mode.compute(metadata, np.zeros((2, 3)))
    assert list(values) == ["left", "right"]


def test_nihss_mode_is_continuous_and_reads_participants_tsv(tmp_path, monkeypatch):
    monkeypatch.setattr(clinical, "METADATA_ROOT", tmp_path)
    path = tmp_path / "UNIPD_WashU_participants_lesions.tsv"
    pd.DataFrame([{"participant_id": "sub-1", "NIHSS": "4"}, {"participant_id": "sub-2", "NIHSS": "n/a"}]).to_csv(
        path, sep="\t", index=False
    )
    metadata = pd.DataFrame({"subject_id": ["sub-1", "sub-2"], "dataset": ["UNIPD/WashU", "UNIPD/WashU"]})

    mode = resolve_color_mode("nihss")
    assert mode.kind == "continuous"
    values = mode.compute(metadata, np.zeros((2, 3)))
    assert values[0] == 4.0
    assert np.isnan(values[1])


def test_resolve_color_mode_unknown_raises():
    with pytest.raises(ValueError, match="unknown color_by mode 'bogus' - known:"):
        resolve_color_mode("bogus")
