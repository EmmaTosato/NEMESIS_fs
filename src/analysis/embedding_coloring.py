"""Registry of embedding-coloring modes shared between dim_reduction.py's
production and fine-tuning output (src/analysis/embedding_plots.py) and,
since 15-08-26, src.pipeline.embedding_app's interactive explorer (which
reads this registry directly to drive its color buttons, independent of any
pipeline's own `color_by` config - see src/analysis/embedding_app.py).

Adding a new way to color an embedding (e.g. a clinical score) means adding
one entry here plus its name to a pipeline's `color_by` config list - no
other code changes. Each mode declares whether its values are a category
(rendered with a legend, see plotting.plot_embedding_categorical) or a
continuous quantity (rendered with a colorbar, see
plotting.plot_embedding_continuous), and how to compute one value per
subject from (metadata, X) - X is the raw feature matrix, used only by modes
that derive a value from it (volume); modes that only need metadata
(dataset, side, cluster_label) ignore their X argument. Not every mode is
meaningful for every consumer's own metadata.csv (e.g. cluster_label only
ever exists in clustering.py's output, never dim_reduction.py's) - a
consumer reading a metadata.csv without a given mode's column gets a clear
ValueError from build_embedding_figure/PERSISTED_COLUMN_BY_MODE lookup, not
a silently blank plot.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from src.features.clinical import join_lesion_side, join_nihss

ColorKind = Literal["categorical", "continuous"]


@dataclass(frozen=True)
class ColorMode:
    kind: ColorKind
    compute: Callable[[pd.DataFrame, np.ndarray], np.ndarray]
    label: str
    # continuous only - see plot_embedding_continuous/plot_embedding_grid_blocks's
    # own log_scale param. Ignored for categorical modes.
    log_scale: bool = False


COLOR_MODES: dict[str, ColorMode] = {
    "dataset": ColorMode(
        kind="categorical",
        compute=lambda metadata, X: metadata["dataset"].to_numpy(),
        label="dataset",
    ),
    "side": ColorMode(
        kind="categorical",
        compute=lambda metadata, X: join_lesion_side(metadata).to_numpy(),
        label="lesion side",
    ),
    "volume": ColorMode(
        kind="continuous",
        # Same quantity metadata's lesion_volume_voxels column already uses -
        # voxel count, not ml (a scalar rescaling, no need to convert here either).
        compute=lambda metadata, X: X.sum(axis=1),
        label="lesion volume (voxels)",
        # Heavily right-skewed (a handful of large-lesion outliers otherwise
        # stretch a linear scale so far that almost every other point looks
        # the same dark color - visually confirmed on the real 1150-subject
        # cohort, session 2026-08-04) - log makes the whole cohort's spread
        # readable again.
        log_scale=True,
    ),
    "nihss": ColorMode(
        kind="continuous",
        # NaN for subjects with no resolvable NIHSS (dataset-wide gap, e.g.
        # PASPORT, or a per-subject missing cell) - see join_nihss and
        # plot_embedding_continuous's NaN handling (rendered neutral gray).
        compute=lambda metadata, X: join_nihss(metadata).to_numpy(),
        label="NIHSS (severity)",
        # Linear: less skewed than volume, and kept on the same viridis
        # palette as volume (not a second hue family) - deliberately, on
        # request, log_scale=False is the actual differentiator between the
        # two modes' plots, not the colormap.
    ),
    # clustering.py's own production output (docs/dev/clustering_migration_plan.md §3,
    # 15-08-26) - never consumed via a pipeline's `color_by` config (dim_reduction.py runs
    # never have this column, clustering.py's own cluster_plot.png/cluster_plot_interactive.html
    # color by cluster_labels directly, not through this registry, see docs/dev/plotting.md),
    # only by src.pipeline.embedding_app, which reads whichever metadata.csv a run actually
    # wrote and offers every registered mode that column supports. HDBSCAN's noise label (-1)
    # is deliberately rendered as just another category here (no special gray treatment like
    # plot_clusters_2d's _NOISE_COLOR) - this is a generic explorer over any metadata column,
    # not the dedicated cluster-diagnostic plot; the legend still shows "-1" as its own entry,
    # nothing is hidden.
    "cluster_label": ColorMode(
        kind="categorical",
        compute=lambda metadata, X: metadata["cluster_label"].to_numpy(),
        label="cluster",
    ),
}


def resolve_color_mode(name: str) -> ColorMode:
    """Raises ValueError (with the known-modes list) if `name` isn't
    registered - a color_by entry from config must fail with a clear
    message, not a raw KeyError.
    """
    if name not in COLOR_MODES:
        raise ValueError(f"unknown color_by mode {name!r} - known: {sorted(COLOR_MODES)}")
    return COLOR_MODES[name]


# color_by mode name -> metadata column written once, at production time, by
# src.features.clinical.enrich_metadata_with_lesion_info ("dataset" is written earlier
# still, by build_lesion_matrix.py). Any reader of an already-produced run.py's
# metadata.csv (a replot script, the embedding_app, a notebook) should read the value
# straight from this column rather than recomputing it via COLOR_MODES[name].compute -
# that would either re-join "side"/"nihss" from participants.tsv as it exists *right
# now* (silently drifting from what the run actually recorded), or, for "volume", need
# the raw voxel feature matrix, which a read-only consumer of an existing run
# deliberately never reloads. Single source of truth for this mapping - previously
# duplicated privately in scripts/replot_dim_reduction.py and the exploratory notebook
# (see docs/dev/plotting.md's "no silent fallback"/lessons_learned.md #12 on why a 3rd
# private copy wasn't added instead). A mode with no entry here (e.g. a future
# compute-only mode never persisted to metadata.csv) is the caller's own responsibility
# to skip - this module has no opinion on how a missing column is handled.
PERSISTED_COLUMN_BY_MODE: dict[str, str] = {
    "dataset": "dataset",
    "side": "lesion_side",
    "volume": "lesion_volume_voxels",
    "nihss": "nihss",
    "cluster_label": "cluster_label",
}
