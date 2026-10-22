"""Unit tests for src/analysis/cluster_pair.py."""

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from src.analysis.cluster_pair import (
    CentroidSeparation,
    build_odds_ratio_figure,
    centroid_separation,
    difference_image,
    pair_clinical_comparison,
    pair_frame,
    pair_regression,
    regression_term_label,
)
from src.utils import participants as participants_registry

_N_PER_CLUSTER = 100


def _write_registry(root, n_per_cluster=_N_PER_CLUSTER, drop_columns=()):
    """A registry for 3 clusters of `n_per_cluster` subjects: cluster 0 is older, with a bigger
    lesion and more females than cluster 1; cluster 2 is only there to be left out."""
    rng = np.random.default_rng(0)
    rows = []
    for cluster in range(3):
        for i in range(n_per_cluster):
            subject_id = f"sub-STUNIPD{cluster}{i:03d}"
            older = cluster == 0
            rows.append({
                "subject_id": subject_id, "original_id": subject_id,
                "dataset": "UNIPD/WashU" if i % 3 else "UNIPD/PSP",
                "disease_id": "ST", "has_lesion": "True", "has_sdc": "True", "has_features": "False",
                "age": f"{rng.normal(62 if older else 52, 8):.1f}",
                "sex": ("F" if rng.random() < (0.7 if older else 0.3) else "M"),
                "education": "12", "lesion_side": "left" if i % 2 else "right",
                "NIHSS": f"{rng.integers(0, 20)}",
                "lesion_volume_voxels_2mm": f"{int(rng.normal(3200 if older else 2000, 800))}",
                "location_infratentorial_2mm": f"{rng.uniform(0, 0.3):.3f}",
                "location_subcortical_gray_2mm": f"{rng.uniform(0, 0.3):.3f}",
                "location_cortex_only_2mm": f"{rng.uniform(0, 0.3):.3f}",
                "location_cortex_white_boundary_2mm": "0.1", "location_white_matter_only_2mm": "0.1",
                "location_ventricle_2mm": "0.05", "location_unlabeled_2mm": "0.05",
                "location_dominant_2mm": "cortex_only",
            })
    registry = pd.DataFrame(rows).drop(columns=list(drop_columns))
    root.mkdir(exist_ok=True)
    registry.to_csv(root / "participants.csv", index=False)
    return registry


@pytest.fixture
def registry(tmp_path, monkeypatch):
    root = tmp_path / "metadata"
    frame = _write_registry(root)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return frame


def _metadata(registry):
    """The run's metadata.csv: every subject of the registry, labelled by the cluster it was built in."""
    labels = [int(s.removeprefix("sub-STUNIPD")[0]) for s in registry["subject_id"]]
    return pd.DataFrame({"subject_id": registry["subject_id"], "dataset": registry["dataset"], "cluster_label": labels})


# --- pair_frame ------------------------------------------------------------------------------


def test_pair_frame_keeps_only_the_two_clusters_and_reads_the_registry(registry):
    pair = pair_frame(_metadata(registry), 0, 1)

    assert len(pair.frame) == 2 * _N_PER_CLUSTER
    assert set(pair.frame["cluster_label"]) == {0, 1}
    assert pair.unregistered == []
    assert pair.frame["age"].dtype.kind == "f"
    assert pair.frame.loc[pair.frame["cluster_label"] == 0, "age"].mean() > 58


def test_pair_frame_keeps_an_unregistered_subject_as_missing_and_reports_it(registry):
    metadata = pd.concat(
        [_metadata(registry), pd.DataFrame({"subject_id": ["sub-STUNIPD9999"], "dataset": ["UNIPD/PSP"], "cluster_label": [0]})],
        ignore_index=True,
    )

    pair = pair_frame(metadata, 0, 1)

    assert pair.unregistered == ["sub-STUNIPD9999"]
    row = pair.frame[pair.frame["subject_id"] == "sub-STUNIPD9999"].iloc[0]
    assert row["cluster_label"] == 0 and np.isnan(row["age"])
    assert (pair.frame["cluster_label"] == 0).sum() == _N_PER_CLUSTER + 1


@pytest.mark.parametrize(
    "label_1, label_2, message",
    [(0, 0, "same cluster"), (0, 7, "no subjects with cluster_label=7")],
)
def test_pair_frame_rejects_equal_or_empty_clusters(registry, label_1, label_2, message):
    with pytest.raises(ValueError, match=message):
        pair_frame(_metadata(registry), label_1, label_2)


def test_pair_frame_rejects_metadata_without_cluster_labels(registry):
    with pytest.raises(ValueError, match="not a clustering run"):
        pair_frame(_metadata(registry).drop(columns="cluster_label"), 0, 1)


def test_pair_frame_names_a_registry_column_that_is_missing(tmp_path, monkeypatch):
    root = tmp_path / "metadata"
    frame = _write_registry(root, drop_columns=["location_dominant_2mm"])
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)

    with pytest.raises(ValueError, match="location_dominant_2mm"):
        pair_frame(_metadata(frame), 0, 1)


# --- pair_clinical_comparison ----------------------------------------------------------------


def test_clinical_comparison_finds_the_planted_differences_with_the_right_sign(registry):
    comparison = pair_clinical_comparison(pair_frame(_metadata(registry), 0, 1), 0)

    age = comparison.numeric.set_index("variable").loc["Age (years)"]
    assert age["median_1"] > age["median_2"]
    assert age["r"] > 0.3 and age["p_fdr"] < 1e-3
    volume = comparison.numeric.set_index("variable").loc["Lesion volume (voxels)"]
    assert volume["r"] > 0.3 and volume["p_fdr"] < 1e-3
    sex = comparison.categorical.set_index(["variable", "category"]).loc[("Sex", "F")]
    assert sex["share_1"] > sex["share_2"] and sex["odds_ratio"] > 1 and sex["p_fdr"] < 0.01


def test_clinical_comparison_swaps_sign_when_the_clusters_swap(registry):
    pair = pair_frame(_metadata(registry), 0, 1)

    first = pair_clinical_comparison(pair, 0).numeric.set_index("variable")["r"]
    second = pair_clinical_comparison(pair, 1).numeric.set_index("variable")["r"]

    assert np.allclose(first.dropna(), -second.dropna())


def test_clinical_comparison_leaves_the_test_missing_when_a_side_has_one_value(registry):
    pair = pair_frame(_metadata(registry), 0, 1)
    cluster_two = pair.frame.index[pair.frame["cluster_label"] == 1]
    pair.frame.loc[cluster_two, "nihss"] = np.nan
    pair.frame.loc[cluster_two[0], "nihss"] = 4.0

    nihss = pair_clinical_comparison(pair, 0).numeric.set_index("variable").loc["NIHSS"]

    assert nihss["n_2"] == 1
    assert np.isnan(nihss["p"]) and np.isnan(nihss["r"]) and np.isnan(nihss["p_fdr"])


def test_clinical_comparison_rejects_a_label_that_is_not_in_the_pair(registry):
    with pytest.raises(ValueError, match="empty or is the whole frame"):
        pair_clinical_comparison(pair_frame(_metadata(registry), 0, 1), 2)


# --- pair_regression -------------------------------------------------------------------------


def test_regression_gives_odds_above_one_for_what_is_higher_in_cluster_one(registry):
    result = pair_regression(pair_frame(_metadata(registry), 0, 1), 0)

    assert result.n_in_cluster == _N_PER_CLUSTER
    assert result.auc > 0.7
    assert result.coefficients.loc["age", "odds_ratio"] > 1


def test_regression_odds_invert_when_the_clusters_swap(registry):
    pair = pair_frame(_metadata(registry), 0, 1)

    first = pair_regression(pair, 0).coefficients.loc["age", "odds_ratio"]
    second = pair_regression(pair, 1).coefficients.loc["age", "odds_ratio"]

    assert first * second == pytest.approx(1.0, rel=1e-3)


def test_regression_raises_when_a_cluster_is_too_small_for_the_terms(registry):
    metadata = _metadata(registry)
    keep = metadata.groupby("cluster_label").head(_N_PER_CLUSTER).index
    small = metadata.loc[keep].copy()
    cluster_one = small.index[small["cluster_label"] == 1]
    small = small.drop(cluster_one[3:])

    with pytest.raises(ValueError, match="rarer class"):
        pair_regression(pair_frame(small, 0, 1), 0)


def test_regression_term_labels_read_numeric_and_categorical_terms():
    assert regression_term_label("age") == "age"
    assert regression_term_label("sex: M (ref. F)") == "sex: M (ref. F)"
    with pytest.raises(ValueError, match="unknown regression term"):
        regression_term_label("height")


def test_odds_ratio_figure_has_one_point_per_term_on_a_log_axis(registry):
    result = pair_regression(pair_frame(_metadata(registry), 0, 1), 0)

    figure = build_odds_ratio_figure(result, 0, 1)

    assert len(figure.data[0].x) == len(result.coefficients)
    assert figure.layout.xaxis.type == "log"
    assert "more likely in cluster 0" in figure.layout.xaxis.title.text


# --- centroid_separation ---------------------------------------------------------------------


def test_centroid_separation_measures_the_distance_and_each_radius():
    embedding = np.array([[0.0, 0.0], [2.0, 0.0], [10.0, 0.0], [10.0, 4.0], [100.0, 100.0]])
    metadata = pd.DataFrame({"subject_id": list("abcde"), "cluster_label": [0, 0, 1, 1, 2]})

    result = centroid_separation(embedding, metadata, 0, 1)

    assert result == CentroidSeparation(distance=pytest.approx(np.hypot(9.0, 2.0)), radius_1=pytest.approx(1.0), radius_2=pytest.approx(2.0))


def test_centroid_separation_is_symmetric_in_the_distance():
    embedding = np.array([[0.0, 0.0], [2.0, 0.0], [10.0, 0.0], [10.0, 4.0]])
    metadata = pd.DataFrame({"subject_id": list("abcd"), "cluster_label": [0, 0, 1, 1]})

    forward, backward = centroid_separation(embedding, metadata, 0, 1), centroid_separation(embedding, metadata, 1, 0)

    assert forward.distance == pytest.approx(backward.distance)
    assert (forward.radius_1, forward.radius_2) == (backward.radius_2, backward.radius_1)


@pytest.mark.parametrize("labels, message", [((0, 0), "same cluster"), ((0, 5), "no subjects with cluster_label=5")])
def test_centroid_separation_rejects_equal_or_empty_clusters(labels, message):
    metadata = pd.DataFrame({"subject_id": list("ab"), "cluster_label": [0, 1]})

    with pytest.raises(ValueError, match=message):
        centroid_separation(np.zeros((2, 2)), metadata, *labels)


def test_centroid_separation_rejects_a_row_count_mismatch():
    metadata = pd.DataFrame({"subject_id": list("ab"), "cluster_label": [0, 1]})

    with pytest.raises(ValueError, match="3 rows but metadata has 2"):
        centroid_separation(np.zeros((3, 2)), metadata, 0, 1)


# --- difference_image ------------------------------------------------------------------------


def test_difference_image_subtracts_voxel_by_voxel_and_keeps_the_grid():
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    first = nib.Nifti1Image(np.full((2, 2, 2), 30.0, dtype=np.float32), affine)
    second = nib.Nifti1Image(np.full((2, 2, 2), 10.0, dtype=np.float32), affine)

    result = difference_image(first, second)

    assert np.allclose(result.get_fdata(), 20.0)
    assert np.allclose(result.affine, affine)
    assert np.allclose(difference_image(second, first).get_fdata(), -20.0)


def test_difference_image_rejects_two_different_grids():
    first = nib.Nifti1Image(np.zeros((2, 2, 2), dtype=np.float32), np.eye(4))
    other_shape = nib.Nifti1Image(np.zeros((3, 2, 2), dtype=np.float32), np.eye(4))
    other_affine = nib.Nifti1Image(np.zeros((2, 2, 2), dtype=np.float32), np.diag([2.0, 2.0, 2.0, 1.0]))

    with pytest.raises(ValueError, match="not on the same grid"):
        difference_image(first, other_shape)
    with pytest.raises(ValueError, match="not on the same grid"):
        difference_image(first, other_affine)
