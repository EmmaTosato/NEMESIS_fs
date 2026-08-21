"""Shared embedding-plot writer for dim_reduction.py's production and
fine-tuning output, built on plotting.py's primitives plus the
embedding_coloring registry - the single place that knows how to turn "an
embedding + a list of color_by names" into a set of files, so production and
tuning never re-implement this loop themselves.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.embedding_coloring import color_values, resolve_color_mode
from src.analysis.plotting import (
    plot_embedding_2d,
    plot_embedding_categorical,
    plot_embedding_continuous,
    plot_embedding_grid_blocks,
)


def write_embedding_plots(
    embedding: np.ndarray,
    metadata: pd.DataFrame,
    color_by: list[str],
    output_dir: Path,
    xlabel: str,
    ylabel: str,
    title_fn: Callable[[str | None], str],
    zlabel: str | None = None,
    file_prefix: str = "embedding_plot",
) -> None:
    """Writes `<file_prefix>_unico.png` (always, single color) plus, for each
    name in `color_by` (resolved via embedding_coloring.COLOR_MODES), a
    static PNG (`<file_prefix>_<name>.png`).

    `embedding` must have exactly 2 or 3 columns (this writes *visualization*
    embeddings, already reduced to a plottable size - see
    src/analysis/reduction.py::embedding_for_viz for how a caller gets one).
    With 3 columns, no static PNG is written at all - a non-rotatable 3D
    scatter is unreadable, so a 3-component embedding gets no rendering from
    this function; explore it interactively instead via
    src.pipeline.embedding_app (docs/guides/embedding_app.md), which reads
    the saved run directly and needs no static file regenerated per run
    (2026-08-14: this used to also write a combined
    `<file_prefix>_interactive.html` via plot_embedding_interactive, removed
    on request - the live app supersedes it for every color mode, not just
    the ones a given `color_by` config happened to list, and covers every
    production run without a per-run file to keep in sync).

    Each static output is wrapped in its own try/except (broad Exception,
    logged as WARNING) - one bad coloring mode (e.g. a dataset with no
    resolvable participants.tsv for lesion_side) must not abort the whole
    run, same convention dim_reduction.py used before this function existed.
    """
    n_dims = embedding.shape[1]
    if n_dims not in (2, 3):
        raise ValueError(f"write_embedding_plots supports 2 or 3 embedding dimensions, got {n_dims}")
    if n_dims == 3 and zlabel is None:
        raise ValueError("write_embedding_plots needs zlabel for a 3-component embedding")

    if n_dims == 3:
        # No static rendering exists for a 3-component embedding anywhere in this
        # module (see docstring) - nothing left to compute color_by values for.
        return

    try:
        plot_embedding_2d(embedding, output_dir / f"{file_prefix}_unico.png", xlabel, ylabel, title_fn(None))
    except Exception as exc:
        logging.warning("failed to generate 'unico' embedding plot: %s", exc)

    for name in color_by:
        mode = resolve_color_mode(name)
        title = title_fn(mode.label)

        try:
            values = color_values(metadata, name)
        except Exception as exc:
            logging.warning("failed to read values for color_by mode %r: %s", name, exc)
            continue

        static_path = output_dir / f"{file_prefix}_{name}.png"
        try:
            if mode.kind == "categorical":
                plot_embedding_categorical(embedding, values, static_path, xlabel, ylabel, title, legend_title=mode.label)
            else:
                plot_embedding_continuous(
                    embedding, values, static_path, xlabel, ylabel, title,
                    colorbar_label=mode.label, log_scale=mode.log_scale,
                )
        except Exception as exc:
            logging.warning("failed to generate %r embedding plot: %s", name, exc)


def write_embedding_grid(
    blocks: list[tuple[str, list[tuple[str, np.ndarray]]]],
    metadata: pd.DataFrame,
    color_by: list[str],
    output_dir: Path,
    xlabel: str,
    ylabel: str,
    title_fn: Callable[[str | None], str],
    file_prefix: str = "embeddings_grid",
) -> None:
    """Writes `<file_prefix>_unico.png` (always) plus one
    `<file_prefix>_<name>.png` per name in `color_by` - each a
    plot_embedding_grid_blocks figure (one row per grid parameter, real
    embeddings, see that function's docstring). `blocks` is built by the
    caller (src/pipeline/dim_reduction.py's tuning mode: for each free grid
    parameter, one (value, embedding) cell per value swept, every other grid
    parameter held at its base/production value) - this function only
    decides which color to render each block set in, same registry/failure
    handling as write_embedding_plots (one bad coloring mode logged as
    WARNING, does not abort the others).
    """
    try:
        plot_embedding_grid_blocks(blocks, output_dir / f"{file_prefix}_unico.png", xlabel, ylabel, title_fn(None))
    except Exception as exc:
        logging.warning("failed to generate 'unico' embedding grid: %s", exc)

    for name in color_by:
        mode = resolve_color_mode(name)
        try:
            values = color_values(metadata, name)
            plot_embedding_grid_blocks(
                blocks,
                output_dir / f"{file_prefix}_{name}.png",
                xlabel,
                ylabel,
                title_fn(mode.label),
                color_values=values,
                color_kind=mode.kind,
                legend_title=mode.label,
                log_scale=mode.log_scale,
            )
        except Exception as exc:
            logging.warning("failed to generate %r embedding grid: %s", name, exc)
