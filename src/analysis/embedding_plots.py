"""Shared embedding-plot writer for dim_reduction.py's production and
fine-tuning output, built on plotting.py's primitives plus the
embedding_coloring registry - the single place that knows how to turn "an
embedding + a list of color_by names" into a set of files, so production and
tuning (and, optionally, dim_reduction_clustering.py) never re-implement this
loop themselves.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.embedding_coloring import resolve_color_mode
from src.analysis.plotting import (
    plot_embedding_2d,
    plot_embedding_categorical,
    plot_embedding_continuous,
    plot_embedding_grid_blocks,
    plot_embedding_interactive,
)


def write_embedding_plots(
    embedding: np.ndarray,
    metadata: pd.DataFrame,
    X: np.ndarray,
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
    static PNG (`<file_prefix>_<name>.png`) - and one combined interactive
    HTML, `<file_prefix>_interactive.html`, with a dropdown to switch the
    coloring between every mode in `color_by` that computed successfully,
    instead of a separate HTML file per mode.

    `embedding` must have exactly 2 or 3 columns (this writes *visualization*
    embeddings, already reduced to a plottable size - see
    src/analysis/reduction.py::embedding_for_viz for how a caller gets one).
    With 3 columns, no "unico" static PNG is written at all (only the
    interactive plot renders a 3D embedding anywhere in this module) -
    `zlabel` is required in that case.

    Each static output is wrapped in its own try/except (broad Exception,
    logged as WARNING) - one bad coloring mode (e.g. a dataset with no
    resolvable participants.tsv for lesion_side) must not abort the whole
    run, same convention dim_reduction.py used before this function existed.
    The combined interactive HTML is a single file covering every mode that
    computed successfully, so it can only fail (or be skipped, if every mode
    failed) as one unit - not per mode like the static PNGs.
    """
    n_dims = embedding.shape[1]
    if n_dims not in (2, 3):
        raise ValueError(f"write_embedding_plots supports 2 or 3 embedding dimensions, got {n_dims}")
    if n_dims == 3 and zlabel is None:
        raise ValueError("write_embedding_plots needs zlabel for a 3-component embedding")

    if n_dims == 2:
        try:
            plot_embedding_2d(embedding, output_dir / f"{file_prefix}_unico.png", xlabel, ylabel, title_fn(None))
        except Exception as exc:
            logging.warning("failed to generate 'unico' embedding plot: %s", exc)

    metadata_for_plot = metadata.copy()
    interactive_color_options: list[tuple[str, str]] = []

    for name in color_by:
        mode = resolve_color_mode(name)
        title = title_fn(mode.label)

        try:
            values = mode.compute(metadata, X)
        except Exception as exc:
            logging.warning("failed to compute values for color_by mode %r: %s", name, exc)
            continue

        if n_dims == 2:
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

        metadata_for_plot[name] = values
        interactive_color_options.append((mode.label, name))

    # Interactive HTML stays linear-scale regardless of any mode's log_scale: plotly
    # express has no direct LogNorm-style color-axis equivalent (it would mean
    # log-transforming `values` and manually relabeling the colorbar ticks back
    # to real units) - the static PNGs above are where log_scale actually matters,
    # the interactive view's hover already surfaces each point's real value.
    if interactive_color_options:
        try:
            plot_embedding_interactive(
                embedding,
                metadata_for_plot,
                interactive_color_options,
                output_dir / f"{file_prefix}_interactive.html",
                xlabel,
                ylabel,
                title_fn(None),
                zlabel=zlabel,
            )
        except Exception as exc:
            logging.warning("failed to generate interactive embedding plot: %s", exc)


def write_embedding_grid(
    blocks: list[tuple[str, list[tuple[str, np.ndarray]]]],
    metadata: pd.DataFrame,
    X: np.ndarray,
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
            values = mode.compute(metadata, X)
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
