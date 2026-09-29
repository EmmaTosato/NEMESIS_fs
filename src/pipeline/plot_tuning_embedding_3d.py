"""Standalone, read-only utility: render one already-computed 3-component tuning-sweep
embedding as an interactive, rotatable Plotly 3D scatter (one HTML per color mode), without
recomputing anything.

Why this exists: src/pipeline/dim_reduction.py's fine-tuning output only ever writes a
*static*, always-2D "embeddings_grid_*.png" diagnostic for every leaf, including
n_components=3 leaves (see _TUNING_GRID_N_COMPONENTS in dim_reduction.py) - a non-rotatable
static 3D scatter is unreadable, so a 3-component leaf's real 3rd dimension is otherwise never
actually visible anywhere. src.pipeline.embedding_app already solves exactly this for
*production* runs (2D/3D auto, rotatable, color buttons) but is deliberately scoped to
production only (see src/analysis/embedding_app.py's module docstring - tuning sweeps are a
different question, answered by src.pipeline.generate_understanding_umap_report's static grid
instead). This script reuses embedding_app's own plotting primitive
(build_embedding_figure - a pure function of embedding + metadata + color mode, no
production-run concept baked in) to answer "let me actually see this one 3-component tuning
combination in 3D", without extending either of those two tools' documented scope.

Reads embeddings.npz + metadata.csv straight off disk (same "replot, never re-fit" contract as
scripts/replot_dim_reduction.py) - --combo-key must name an entry in embeddings.npz whose
embedding has exactly 3 columns (raises ValueError otherwise, never silently sliced - see
.claude/lessons_learned.md #16).

Writes embedding_3d_unico.html plus one embedding_3d_<name>.html per
src.analysis.embedding_coloring.COLOR_MODES entry whose own backing column is present in
--metadata-csv (skipped with a WARNING otherwise, same convention as replot_dim_reduction.py).

Usage:
    PYTHONPATH=. conda run -n nemesis python scripts/plot_tuning_embedding_3d.py \\
        --embeddings-npz results/lesion/dim_reduction/tuning/umap/26-08_s1.2/embeddings.npz \\
        --metadata-csv results/lesion/dim_reduction/tuning/umap/26-08_s1.2/metadata.csv \\
        --combo-key "metric=dice,n_components=3,n_neighbors=5,min_dist=0.0" \\
        --reduction-method umap \\
        --output-dir results/lesion/dim_reduction/tuning/umap/26-08_s1.2/metric=dice/n_components=3
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.embedding_app import COLOR_MODE_ORDER, NEUTRAL_MODE, build_embedding_figure
from src.analysis.embedding_coloring import COLOR_MODES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render one 3-component tuning-sweep embedding as an interactive, "
        "rotatable Plotly 3D scatter - one HTML per color mode."
    )
    parser.add_argument("--embeddings-npz", required=True, help="Tuning run's own embeddings.npz (top-level, not a leaf)")
    parser.add_argument("--metadata-csv", required=True, help="Tuning run's own metadata.csv (top-level, same row order)")
    parser.add_argument("--combo-key", required=True, help="Exact key in embeddings.npz to render - must be a 3-column embedding")
    parser.add_argument("--reduction-method", required=True, help="e.g. umap, tsne - used for axis labels/title only")
    parser.add_argument("--output-dir", required=True, help="Directory to write embedding_3d_*.html into")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    embeddings_npz = Path(args.embeddings_npz)
    metadata_csv = Path(args.metadata_csv)
    output_dir = Path(args.output_dir)

    try:
        embedding, metadata = _load_combo(embeddings_npz, metadata_csv, args.combo_key)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    xlabel, ylabel, zlabel = (f"{args.reduction_method} dim {i}" for i in (1, 2, 3))

    _write_one(embedding, metadata, NEUTRAL_MODE, xlabel, ylabel, zlabel, args, output_dir, "unico")
    for mode_name in COLOR_MODE_ORDER:
        if mode_name == NEUTRAL_MODE:
            continue
        column = COLOR_MODES[mode_name].column
        if column not in metadata.columns:
            logging.warning("skipping color mode %r: metadata.csv has no %r column", mode_name, column)
            continue
        _write_one(embedding, metadata, mode_name, xlabel, ylabel, zlabel, args, output_dir, mode_name)

    logging.info("done - HTML files written to %s", output_dir)
    return 0


def _load_combo(embeddings_npz: Path, metadata_csv: Path, combo_key: str) -> tuple[np.ndarray, pd.DataFrame]:
    if not embeddings_npz.is_file():
        raise FileNotFoundError(f"embeddings_npz not found: {embeddings_npz}")
    if not metadata_csv.is_file():
        raise FileNotFoundError(f"metadata_csv not found: {metadata_csv}")

    with np.load(embeddings_npz) as data:
        if combo_key not in data:
            raise KeyError(f"{combo_key!r} not found in {embeddings_npz} - known keys: {sorted(data.keys())}")
        embedding = data[combo_key]

    if embedding.shape[1] != 3:
        raise ValueError(
            f"combo {combo_key!r} has a {embedding.shape[1]}-column embedding, not 3 - "
            "this script only renders 3-component combinations (use the existing 2D grid PNG for a 2-component one)"
        )

    metadata = pd.read_csv(metadata_csv)
    if len(metadata) != embedding.shape[0]:
        raise ValueError(
            f"{metadata_csv} has {len(metadata)} rows but combo {combo_key!r}'s embedding has {embedding.shape[0]} - "
            "metadata_csv must be the same tuning run's own metadata.csv, in the same row order"
        )
    return embedding, metadata


def _write_one(
    embedding: np.ndarray,
    metadata: pd.DataFrame,
    mode_name: str,
    xlabel: str,
    ylabel: str,
    zlabel: str,
    args: argparse.Namespace,
    output_dir: Path,
    file_suffix: str,
) -> None:
    label = "neutral" if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label
    title = f"{args.reduction_method} - {args.combo_key} - {label}"
    fig = build_embedding_figure(embedding, metadata, mode_name, xlabel, ylabel, title, zlabel=zlabel)
    output_path = output_dir / f"embedding_3d_{file_suffix}.html"
    fig.write_html(output_path)
    logging.info("wrote %s", output_path)


if __name__ == "__main__":
    raise SystemExit(main())
