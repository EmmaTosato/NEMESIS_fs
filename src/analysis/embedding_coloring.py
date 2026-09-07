"""Registry of embedding-coloring modes shared between dim_reduction.py's
production/fine-tuning output (src/analysis/embedding_plots.py) and
src.pipeline.embedding_app's interactive explorer. Adding a new way to color
an embedding means adding one entry here plus its name to a pipeline's
`color_by` config list - no other code changes.

Read-only: no mode ever recomputes a value from X - see docs/dev/plotting.md
for why (a real bug this design replaced). A mode's values come from one of
two persisted places, never from a live recomputation:

- the run's own metadata.csv, for facts that belong to that run (`dataset`,
  `lesion_volume_voxels`, `cluster_label`);
- assets/metadata/participants.csv, the project's subject registry, for
  clinical facts about a subject that are true regardless of which run is
  being plotted (`lesion_side`, `NIHSS`) - see docs/dev/metadata.md.

The registry lookup (2026-09-06) replaced a per-run enrichment step that used
to copy those clinical columns into every run's own metadata.csv: they now
have exactly one home, and a run plotted today gets them whether or not that
step was ever applied to it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from src.utils.participants import load_participants_registry

ColorKind = Literal["categorical", "continuous"]

# Bucket for a categorical mode whose value can't be resolved for a subject.
UNKNOWN_CATEGORICAL = "unknown"


@dataclass(frozen=True)
class ColorMode:
    kind: ColorKind
    column: str  # metadata.csv column this mode reads, when the run carries it itself
    label: str
    # Column in assets/metadata/participants.csv holding this same fact, for modes whose
    # value is a property of the subject rather than of the run. None means the value
    # exists only in the run's own metadata.csv (dataset, lesion_volume_voxels, cluster)
    # and there is nowhere else to legitimately get it from.
    registry_column: str | None = None
    # continuous only - see plot_embedding_continuous/plot_embedding_grid_blocks's
    # own log_scale param. Ignored for categorical modes.
    log_scale: bool = False


COLOR_MODES: dict[str, ColorMode] = {
    "dataset": ColorMode(kind="categorical", column="dataset", label="dataset"),
    # "unknown" sentinel for an unresolvable subject (dataset-wide gap, e.g. PASPORT has no
    # lesion_side column at all, or a per-subject missing cell). The sentinel is applied here,
    # on read: the registry itself stores a plain empty cell, but this mode sorts its values as
    # plain strings, so a NaN mixed in would raise TypeError.
    "side": ColorMode(
        kind="categorical", column="lesion_side", label="lesion side", registry_column="lesion_side"
    ),
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
    # NaN for subjects with no resolvable NIHSS (dataset-wide gap, e.g. UCL-UK records no
    # NIHSS at all, or a per-subject missing cell) - see plot_embedding_continuous's NaN
    # handling (rendered neutral gray). A numeric quantity has no categorical "unknown".
    "nihss": ColorMode(
        kind="continuous",
        column="nihss",
        registry_column="NIHSS",
        label="NIHSS (severity)",
        # Linear: less skewed than volume, and kept on the same viridis
        # palette as volume (not a second hue family) - deliberately, on
        # request, log_scale=False is the actual differentiator between the
        # two modes' plots, not the colormap.
    ),
    # clustering.py's own production output (docs/dev/clustering_migration_plan.md §3,
    # 15-08-26) - never consumed via a pipeline's `color_by` config (dim_reduction.py runs
    # never have this column, clustering.py's own cluster_plot.png colors by
    # cluster_labels directly, not through this registry, see docs/dev/plotting.md),
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

    Resolution order: the run's own metadata.csv column if present, otherwise the subject
    registry for modes that declare a registry_column. A mode that can be resolved from
    neither raises - a caller offering a mode whose values don't exist anywhere (e.g.
    "volume" before build_lesion_matrix.py added lesion_volume_voxels) needs to know that
    explicitly, not get a silently blank/wrong plot.
    """
    mode = resolve_color_mode(mode_name)
    if mode.column in metadata.columns:
        return metadata[mode.column].to_numpy()
    if mode.registry_column is not None:
        return _values_from_registry(metadata, mode, mode_name)
    raise ValueError(
        f"metadata has no {mode.column!r} column for color mode {mode_name!r} - "
        "run the pipeline step that produces it first (build_lesion_matrix.py for "
        "'volume', clustering.py for 'cluster_label')"
    )


def _values_from_registry(metadata: pd.DataFrame, mode: ColorMode, mode_name: str) -> np.ndarray:
    """Resolve a subject-level clinical mode from assets/metadata/participants.csv.

    Used when the run's own metadata.csv doesn't carry the column - which is the normal
    case since these values stopped being copied into each run's metadata (2026-09-06).
    Reached only for modes that declare a registry_column, never as a blanket fallback.

    Raises ValueError if the registry hasn't been enriched with that variable yet
    (src/pipeline/enrich_metadata.py), or if a plotted subject has no registry row at
    all - a run whose subjects aren't in the registry is a real mismatch, not a
    legitimately missing colour.
    """
    if "subject_id" not in metadata.columns:
        raise ValueError(
            f"color mode {mode_name!r} resolves from the subject registry, which needs a "
            f"'subject_id' column in metadata; got {list(metadata.columns)}"
        )
    registry = load_participants_registry()
    if mode.registry_column not in registry.columns:
        raise ValueError(
            f"the subject registry has no {mode.registry_column!r} column for color mode "
            f"{mode_name!r} - run src/pipeline/enrich_metadata.py to populate it"
        )

    lookup = registry.set_index("subject_id")[mode.registry_column]
    unknown = sorted(set(metadata["subject_id"]) - set(lookup.index))
    if unknown:
        raise ValueError(
            f"color mode {mode_name!r}: {len(unknown)} subject(s) of this run have no row in "
            f"the subject registry: {unknown[:5]}"
        )

    values = metadata["subject_id"].map(lookup)
    if mode.kind == "categorical":
        # This mode's values get sorted as plain strings downstream - a NaN would raise
        # TypeError, so an unresolved subject becomes the explicit "unknown" bucket.
        return values.fillna(UNKNOWN_CATEGORICAL).to_numpy()
    return pd.to_numeric(values, errors="raise").to_numpy()
