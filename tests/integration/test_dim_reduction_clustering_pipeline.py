"""Integration test: dim_reduction_clustering.py chained onto a build_lesion_matrix.py output."""

import csv
import json

import nibabel as nib
import numpy as np
import pandas as pd

from src.features import clinical
from src.pipeline import build_lesion_matrix, dim_reduction_clustering
from src.utils.artifacts import save_matrix

_AFFINE = np.eye(4) * 2
_AFFINE[3, 3] = 1
_SHAPE = (10, 10, 10)


def _write_participants_registry(tmp_path, monkeypatch, n_subjects, dataset="siteA"):
    """Fixture participants.tsv under a monkeypatched METADATA_ROOT, so
    dim_reduction_clustering.py's production-mode enrich_metadata_with_lesion_info
    (src/features/clinical.py) can resolve lesion_side/nihss for the
    synthetic "siteA" dataset these tests build - same fixture shape as
    test_dim_reduction_pipeline.py's own registry helper.
    """
    metadata_root = tmp_path / "metadata_registry"
    metadata_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(clinical, "METADATA_ROOT", metadata_root)
    rows = [
        {"participant_id": f"sub-{i:02d}", "lesion_side": ("left", "right")[i % 2], "NIHSS": str(4 + i)}
        for i in range(n_subjects)
    ]
    pd.DataFrame(rows).to_csv(metadata_root / f"{dataset}_participants_lesions.tsv", sep="\t", index=False)


def _build_matrix(tmp_path, monkeypatch, n_subjects=12):
    monkeypatch.setattr(build_lesion_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "logs")

    data_root = tmp_path / "data"
    rng = np.random.default_rng(3)
    for i in range(n_subjects):
        subject_id = f"sub-{i:02d}"
        subject_dir = data_root / "siteA" / subject_id / "lesion" / "manual_masks" / "anat"
        subject_dir.mkdir(parents=True, exist_ok=True)
        volume = np.zeros(_SHAPE, dtype=np.float32)
        for voxel in [tuple(rng.integers(0, 10, size=3)) for _ in range(5)]:
            volume[voxel] = 1.0
        nib.save(nib.Nifti1Image(volume, _AFFINE), subject_dir / f"{subject_id}_label-lesion_mask.nii.gz")

    output_root = tmp_path / "matrix_out"
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


def test_dim_reduction_clustering_end_to_end(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    _write_participants_registry(tmp_path, monkeypatch, n_subjects=12)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": "prova pca+kmeans",
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    exit_code = dim_reduction_clustering.main(["--config", str(cfg_path)])
    assert exit_code == 0

    out_dir = next(p for p in (output_root / "production" / "pca" / "kmeans").iterdir() if p.is_dir())
    embedding = np.load(out_dir / "matrix.npy")
    metadata = pd.read_csv(out_dir / "metadata.csv")
    assert embedding.shape == (12, 2)
    assert list(metadata.columns) == [
        "subject_id", "dataset", "lesion_volume_voxels", "lesion_side", "nihss", "cluster_label",
    ]
    assert set(metadata["cluster_label"].unique()) <= {0, 1, 2}
    assert (out_dir / "cluster_plot.png").stat().st_size > 0

    interactive_html = (out_dir / "cluster_plot_interactive.html").read_text()
    assert "plotly" in interactive_html
    assert "Color by" not in interactive_html  # cluster-only coloring, no dataset toggle

    with (output_root / "production" / "pca" / "runs.csv").open(newline="") as f:
        runs_rows = list(csv.DictReader(f))
    assert len(runs_rows) == 1
    assert runs_rows[0]["reduction_method"] == "pca"
    assert runs_rows[0]["clustering_method"] == "kmeans"
    assert runs_rows[0]["session"] == "run1"
    assert runs_rows[0]["notes"] == "prova pca+kmeans"


def test_dim_reduction_clustering_end_to_end_multiple_methods_writes_comparison_plot(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    _write_participants_registry(tmp_path, monkeypatch, n_subjects=12)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}},
                "agglomerative": {"params": {"n_clusters": 3, "linkage": "ward"}},
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans", "agglomerative"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    for method in ("kmeans", "agglomerative"):
        out_dir = next(p for p in (output_root / "production" / "pca" / method).iterdir() if p.is_dir())
        embedding = np.load(out_dir / "matrix.npy")
        assert embedding.shape == (12, 2)
        assert (out_dir / "cluster_plot.png").stat().st_size > 0

    # both methods share one runs.csv under the reduction folder, distinguished by clustering_method
    with (output_root / "production" / "pca" / "runs.csv").open(newline="") as f:
        runs_rows = list(csv.DictReader(f))
    assert [row["clustering_method"] for row in runs_rows] == ["kmeans", "agglomerative"]
    assert all(row["reduction_method"] == "pca" for row in runs_rows)

    comparison_dir = next(p for p in (output_root / "production" / "pca" / "comparison").iterdir() if p.is_dir())
    assert comparison_dir.name.startswith("pca_")
    assert (comparison_dir / "cluster_comparison.png").stat().st_size > 0
    assert (comparison_dir / "cluster_comparison_interactive.html").stat().st_size > 0
    comparison_html = (comparison_dir / "cluster_comparison_interactive.html").read_text()
    assert "plotly" in comparison_html
    assert "updatemenus" in comparison_html
    comparison_readme = (comparison_dir / "config.md").read_text()
    assert "kmeans" in comparison_readme
    assert "agglomerative" in comparison_readme
    assert "pca" in comparison_readme


def test_dim_reduction_clustering_fine_tuning_kmeans_sweeps_against_one_embedding(tmp_path, monkeypatch):
    """fine_tuning=true: the reduction runs once (fixed params, never swept),
    then kmeans' own tuning_grid is swept against that one embedding.
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3, 4]},
                }
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": "prova sweep n_clusters su embedding pca",
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "pca" / "kmeans").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_results.csv").is_file()
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0
    assert not (tuning_dir / "matrix.npy").exists()  # a sweep is not a matrix artifact

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert list(results["n_clusters"]) == [2, 3, 4]
    assert "inertia" in results.columns
    assert "silhouette" in results.columns

    # config.md must be a self-contained snapshot of what was actually swept -
    # not just the pipeline-level config, which alone can't tell you the grid.
    config_md = (tuning_dir / "config.md").read_text()
    assert '"clustering_base_params"' in config_md
    assert '"clustering_tuning_grid"' in config_md
    assert '"n_clusters": [' in config_md
    assert "Warning: no automatic selection" in config_md

    # no comparison plot in tuning mode - only one method's sweep, and a sweep
    # isn't a single set of cluster labels to compare side by side anyway
    assert not (output_root / "production" / "pca" / "comparison").exists()

    assert not (output_root / "production" / "pca" / "runs.csv").exists()  # tuning writes runs_tuning.csv, not runs.csv
    with (output_root / "tuning" / "pca" / "runs_tuning.csv").open(newline="") as f:
        runs_rows = list(csv.DictReader(f))
    assert runs_rows[0]["reduction_method"] == "pca"
    assert runs_rows[0]["clustering_method"] == "kmeans"
    assert runs_rows[0]["notes"] == "prova sweep n_clusters su embedding pca"


def test_dim_reduction_clustering_fine_tuning_two_swept_params_writes_heatmap(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "agglomerative": {
                    "params": {"n_clusters": 2, "linkage": "ward"},
                    "tuning_grid": {"n_clusters": [2, 3], "linkage": ["ward", "average"]},
                }
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["agglomerative"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "pca" / "agglomerative").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0  # heatmap, not the 1-param line plot

    results = pd.read_csv(tuning_dir / "tuning_results.csv")
    assert len(results) == 4  # 2 x 2 cartesian product
    assert set(results["linkage"]) == {"ward", "average"}


def test_dim_reduction_clustering_fine_tuning_overwrite_wipes_stale_plot_from_incompatible_prior_grid(
    tmp_path, monkeypatch
):
    """Regression: same gap as clustering.py's twin - re-running fine_tuning
    into the same output_dir with overwrite=True but a differently-shaped
    tuning_grid (3+ swept params, no plot supported) used to leave the prior
    run's tuning_plot.png stale on disk (lessons_learned.md #18)."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    output_root = tmp_path / "drc_out"

    def _cfg(overwrite):
        return {
            "project": "testproj",
            "input_path": str(input_dir),
            "reduction_method": "pca",
            "reduction_params_file": str(reduction_params_path),
            "clustering_methods": ["kmeans"],
            "clustering_params_file": str(clustering_params_path),
            "output_root": str(output_root),
            "session_name": "tune_reuse",
            "overwrite": overwrite,
            "fine_tuning": True,
            "viz_n_components": 2,
            "color_by": [],
            "run_notes": None,
        }

    # Run 1: 1 swept param -> writes a real tuning_plot.png (line plot).
    clustering_params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                }
            }
        )
    )
    cfg_path = tmp_path / "drc1.json"
    cfg_path.write_text(json.dumps(_cfg(overwrite=False)))
    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "pca" / "kmeans").iterdir() if p.is_dir())
    assert (tuning_dir / "tuning_plot.png").stat().st_size > 0

    # Run 2: same output_dir, overwrite=True, but 3 swept params - no plot
    # supported (only 1 or 2), see _write_tuning_output's own warning branch.
    clustering_params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3], "random_state": [0, 1], "n_init": [1, 2]},
                }
            }
        )
    )
    cfg_path2 = tmp_path / "drc2.json"
    cfg_path2.write_text(json.dumps(_cfg(overwrite=True)))
    assert dim_reduction_clustering.main(["--config", str(cfg_path2)]) == 0

    assert not (tuning_dir / "tuning_plot.png").exists(), (
        "stale plot from the prior, incompatible grid must not survive overwrite=True"
    )
    assert (tuning_dir / "tuning_results.csv").is_file()


def test_dim_reduction_clustering_fine_tuning_agglomerative_writes_dendrogram(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "agglomerative": {
                    "params": {"n_clusters": 3, "linkage": "ward"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                }
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["agglomerative"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    tuning_dir = next(p for p in (output_root / "tuning" / "pca" / "agglomerative").iterdir() if p.is_dir())
    assert (tuning_dir / "dendrogram.png").stat().st_size > 0  # standalone diagnostic, agglomerative-only


def test_dim_reduction_clustering_dice_metric_on_non_binary_matrix_raises(tmp_path, monkeypatch):
    """Regression test for the binarity-validation gap (2026-08,
    literature-validation review): metric="dice" requires a strictly binary
    matrix - dim_reduction_clustering.py's main() must reject a continuous
    (e.g. parcellated fraction_lesioned) matrix upfront, before computing
    anything, same as dim_reduction.py's own production path.
    """
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    input_dir = tmp_path / "continuous_matrix"
    rng = np.random.default_rng(0)
    X_continuous = rng.random((12, 5))
    metadata = pd.DataFrame({"subject_id": [f"sub-{i:02d}" for i in range(12)], "dataset": "siteA"})
    save_matrix(input_dir, X_continuous, metadata, ["# continuous fixture"], overwrite=False)

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(
        json.dumps(
            {
                "umap": {
                    "params": {
                        "n_neighbors": 3,
                        "min_dist": 0.1,
                        "n_components": 2,
                        "random_state": 0,
                        "metric": "dice",
                    }
                }
            }
        )
    )
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(tmp_path / "drc_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 1
    assert not (tmp_path / "drc_out").exists()


def test_dim_reduction_clustering_fine_tuning_missing_tuning_grid_raises(tmp_path, monkeypatch):
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    # kmeans has no "tuning_grid" entry on purpose
    clustering_params_path.write_text(
        json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}})
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 1


def test_dim_reduction_clustering_fine_tuning_sweep_value_error_is_caught_not_propagated(tmp_path, monkeypatch):
    """Regression: same gap as clustering.py's twin - run_clustering_tuning_sweep
    sat unprotected between two try/except blocks in _run_one_method_tuning.
    A ValueError raised inside it must produce a clean logging.error +
    return 1, not propagate as a raw unhandled exception out of main()."""
    input_dir = _build_matrix(tmp_path, monkeypatch)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    def _raise(*args, **kwargs):
        raise ValueError("subjects sub-00 and sub-05 never co-sampled together")

    monkeypatch.setattr(dim_reduction_clustering, "run_clustering_tuning_sweep", _raise)

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(
        json.dumps(
            {
                "kmeans": {
                    "params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"},
                    "tuning_grid": {"n_clusters": [2, 3]},
                }
            }
        )
    )

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "tune1",
        "overwrite": False,
        "fine_tuning": True,
        "viz_n_components": 2,
        "color_by": [],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc_valueerror.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 1


def test_dim_reduction_clustering_viz_embedding_refit_when_n_components_above_viz(tmp_path, monkeypatch):
    """Real end-to-end test of the double-embedding mechanism (2026-08 session):
    clustering runs on the full n_components=4 embedding (saved as-is in
    matrix.npy), but every plot uses a separately-fit 2-component embedding
    (viz_n_components) instead of an invalid slice - and the optional
    color_by bonus feature writes its own embedding/ folder.
    """
    input_dir = _build_matrix(tmp_path, monkeypatch)
    _write_participants_registry(tmp_path, monkeypatch, n_subjects=12)
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(
        json.dumps({"umap": {"params": {"n_neighbors": 4, "min_dist": 0.1, "n_components": 4, "random_state": 0}}})
    )
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    output_root = tmp_path / "drc_out"
    cfg = {
        "project": "testproj",
        "input_path": str(input_dir),
        "reduction_method": "umap",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "viz_n_components": 2,
        "color_by": ["dataset"],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 0

    out_dir = next(p for p in (output_root / "production" / "umap" / "kmeans").iterdir() if p.is_dir())
    embedding = np.load(out_dir / "matrix.npy")
    assert embedding.shape == (12, 4)  # the real, saved clustering embedding - unaffected by viz
    assert (out_dir / "cluster_plot.png").stat().st_size > 0  # still a valid 2D plot, not a broken slice

    embedding_dir = next(p for p in (output_root / "production" / "umap" / "embedding").iterdir() if p.is_dir())
    assert (embedding_dir / "embedding_plot_dataset.png").stat().st_size > 0


def test_dim_reduction_clustering_viz_n_components_3_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(dim_reduction_clustering, "LOGS_ROOT", tmp_path / "drc_logs")

    reduction_params_path = tmp_path / "params_reduction.json"
    reduction_params_path.write_text(json.dumps({"pca": {"params": {"n_components": 2}}}))
    clustering_params_path = tmp_path / "params_clustering.json"
    clustering_params_path.write_text(json.dumps({"kmeans": {"params": {"n_clusters": 3, "random_state": 0, "n_init": "auto"}}}))

    cfg = {
        "project": "testproj",
        "input_path": str(tmp_path / "does-not-matter"),
        "reduction_method": "pca",
        "reduction_params_file": str(reduction_params_path),
        "clustering_methods": ["kmeans"],
        "clustering_params_file": str(clustering_params_path),
        "output_root": str(tmp_path / "drc_out"),
        "session_name": "run1",
        "overwrite": False,
        "fine_tuning": False,
        "viz_n_components": 3,
        "color_by": [],
        "run_notes": None,
    }
    cfg_path = tmp_path / "drc.json"
    cfg_path.write_text(json.dumps(cfg))

    assert dim_reduction_clustering.main(["--config", str(cfg_path)]) == 1
