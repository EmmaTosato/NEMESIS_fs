"""Integration test: dim_reduction.py chained onto a build_lesion_matrix.py output, on synthetic data."""

import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.pipeline import build_lesion_matrix, dim_reduction
from src.utils.artifacts import save_matrix

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _add_clinical_columns(input_dir, subject_ids):
    """Directly patches an existing build_lesion_matrix.py output's metadata.csv with
    lesion_side/nihss columns - simulating what src.pipeline.enrich_lesion_metadata.py would
    produce against it (that tool's own join/coverage-report contract is tested separately,
    tests/integration/test_enrich_lesion_metadata_pipeline.py). dim_reduction.py no longer
    enriches metadata itself (2026-08-17 - see src/analysis/embedding_coloring.py's own
    module docstring for why) - these tests only need to verify it reads/passes through
    whatever metadata.csv already has, not re-exercise the enrichment tool.
    """
    metadata_path = input_dir / "metadata.csv"
    metadata = pd.read_csv(metadata_path)
    sides = {sid: ("left", "right")[i % 2] for i, sid in enumerate(subject_ids)}
    nihss = {sid: float(4 + i) for i, sid in enumerate(subject_ids)}
    metadata["lesion_side"] = metadata["subject_id"].map(sides)
    metadata["nihss"] = metadata["subject_id"].map(nihss)
    metadata.to_csv(metadata_path, index=False)


def _make_dataset(data_root, n_subjects=8):
    rng = np.random.default_rng(2)
    for i in range(n_subjects):
        subject_id = f"sub-{i:02d}"
        subject_dir = data_root / "siteA" / subject_id / "lesion" / "manual_masks" / "anat"
        subject_dir.mkdir(parents=True, exist_ok=True)
        volume = np.zeros(_SHAPE, dtype=np.float32)
        for voxel in [tuple(rng.integers(0, 10, size=3)) for _ in range(5)]:
            volume[voxel] = 1.0
        nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _build_matrix(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "matrix_out"
    _make_dataset(data_root)
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), template_path)

    build_cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "reference_template_path": str(template_path),
        "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "parcellate": False,
        "atlas_path": None,
        "parcel_aggregation": None,
        "save_parcellated_volumes": False,
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    build_cfg_path = tmp_path / "build.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0

    return next(p for p in output_root.iterdir() if p.is_dir())


def _write_params(tmp_path):
    params_path = tmp_path / "params_reduction.json"
    params_path.write_text(
        json.dumps(
            {
                "pca": {
                    "params": {"n_components": 2},
                    "tuning_grid": {"n_components": [1, 2, 3]},
                },
                "umap": {
                    "params": {"n_neighbors": 3, "min_dist": 0.1, "n_components": 2, "random_state": 0},
                    "tuning_grid": {"n_neighbors": [2, 3], "min_dist": [0.1, 0.5]},
                    "trustworthiness_n_neighbors": 2,
                },
                "pca_varimax": {
                    "params": {"n_components": 2, "rotation_max_iter": 500},
                    "tuning_grid": {"n_components": [2, 3, 4]},
                },
                "pacmap": {
                    "params": {"n_components": 2, "n_neighbors": 3, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0},
                    "tuning_grid": {"n_neighbors": [2, 3]},
                    "trustworthiness_n_neighbors": 2,
                },
                "tsne": {
                    "params": {"n_components": 2, "perplexity": 3, "random_state": 0},
                    "tuning_grid": {"perplexity": [2, 3]},
                    "trustworthiness_n_neighbors": 2,
                },
            }
        )
    )
    return params_path


def test_dim_reduction_end_to_end_chained(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")
    _add_clinical_columns(input_dir, [f"sub-{i:02d}" for i in range(8)])

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "color_by": ["dataset", "volume", "side"],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    out_dir = next(p for p in (output_root / "production" / "pca").iterdir() if p.is_dir())
    embedding = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert embedding.shape == (8, 2)
    assert list(metadata.columns) == ["subject_id", "dataset", "lesion_volume_voxels", "lesion_side", "nihss"]
    assert len(metadata) == 8
    assert set(metadata["lesion_side"]) == {"left", "right"}
    assert metadata["nihss"].tolist() == [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
    assert (metadata["lesion_volume_voxels"] > 0).all()

    for suffix in ("_unico", "_dataset", "_volume", "_side"):
        assert (out_dir / f"embedding_plot{suffix}.png").is_file()

    runs_csv = (output_root / "production" / "pca" / "runs.csv").read_text()
    assert "run1" in runs_csv
    assert not (output_root / "tuning" / "pca" / "runs_tuning.csv").exists()  # production/tuning are separate files, not a column


def test_dim_reduction_fine_tuning_umap_writes_sweep_not_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": "prova sweep",
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "umap").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert not (tuning_dir / "tuning_plot.png").exists()  # 2 swept params - heatmaps removed on request, CSV only
    assert not (tuning_dir / "matrix.npy").exists()  # a sweep is not a matrix artifact
    assert not (tuning_dir / "embeddings.npz").exists()  # save_tuning_embeddings=False (default) writes nothing
    assert not (tuning_dir / "metadata.csv").exists()  # same flag also gates metadata.csv - no enrichment either

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results.columns) == ["n_neighbors", "min_dist", "trustworthiness"]
    assert len(results) == 4  # 2 x 2 grid

    # config.md must be a self-contained snapshot of what was actually swept -
    # not just the pipeline-level config, which alone can't tell you the grid.
    config_md = (tuning_dir / "config.md").read_text()
    assert '"base_params"' in config_md
    assert '"tuning_grid"' in config_md
    assert '"n_neighbors": [' in config_md
    assert '"min_dist": [' in config_md

    runs_csv = (output_root / "tuning" / "umap" / "runs_tuning.csv").read_text()
    assert "tune1" in runs_csv
    assert "prova sweep" in runs_csv
    assert not (output_root / "production" / "umap" / "runs.csv").exists()  # tuning writes runs_tuning.csv, not runs.csv


def test_dim_reduction_fine_tuning_save_tuning_embeddings_writes_npz(tmp_path, monkeypatch):
    """save_tuning_embeddings=True (opt-in, 2026-08 field) persists every
    combination's actual embedding into embeddings.npz, keyed by a
    self-describing 'k1=v1,k2=v2,...' string built from tuning_grid's own key
    order - the same names/values each tuning_results.csv row already carries,
    so a caller rebuilds the exact key from any row without a separate index
    file (docs/dev/models.md). Also writes a metadata.csv - whatever input_path's
    own metadata.csv already had (2026-08-17: no enrichment of its own anymore,
    see _add_clinical_columns) - so a later reader never needs X again to
    color/label a saved embedding, provided input_path was itself already
    enriched (lesion_side/nihss here) before this run.
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")
    _add_clinical_columns(input_dir, [f"sub-{i:02d}" for i in range(8)])

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_emb",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": True,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning_emb.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    assert dim_reduction.main(["--config", str(dr_cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "umap").iterdir() if p.is_dir())
    npz_path = tuning_dir / "embeddings.npz"
    assert npz_path.is_file()

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 4  # 2 x 2 grid (n_neighbors x min_dist), same sweep as the test above
    expected_keys = {f"n_neighbors={row.n_neighbors},min_dist={row.min_dist}" for row in results.itertuples()}

    data = np.load(npz_path)
    assert set(data.files) == expected_keys
    for key in expected_keys:
        assert data[key].shape == (8, 2)  # 8 subjects (fixture size), n_components=2 (umap's base params)

    metadata_path = tuning_dir / "metadata.csv"
    assert metadata_path.is_file()
    metadata = pd.read_csv(metadata_path)
    assert list(metadata.columns) == ["subject_id", "dataset", "lesion_volume_voxels", "lesion_side", "nihss"]
    assert len(metadata) == 8
    assert set(metadata["lesion_side"]) == {"left", "right"}
    assert metadata["nihss"].tolist() == [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]
    assert (metadata["lesion_volume_voxels"] > 0).all()


def test_dim_reduction_fine_tuning_pca_varimax_writes_sweep_not_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca_varimax",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "pca_varimax").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert not (tuning_dir / "matrix.npy").exists()

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results.columns) == ["n_components", "cumulative_explained_variance"]
    assert len(results) == 3  # 3-value grid


def test_dim_reduction_fine_tuning_pacmap_writes_sweep_not_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pacmap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "pacmap").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert not (tuning_dir / "matrix.npy").exists()

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results.columns) == ["n_neighbors", "trustworthiness"]
    assert len(results) == 2  # 2-value grid


def test_dim_reduction_fine_tuning_tsne_writes_sweep_not_embedding(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "tsne",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "tsne").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert not (tuning_dir / "matrix.npy").exists()  # a sweep is not a matrix artifact

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results.columns) == ["perplexity", "trustworthiness"]
    assert len(results) == 2  # 2-value grid


def _make_varying_volume_dataset(data_root, n_subjects=8):
    """Unlike _make_dataset (fixed 5-voxel draws, which can coincidentally
    tie every subject's lesion volume at the same count), each subject here
    gets a strictly increasing, non-overlapping voxel count - guarantees the
    lesion-volume covariate actually varies (used by tests that check
    build_lesion_matrix.py's own lesion_volume_voxels downstream).
    """
    rng = np.random.default_rng(42)
    for i in range(n_subjects):
        subject_id = f"sub-{i:02d}"
        subject_dir = data_root / "siteA" / subject_id / "lesion" / "manual_masks" / "anat"
        subject_dir.mkdir(parents=True, exist_ok=True)
        n_voxels = 3 + i
        flat = np.zeros(np.prod(_SHAPE), dtype=np.float32)
        flat[rng.choice(flat.shape[0], size=n_voxels, replace=False)] = 1.0
        nib.save(nib.Nifti1Image(flat.reshape(_SHAPE), _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")


def _build_matrix_varying_volume(tmp_path, monkeypatch):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    output_root = tmp_path / "matrix_out"
    _make_varying_volume_dataset(data_root)
    template_path = tmp_path / "reference_template.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros(_SHAPE, dtype=np.float32), _AFFINE), template_path)

    build_cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "reference_template_path": str(template_path),
        "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "parcellate": False,
        "atlas_path": None,
        "parcel_aggregation": None,
        "save_parcellated_volumes": False,
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    build_cfg_path = tmp_path / "build_varying.json"
    build_cfg_path.write_text(json.dumps(build_cfg))
    assert build_lesion_matrix.main(["--config", str(build_cfg_path)]) == 0

    return next(p for p in output_root.iterdir() if p.is_dir())


def test_dim_reduction_jaccard_metric_on_non_binary_matrix_raises(tmp_path, monkeypatch):
    """Regression test for the binarity-validation gap (2026-08,
    literature-validation review): jaccard/dice are only defined on strictly
    binary data - a parcellated 'fraction_lesioned' matrix (continuous in
    [0, 1], as build_lesion_matrix.py produces when parcellate=True) fed to
    metric="jaccard" used to silently compute numbers that look like valid
    distances but aren't Jaccard/Dice at all. Production must now reject this
    upfront, before any output directory is created. Built directly via
    save_matrix (not build_lesion_matrix.py, which would need a real atlas
    fixture to actually parcellate) - only the continuous-valued matrix.npy
    matters for this test, not how it was produced.
    """
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    input_dir = tmp_path / "continuous_matrix"
    rng = np.random.default_rng(0)
    X_continuous = rng.random((8, 5))  # e.g. fraction_lesioned per parcel - never exactly 0/1
    metadata = pd.DataFrame({"subject_id": [f"sub-{i:02d}" for i in range(8)], "dataset": "siteA"})
    save_matrix(input_dir, X_continuous, metadata, ["# continuous fixture"], overwrite=False)

    params_path = tmp_path / "params_reduction.json"
    params_path.write_text(
        json.dumps(
            {
                "umap": {
                    "params": {
                        "n_neighbors": 3,
                        "min_dist": 0.1,
                        "n_components": 2,
                        "random_state": 0,
                        "metric": "jaccard",
                    }
                }
            }
        )
    )
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(tmp_path / "dr_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    assert dim_reduction.main(["--config", str(dr_cfg_path)]) == 1
    assert not (tmp_path / "dr_out").exists()


def test_dim_reduction_missing_input_path_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = _write_params(tmp_path)
    dr_cfg = {
        "project": "testproj",
        "input_path": str(tmp_path / "does_not_exist"),
        "reduction_method": "pca",
        "params_file": str(params_path),
        "output_root": str(tmp_path / "dr_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    assert dim_reduction.main(["--config", str(dr_cfg_path)]) == 1


def test_dim_reduction_fine_tuning_nested_params_writes_leaf_folders_and_embeddings_grid(tmp_path, monkeypatch):
    """Real end-to-end test of the nested_params mechanism (2026-08 session):
    metric fixed one-at-a-time (own subfolder per value), n_neighbors/min_dist
    swept jointly as the real grid, each leaf getting its own filtered
    tuning_results.csv plus an embeddings_grid_unico.png of real embeddings.
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = tmp_path / "params_nested.json"
    params_path.write_text(
        json.dumps(
            {
                "umap": {
                    "params": {"n_neighbors": 3, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "euclidean"},
                    "tuning_grid": {
                        "metric": ["euclidean", "cosine"],
                        "n_neighbors": [2, 3],
                        "min_dist": [0.1, 0.5],
                    },
                    "nested_params": ["metric"],
                    "trustworthiness_n_neighbors": 2,
                }
            }
        )
    )
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_nested",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning_nested.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "umap").iterdir() if p.is_dir())
    top_results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(top_results) == 8  # 2 metric x 2 n_neighbors x 2 min_dist

    for metric in ("euclidean", "cosine"):
        leaf_dir = tuning_dir / f"metric={metric}"
        assert leaf_dir.is_dir()
        leaf_results = pd.read_csv(leaf_dir / "tuning_results.csv")
        assert len(leaf_results) == 4  # 2 n_neighbors x 2 min_dist, this metric only
        assert set(leaf_results["metric"]) == {metric}
        assert (leaf_dir / "embeddings_grid_unico.png").is_file()

    config_md = (tuning_dir / "config.md").read_text()
    assert '"nested_params": [' in config_md


def test_dim_reduction_fine_tuning_overwrite_wipes_leaves_from_incompatible_prior_grid(tmp_path, monkeypatch):
    """Regression: re-running fine_tuning into the same output_dir with
    overwrite=True but a DIFFERENT nested_params (fewer nesting levels) used
    to leave the prior run's now-orphaned leaf folders on disk, never
    described by the freshly-written config.md (lessons_learned.md #18 -
    already happened once in production, fixed by hand that time)."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = tmp_path / "params_nested.json"

    def _write_params(nested_params):
        params_path.write_text(
            json.dumps(
                {
                    "umap": {
                        "params": {
                            "n_neighbors": 3,
                            "min_dist": 0.1,
                            "n_components": 2,
                            "random_state": 0,
                            "metric": "euclidean",
                        },
                        "tuning_grid": {
                            "metric": ["euclidean", "cosine"],
                            "n_neighbors": [2, 3],
                            "min_dist": [0.1],
                        },
                        "nested_params": nested_params,
                        "trustworthiness_n_neighbors": 2,
                    }
                }
            )
        )

    output_root = tmp_path / "dr_out"

    def _cfg(overwrite):
        return {
            "project": "testproj",
            "input_path": str(input_dir),
            "reduction_method": "umap",
            "params_file": str(params_path),
            "output_root": str(output_root),
            "session_name": "tune_reuse",
            "overwrite": overwrite,
            "fine_tuning": True,
            "color_by": [],
            "viz_n_components": 2,
            "write_embeddings_grid": True,
            "save_tuning_embeddings": False,
            "run_notes": None,
        }

    # Run 1: nested on both metric and n_neighbors -> 2-level leaf folders.
    _write_params(["metric", "n_neighbors"])
    cfg_path = tmp_path / "cfg1.json"
    cfg_path.write_text(json.dumps(_cfg(overwrite=False)))
    assert dim_reduction.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "umap").iterdir() if p.is_dir())
    stale_leaf = tuning_dir / "metric=euclidean" / "n_neighbors=2"
    assert stale_leaf.is_dir()

    # Run 2: same output_dir (same session_name, same day), overwrite=True,
    # but nested only on metric - n_neighbors becomes a free/grid param again.
    _write_params(["metric"])
    cfg_path2 = tmp_path / "cfg2.json"
    cfg_path2.write_text(json.dumps(_cfg(overwrite=True)))
    assert dim_reduction.main(["--config", str(cfg_path2)]) == 0

    assert not stale_leaf.exists(), "leaf folder from the prior, incompatible nested_params must not survive overwrite=True"
    assert (tuning_dir / "metric=euclidean" / "tuning_results.csv").is_file()


def test_dim_reduction_fine_tuning_write_embeddings_grid_false_skips_plots_keeps_csv(tmp_path, monkeypatch):
    """write_embeddings_grid=False is a manual opt-out (2026-08 session): each
    leaf's tuning_results.csv is still written (cheap, always useful), but
    _build_grid_blocks/write_embedding_grid - and every umap refit that
    mechanism would trigger - is skipped entirely. Useful when a sweep's
    tuning_grid varies n_components: the refit for any leaf whose own
    n_components != 2 is otherwise guaranteed redundant with whichever other
    leaf already covers n_components=2 at the same free-parameter values
    (same metric/n_neighbors/min_dist/random_state, umap is deterministic).
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = tmp_path / "params_nested_no_grid.json"
    params_path.write_text(
        json.dumps(
            {
                "umap": {
                    "params": {"n_neighbors": 3, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "euclidean"},
                    "tuning_grid": {
                        "metric": ["euclidean", "cosine"],
                        "n_neighbors": [2, 3],
                        "min_dist": [0.1, 0.5],
                    },
                    "nested_params": ["metric"],
                    "trustworthiness_n_neighbors": 2,
                }
            }
        )
    )
    output_root = tmp_path / "dr_out"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_nested_no_grid",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": False,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning_nested_no_grid.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "umap").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    for metric in ("euclidean", "cosine"):
        leaf_dir = tuning_dir / f"metric={metric}"
        assert (leaf_dir / "tuning_results.csv").is_file()
        assert not (leaf_dir / "embeddings_grid_unico.png").exists()
    assert not any(tuning_dir.rglob("embeddings_grid_*.png"))


def test_dim_reduction_fine_tuning_nested_n_components_refits_viz(tmp_path, monkeypatch):
    """Regression coverage for embedding_for_viz's refit branch: a
    nested_params sweep that varies n_components forces
    _build_grid_blocks/embedding_for_viz to actually refit (a leaf's own
    n_components=3 != the grid's fixed viz n_components=2), not take the
    "already the right shape, reuse as-is" early-return path - a branch that
    stays untested by construction as long as every leaf's n_components
    happens to already equal 2 (lessons_learned.md #17: the first real input
    that finally makes the early-return condition false is the first real
    test that branch has ever had).
    """
    input_dir = _build_matrix_varying_volume(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction, "LOGS_ROOT", tmp_path / "dr_logs")

    params_path = tmp_path / "params_nested_ncomp.json"
    params_path.write_text(
        json.dumps(
            {
                "umap": {
                    "params": {"n_neighbors": 3, "min_dist": 0.1, "n_components": 2, "random_state": 0, "metric": "euclidean"},
                    "tuning_grid": {
                        "n_components": [2, 3],
                        "n_neighbors": [2, 3],
                    },
                    "nested_params": ["n_components"],
                    "trustworthiness_n_neighbors": 2,
                }
            }
        )
    )
    output_root = tmp_path / "dr_out_ncomp"
    dr_cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "params_file": str(params_path),
        "output_root": str(output_root),
        "session_name": "tune_nested_ncomp",
        "overwrite": False,
        "fine_tuning": True,
        "color_by": [],
        "viz_n_components": 2,
        "write_embeddings_grid": True,
        "save_tuning_embeddings": False,
        "run_notes": None,
    }
    dr_cfg_path = tmp_path / "dim_reduction_tuning_nested_ncomp.json"
    dr_cfg_path.write_text(json.dumps(dr_cfg))

    exit_code = dim_reduction.main(["--config", str(dr_cfg_path)])
    assert exit_code == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "umap").iterdir() if p.is_dir())
    # n_components=3 forces a refit (2 != the grid's fixed viz n_components).
    leaf_dir = tuning_dir / "n_components=3"
    assert leaf_dir.is_dir()
    assert (leaf_dir / "embeddings_grid_unico.png").is_file()
