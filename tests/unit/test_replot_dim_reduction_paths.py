"""`src/pipeline/replot_dim_reduction.py`: `main` (codici d'uscita, messaggi), layout flat/legacy del clustering,
sovrascrittura sul posto e modalità cliniche lette da un registro isolato (mai da `assets/metadata/` vero)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis.embedding_coloring import COLOR_MODES
from src.pipeline import replot_dim_reduction as replot
from src.utils import participants as participants_registry
from src.utils.artifacts import save_matrix
from tests.factories.ids import subject_ids

N = 6
IDS = subject_ids(N)


@pytest.fixture(autouse=True)
def registry(tmp_path, monkeypatch):
    root = tmp_path / "metadata"
    root.mkdir()
    pd.DataFrame({
        "subject_id": IDS, "original_id": IDS, "dataset": "siteA", "disease_id": "ST",
        "has_lesion": "True", "has_sdc": "False", "has_features": "False",
        "lesion_side": ["left", "right"] * 3, "NIHSS": [1, 2, 3, 4, 5, 6],
        "lesion_volume_voxels_2mm": [10, 20, 30, 40, 50, 60],
    }).to_csv(root / "participants.csv", index=False)
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    return root


def _save(run_dir, X=None, **columns):
    X = np.random.default_rng(0).random((N, 2)) if X is None else X
    metadata = pd.DataFrame({"subject_id": IDS, "dataset": ["siteA", "siteB"] * 3, **columns})
    save_matrix(run_dir, X, metadata, readme_lines=["# t"], overwrite=False)
    return run_dir


def _embedding_run(tmp_path, **columns):
    return _save(tmp_path / "res" / "lesion" / "dim_reduction" / "umap" / "10-08_s1", **columns)


def test_main_success_prints_one_line_per_written_plot_and_returns_0(tmp_path, capsys):
    run = _embedding_run(tmp_path, lesion_side="x", lesion_volume_voxels=1, nihss=1.0)
    assert replot.main(["--run-dir", str(run)]) == 0
    out = capsys.readouterr().out.splitlines()
    assert all(line.startswith("plot rewritten to ") for line in out)
    written = sorted(p.name for p in run.glob("embedding_plot_*.png"))
    assert written == ["embedding_plot_dataset.png", "embedding_plot_nihss.png", "embedding_plot_side.png",
                       "embedding_plot_unico.png", "embedding_plot_volume.png"]
    assert len(out) == len(written)
    assert all((run / name).stat().st_size > 0 for name in written)


def test_only_modes_whose_column_is_in_metadata_are_plotted_and_skips_are_warned(tmp_path, caplog):
    run = _embedding_run(tmp_path)  # solo `dataset`
    with caplog.at_level("WARNING"):
        paths = replot.replot(run)
    assert sorted(p.name for p in paths) == ["embedding_plot_dataset.png", "embedding_plot_unico.png"]
    skipped = [r.getMessage() for r in caplog.records if "skipping this plot" in r.getMessage()]
    assert len(skipped) == len(COLOR_MODES) - 1  # una per ogni modalità senza colonna (dataset è l'unica presente)


def test_replot_overwrites_existing_plots_in_place(tmp_path):
    run = _embedding_run(tmp_path)
    (run / "embedding_plot_unico.png").write_bytes(b"stale")
    replot.replot(run)
    assert (run / "embedding_plot_unico.png").read_bytes().startswith(b"\x89PNG")


@pytest.mark.parametrize("missing", ["absent_dir", "no_manifest"])
def test_main_missing_run_returns_1_with_a_readable_message(tmp_path, capsys, missing):
    run = tmp_path / "nowhere"
    if missing == "no_manifest":
        run.mkdir()
    assert replot.main(["--run-dir", str(run)]) == 1
    out = capsys.readouterr().out
    assert out.startswith("error: ") and "manifest.json" in out


def test_main_three_component_embedding_returns_1_and_writes_no_plot(tmp_path, capsys):
    run = _save(tmp_path / "r" / "umap" / "10-08_s1", X=np.zeros((N, 3)))
    assert replot.main(["--run-dir", str(run)]) == 1
    assert "3 component(s)" in capsys.readouterr().out
    assert not list(run.glob("*.png"))


def test_main_metadata_without_dataset_returns_1(tmp_path, capsys):
    run = tmp_path / "r" / "umap" / "10-08_s1"
    save_matrix(run, np.zeros((N, 2)), pd.DataFrame({"subject_id": IDS}), readme_lines=["# t"], overwrite=False)
    assert replot.main(["--run-dir", str(run)]) == 1
    assert "no 'dataset' column" in capsys.readouterr().out
    assert not list(run.glob("*.png"))


@pytest.mark.parametrize(
    "parts, expected",
    [
        (("production", "kmeans", "10-08_s1"), None),  # layout piatto di clustering.py
        (("production", "umap", "kmeans", "10-08_s1"), "umap"),  # layout legacy dim_reduction_clustering
    ],
)
def test_reduction_method_label_depends_on_the_depth_of_the_run_path(tmp_path, parts, expected):
    assert replot._reduction_method_label_for(tmp_path.joinpath(*parts)) == expected


def test_flat_clustering_run_gets_generic_axis_labels(tmp_path, monkeypatch):
    run = _save(tmp_path / "out" / "production" / "kmeans" / "10-08_s1", cluster_label=[0, 1, 0, 1, 0, 1])
    seen = {}
    real = replot.plot_clusters_2d

    def spy(X, labels, path, xlabel, ylabel, title):
        seen.update(xlabel=xlabel, ylabel=ylabel, title=title, labels=list(labels))
        return real(X, labels, path, xlabel, ylabel, title)

    monkeypatch.setattr(replot, "plot_clusters_2d", spy)
    paths = replot.replot(run)
    assert paths == [run / "cluster_plot.png"] and paths[0].stat().st_size > 0
    assert (seen["xlabel"], seen["ylabel"]) == ("viz dim 1", "viz dim 2")
    assert "kmeans" in seen["title"].lower()
    assert seen["labels"] == [0, 1, 0, 1, 0, 1]


def test_legacy_nested_clustering_run_labels_axes_with_the_reduction_method(tmp_path, monkeypatch):
    run = _save(tmp_path / "out" / "production" / "umap" / "hdbscan" / "10-08_s1", cluster_label=[0, -1, 0, -1, 0, 0])
    seen = {}
    real = replot.plot_clusters_2d
    monkeypatch.setattr(
        replot, "plot_clusters_2d",
        lambda X, labels, path, xlabel, ylabel, title: (seen.update(x=xlabel, y=ylabel, t=title), real(X, labels, path, xlabel, ylabel, title))[1],
    )
    replot.replot(run)
    assert (seen["x"], seen["y"]) == ("umap dim 1", "umap dim 2")
    assert "umap" in seen["t"].lower() and "hdbscan" in seen["t"].lower()


def test_registry_without_a_clinical_column_aborts_cleanly_with_return_1(tmp_path, registry, capsys):
    """Una modalità clinica presente in metadata ma non nel registro non è un traceback: `main` risponde 1 col perché."""
    frame = pd.read_csv(registry / "participants.csv").drop(columns=["lesion_side"])
    frame.to_csv(registry / "participants.csv", index=False)
    run = _embedding_run(tmp_path, lesion_side="x")
    assert replot.main(["--run-dir", str(run)]) == 1
    assert "registry has no 'lesion_side' column" in capsys.readouterr().out
