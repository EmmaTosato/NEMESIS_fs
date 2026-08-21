"""Unit tests for src/pipeline/generate_understanding_umap_report.py's main() (the CLI
entry point) - AUDIT_FINDINGS.md #61: this file didn't exist before, main()'s own argument
parsing/error handling had no test coverage of its own (only
src/analysis/understanding_umap_report.py's underlying functions were tested).
"""

import numpy as np
import pandas as pd

from src.pipeline import generate_understanding_umap_report as pipeline

_SUBJECT_IDS = ["sub-1", "sub-2", "sub-3", "sub-4"]


def _metadata() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "subject_id": _SUBJECT_IDS,
            "dataset": ["siteA"] * 4,
            "lesion_volume_voxels": [1200.0, 3400.0, 800.0, 5600.0],
            "lesion_side": ["left", "right", "left", "unknown"],
            "nihss": [4.0, 12.0, 6.0, 7.0],
        }
    )


def _write_umap_tuning_dir(root, metric="dice"):
    root.mkdir(parents=True)
    _metadata().to_csv(root / "metadata.csv", index=False)
    (root / "config.md").write_text('# fake tuning run\n\n```json\n{"base_params": {"n_components": 2}}\n```\n')

    arrays = {}
    for n_components in (2, 3):
        leaf = root / f"metric={metric}" / f"n_components={n_components}"
        leaf.mkdir(parents=True)
        rows = []
        for n_neighbors in (5, 15):
            for min_dist in (0.0, 0.5):
                rows.append({"metric": metric, "n_components": n_components, "n_neighbors": n_neighbors, "min_dist": min_dist, "trustworthiness": 0.9})
                key = f"metric={metric},n_components={n_components},n_neighbors={n_neighbors},min_dist={min_dist}"
                arrays[key] = np.random.default_rng(0).normal(size=(len(_SUBJECT_IDS), n_components))
        pd.DataFrame(rows).to_csv(leaf / "tuning_results.csv", index=False)
    np.savez(root / "embeddings.npz", **arrays)
    return root


def _write_tsne_tuning_dir(root, metric="dice"):
    root.mkdir(parents=True)
    _metadata().to_csv(root / "metadata.csv", index=False)

    leaf = root / f"metric={metric}"
    leaf.mkdir(parents=True)
    rows = []
    arrays = {}
    for perplexity in (5, 15):
        rows.append({"metric": metric, "perplexity": perplexity, "trustworthiness": 0.9})
        key = f"metric={metric},perplexity={perplexity}"
        arrays[key] = np.random.default_rng(1).normal(size=(len(_SUBJECT_IDS), 2))
    pd.DataFrame(rows).to_csv(leaf / "tuning_results.csv", index=False)
    np.savez(root / "embeddings.npz", **arrays)
    return root


def test_main_writes_report_and_returns_0(tmp_path):
    umap_dir = _write_umap_tuning_dir(tmp_path / "umap")
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne")

    exit_code = pipeline.main(["--umap-tuning-dir", str(umap_dir), "--tsne-tuning-dir", str(tsne_dir)])

    assert exit_code == 0
    assert (umap_dir / "understanding_umap_dice.html").is_file()


def test_main_missing_umap_dir_returns_1_not_raw_traceback(tmp_path):
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne")

    exit_code = pipeline.main(
        ["--umap-tuning-dir", str(tmp_path / "does_not_exist"), "--tsne-tuning-dir", str(tsne_dir)]
    )

    assert exit_code == 1


def test_main_cohort_mismatch_returns_1(tmp_path):
    umap_dir = _write_umap_tuning_dir(tmp_path / "umap")
    tsne_dir = _write_tsne_tuning_dir(tmp_path / "tsne")
    # Break the cohort match: tsne's metadata now covers different subjects.
    mismatched = _metadata()
    mismatched["subject_id"] = ["sub-9", "sub-10", "sub-11", "sub-12"]
    mismatched.to_csv(tsne_dir / "metadata.csv", index=False)

    exit_code = pipeline.main(["--umap-tuning-dir", str(umap_dir), "--tsne-tuning-dir", str(tsne_dir)])

    assert exit_code == 1
