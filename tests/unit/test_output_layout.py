"""Unit tests for src.retrieval.output_layout - the local retrieval layout's
single source of truth (dataset root + pipeline-first per-file path)."""

from pathlib import Path

import pytest

from src.retrieval.config import RetrievalConfig, RetrieveItem
from src.retrieval.output_layout import local_dataset_root, local_relative_path


def _make_config(tmp_path, **overrides):
    defaults = dict(
        output_root=tmp_path / "data",
        project="clinical_connectome",
        file_patterns_path=tmp_path / "file_patterns.json",
        file_patterns=None,
        datasets=["UNIPD/WashU"],
        group_filter=None,
        subjects=None,
        retrieve=[RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")],
        include_tabular_data=False,
        overwrite=False,
    )
    defaults.update(overrides)
    return RetrievalConfig(**defaults)


def test_local_dataset_root_nests_under_a_single_derivatives_level(tmp_path):
    config = _make_config(tmp_path)
    assert local_dataset_root(config, "UNIPD/WashU") == tmp_path / "data" / "clinical_connectome" / "derivatives" / "UNIPD" / "WashU"


def test_local_relative_path_lesion_uses_real_pipeline_name_first():
    item = RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")
    assert local_relative_path(item, "sub-STUNIPD0001", "sub-STUNIPD0001_label-lesion_mask.nii.gz") == Path(
        "manual_masks", "sub-STUNIPD0001", "anat", "sub-STUNIPD0001_label-lesion_mask.nii.gz"
    )


def test_local_relative_path_feature_uses_stand_in_pipeline_label():
    """`feature` has no real pipeline name at the source (see
    docs/dev/retrieval.md) - the local layout uses a registered stand-in
    ("features") so the path is still pipeline-first, not a claim about the
    real source pipeline."""
    item = RetrieveItem(object="feature", pipeline=None, datatype="func", suffix="FC-pearson")
    assert local_relative_path(item, "sub-STUNIPD0131", "sub-STUNIPD0131_FC-pearson_atlas-X.csv") == Path(
        "features", "sub-STUNIPD0131", "func", "sub-STUNIPD0131_FC-pearson_atlas-X.csv"
    )


def test_local_relative_path_sdc_uses_its_own_stand_in_pipeline_label():
    """`sdc` also has no real pipeline name at the source - it's the same
    Stage1+Stage2 BCBToolKit output src/sdc/runner.py itself produces, just
    not run through our own `compute_sdc.py` orchestration for this
    particular run (no `manifest.csv`/`_status/` written by us for it)."""
    item = RetrieveItem(object="sdc", pipeline=None, datatype="dwi", suffix="disconnectome-map")
    assert local_relative_path(item, "sub-STUNIPD0001", "sub-STUNIPD0001_desc-disconnectome.nii.gz") == Path(
        "sdc", "sub-STUNIPD0001", "sub-STUNIPD0001_desc-disconnectome.nii.gz"
    )


def test_local_relative_path_sdc_skips_the_datatype_folder():
    """`sdc`'s `datatype` ("dwi") isn't a real folder at the source (unlike
    lesion's `anat`/feature's `func`) - the local layout must not fabricate
    one either (_OBJECTS_WITHOUT_DATATYPE_FOLDER)."""
    item = RetrieveItem(object="sdc", pipeline=None, datatype="dwi", suffix="lesion-map")
    path = local_relative_path(item, "sub-STUKE0001", "sub-STUKE0001_desc-lesion.nii.gz")
    assert "dwi" not in path.parts
    assert path == Path("sdc", "sub-STUKE0001", "sub-STUKE0001_desc-lesion.nii.gz")


def test_pipeline_first_ordering_puts_pipeline_before_subject_id():
    """Regression for the switch from subject-first to pipeline-first: the
    pipeline/stand-in label must be the first path segment, subject_id the
    second - not the reverse."""
    item = RetrieveItem(object="lesion", pipeline="manual_masks", datatype="anat", suffix="lesion_mask")
    parts = local_relative_path(item, "sub-A", "file.nii.gz").parts
    assert parts[0] == "manual_masks"
    assert parts[1] == "sub-A"
