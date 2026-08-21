"""Registry of embedding-coloring modes shared between dim_reduction.py's
production and fine-tuning output (src/analysis/embedding_plots.py) and
src.pipeline.embedding_app's interactive explorer (which reads this registry
directly to drive its color buttons, independent of any pipeline's own
`color_by` config).

Adding a new way to color an embedding (e.g. a clinical score) means adding
one entry here plus its name to a pipeline's `color_by` config list - no
other code changes. Each mode declares whether its values are a category
(rendered with a legend, see plotting.plot_embedding_categorical) or a
continuous quantity (rendered with a colorbar, see
plotting.plot_embedding_continuous), and which metadata.csv column holds its
values.

Single source of truth, read-only (2026-08-17 - collapsed from two separate,
independently-maintained mechanisms: a `compute(metadata, X)` callable that
recomputed a value live for the production/tuning plot writers, and a
`PERSISTED_COLUMN_BY_MODE` mapping used only by embedding_app's read-only
explorer to read the same value already sitting in metadata.csv. The two
were meant to agree but had no way to be checked against each other - the
"volume" mode's live `compute` did `X.sum(axis=1)` with zero guard against a
parcellated (continuous, non-binary) X, silently producing a meaningless
number, while the persisted `lesion_volume_voxels` column right there in the
same metadata.csv was already correct. Every mode now reads its own column
straight from metadata via `color_values` below - never recomputed from X,
never rejoined from participants.tsv live - so a color always matches
exactly what was actually persisted for that run, and a consumer that reads
a metadata.csv without a given mode's column gets a clear ValueError, not a
silently wrong or blank plot. `X` is no longer needed by any color mode: the
raw feature matrix a reduction/clustering pipeline uses to build its
embedding has no role in coloring points by dataset/side/volume/nihss/
cluster - those are per-subject facts already resolved once, upstream, by
src.features.lesion.build_lesion_matrix (lesion_volume_voxels) and
src.pipeline.enrich_lesion_metadata (lesion_side/nihss/other clinical
fields), not derived at plot time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

ColorKind = Literal["categorical", "continuous"]


@dataclass(frozen=True)
class ColorMode:
    kind: ColorKind
    column: str  # metadata.csv column this mode reads - the only place its values come from
    label: str
    # continuous only - see plot_embedding_continuous/plot_embedding_grid_blocks's
    # own log_scale param. Ignored for categorical modes.
    log_scale: bool = False


COLOR_MODES: dict[str, ColorMode] = {
    "dataset": ColorMode(kind="categorical", column="dataset", label="dataset"),
    # "unknown" sentinel for an unresolvable subject (dataset-wide gap, e.g. PASPORT has no
    # lesion_side column at all, or a per-subject missing cell) - written by
    # src.features.clinical.join_lesion_side, via src.pipeline.enrich_lesion_metadata.
    "side": ColorMode(kind="categorical", column="lesion_side", label="lesion side"),
    "volume": ColorMode(
        kind="continuous",
        column="lesion_volume_voxels",
        label="lesion volume (voxels)",
        # Heavily right-skewed (a handful of large-lesion outliers otherwise
        # stretch a linear scale so far that almost every other point looks
        # the same dark color - visually confirmed on the real 1150-subject
        # cohort, session 2026-08-04) - log makes the whole cohort's spread
        # readable again.
        log_scale=True,
    ),
    # NaN for subjects with no resolvable NIHSS (dataset-wide gap, e.g. PASPORT, or a
    # per-subject missing cell) - see src.features.clinical.join_nihss and
    # plot_embedding_continuous's NaN handling (rendered neutral gray).
    "nihss": ColorMode(
        kind="continuous",
        column="nihss",
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
    "cluster_label": ColorMode(kind="categorical", column="cluster_label", label="cluster"),
}


def resolve_color_mode(name: str) -> ColorMode:
    """Raises ValueError (with the known-modes list) if `name` isn't
    registered - a color_by entry from config must fail with a clear
    message, not a raw KeyError.
    """
    if name not in COLOR_MODES:
        raise ValueError(f"unknown color_by mode {name!r} - known: {sorted(COLOR_MODES)}")
    return COLOR_MODES[name]


def color_values(metadata: pd.DataFrame, mode_name: str) -> np.ndarray:
    """The one place every embedding-coloring consumer in this repo (dim_reduction.py's
    production/tuning plots via embedding_plots.py, src.pipeline.embedding_app's interactive
    explorer) reads a color mode's actual values - straight from metadata's own column
    (resolve_color_mode(mode_name).column), never recomputed.

    Raises ValueError if metadata doesn't have that column - a caller offering this mode
    without metadata actually carrying it (e.g. "volume" before build_lesion_matrix.py added
    lesion_volume_voxels, or "side"/"nihss" before src.pipeline.enrich_lesion_metadata.py was
    ever run against this metadata.csv) needs to know that explicitly, not get a silently
    blank/wrong plot.
    """
    mode = resolve_color_mode(mode_name)
    if mode.column not in metadata.columns:
        raise ValueError(
            f"metadata has no {mode.column!r} column for color mode {mode_name!r} - "
            "run the pipeline step that produces it first (build_lesion_matrix.py for "
            "'volume', src.pipeline.enrich_lesion_metadata for 'side'/'nihss')"
        )
    return metadata[mode.column].to_numpy()
