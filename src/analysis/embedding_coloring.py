"""Registry of embedding-coloring modes shared between dim_reduction.py's
production/fine-tuning output (src/analysis/embedding_plots.py) and
src.pipeline.embedding_app's interactive explorer. Adding a new way to color
an embedding means adding one entry here plus its name to a pipeline's
`color_by` config list - no other code changes.

Read-only: no mode ever recomputes a value from X - see docs/dev/plotting.md
for why (a real bug this design replaced). A mode's values come from one of
two persisted places, never from a live recomputation:

- assets/metadata/participants.csv, the project's subject registry, for facts
  about a SUBJECT that are true regardless of which run is being plotted
  (`lesion_side`, `NIHSS`, lesion volume, overall disconnection) - see docs/dev/metadata.md;
- the run's own metadata.csv, only for facts that belong to that RUN and
  exist nowhere else (`dataset`, `cluster_label`).

The registry lookup (2026-09-06) replaced a per-run enrichment step that used
to copy those clinical columns into every run's own metadata.csv: they now
have exactly one home, and a run plotted today gets them whether or not that
step was ever applied to it.

**The registry wins** whenever a mode declares a registry_column (30-09-26, on
request: "dash deve prendere da participants o, se sono info specifiche
dell'embedding, dal suo relativo metadata.csv"). Until then the order was the
other way round - the run's own column first - so an old run still carrying a
stale `lesion_side`/`nihss`/`lesion_volume_voxels` column from before the
2026-09-06 migration was silently coloured from that copy instead of from the
registry, and two runs of the same subjects could disagree. Lesion volume in
particular is per-run in a way that is NOT comparable: each run's own
`lesion_volume_voxels` counts voxels on whatever grid that build_lesion_matrix
call used, while the registry's `lesion_volume_voxels_2mm`/`_1mm` are computed
once, on one fixed grid, for every subject.
"""

from __future__ import annotations

import logging
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
    # None (default): a subject-level fact meaningful regardless of which modality built the
    # embedding (dataset/side/NIHSS/lesion volume are all plottable on an sdc run too, e.g. to
    # relate disconnection clusters to lesion size). A ProductionRun.modality value otherwise:
    # the mode only makes sense on a run of that modality, enforced by
    # src.analysis.embedding_app.build_embedding_figure's own modality parameter - checked
    # there, not here, since this module has no ProductionRun concept of its own.
    restricted_to_modality: str | None = None


# Lesion volume is measured on a voxel grid, and the registry holds one column per grid
# (src/pipeline/enrich_metadata.py's lesion_metrics.grids). The app offers whichever of these
# actually exists in participants.csv today (available_volume_grids) as a small button row of
# its own, so the choice of grid is explicit instead of buried in whichever column a run
# happened to write. A closed vocabulary: an unknown grid raises rather than being looked up.
VOLUME_MODE = "volume"
DEFAULT_VOLUME_GRID = "2mm"
_VOLUME_GRID_COLUMNS: dict[str, str] = {
    "2mm": "lesion_volume_voxels_2mm",
    "1mm": "lesion_volume_voxels_1mm",
}


def volume_grid_column(grid: str) -> str:
    """The participants.csv column holding lesion volume on `grid`.

    Raises ValueError for an unregistered grid - a typo'd grid must fail with the known list,
    never resolve to a column name built by string interpolation."""
    if grid not in _VOLUME_GRID_COLUMNS:
        raise ValueError(f"unknown volume grid {grid!r} - known: {sorted(_VOLUME_GRID_COLUMNS)}")
    return _VOLUME_GRID_COLUMNS[grid]


def available_volume_grids() -> list[str]:
    """The grids the registry can actually serve right now, in _VOLUME_GRID_COLUMNS order.

    Read from participants.csv rather than declared, because the 1mm column only exists once
    enrich_metadata.py has been run with a "1mm" grid in its own config - the app must offer
    what is there, not what is theoretically supported, and must not offer a button that would
    raise when clicked. DEFAULT_VOLUME_GRID first if present, so the default is always offered.
    """
    registry = load_participants_registry()
    return [grid for grid, column in _VOLUME_GRID_COLUMNS.items() if column in registry.columns]


# Overall disconnection per subject, written into the registry by enrich_metadata from
# assets/metadata/sdc_metadata.csv (src.pipeline.compute_sdc_metadata). One fixed grid: the
# disconnectome maps exist only at 1mm, so unlike lesion volume there is no grid to choose and
# no button row for it. The names are those compute_sdc_metadata writes - its column prefixes
# (src.features.sdc.DISCONNECTION_*_PREFIX) plus the grid name configured in
# config/pipelines/compute_sdc_metadata.json - repeated here rather than imported, so this
# module stays free of the imaging stack; tests/unit/test_embedding_coloring.py pins that the
# two agree.
_DISCONNECTION_LOAD_COLUMN = "disconnection_load_voxels_1mm"
_DISCONNECTION_MEAN_COLUMN = "disconnection_mean_1mm"


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
        registry_column=_VOLUME_GRID_COLUMNS[DEFAULT_VOLUME_GRID],
        label="lesion volume (voxels)",
        # Heavily right-skewed (a handful of large-lesion outliers otherwise
        # stretch a linear scale so far that almost every other point looks
        # the same dark color - visually confirmed on the real 1150-subject
        # cohort, session 2026-08-04) - log makes the whole cohort's spread
        # readable again.
        log_scale=True,
    ),
    # How disconnected a subject is overall, the disconnection counterpart of "volume": the sum of
    # its disconnection probability over the brain (a probability-weighted voxel count), and the
    # same sum over the number of brain voxels (a 0-1 fraction). The divisor is a constant of the
    # grid, so the two colour every point identically and differ only in the number the colorbar
    # prints - both are offered because the voxel count reads like "lesion volume" and the
    # fraction reads like "how much of the brain, on average".
    #
    # Linear, NOT log like "volume": measured on the full cohort (06-10-26) the load has
    # skew 1.5 and max/median 7.6, against 4.1 and 97 for lesion volume. The reason volume needs
    # a log scale - a few huge outliers flatten everyone else to one colour - does not hold, and
    # a log scale would over-correct (log10 skew -0.8) by stretching the low-disconnection tail.
    "disconnection_load": ColorMode(
        kind="continuous",
        column=_DISCONNECTION_LOAD_COLUMN,
        registry_column=_DISCONNECTION_LOAD_COLUMN,
        label="disconnection load (voxels)",
        # Restricted to sdc runs, unlike volume/side/nihss (26-10-06, on request): a "lesion"
        # run's own embedding is about lesion location/volume, and this app does not yet have a
        # production use for colouring it by overall disconnection - revisit if one comes up.
        restricted_to_modality="sdc",
    ),
    "disconnection_mean": ColorMode(
        kind="continuous",
        column=_DISCONNECTION_MEAN_COLUMN,
        registry_column=_DISCONNECTION_MEAN_COLUMN,
        label="mean disconnection (0-1)",
        restricted_to_modality="sdc",
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


def color_values(
    metadata: pd.DataFrame, mode_name: str, registry_column: str | None = None
) -> np.ndarray:
    """The one place every embedding-coloring consumer in this repo (dim_reduction.py's
    production/tuning plots via embedding_plots.py, src.pipeline.embedding_app's interactive
    explorer) reads a color mode's actual values - straight from metadata's own column
    (resolve_color_mode(mode_name).column), never recomputed.

    Resolution order (30-09-26, inverted on request - see this module's docstring): the
    subject registry for any mode that declares a registry_column, and the run's own
    metadata.csv only for modes that declare none (`dataset`, `cluster_label`), which exist
    nowhere else. A mode that can be resolved from neither raises - a caller offering a mode
    whose values don't exist anywhere needs to know that explicitly, not get a silently
    blank/wrong plot.

    registry_column overrides which registry column this mode reads - used by the app to
    switch the "volume" mode between the 2mm and 1mm grids (volume_grid_column) without a
    second, near-identical ColorMode entry per grid.
    """
    mode = resolve_color_mode(mode_name)
    column = mode.registry_column if registry_column is None else registry_column
    if column is not None:
        return _values_from_registry(metadata, mode, mode_name, column)
    if mode.column in metadata.columns:
        return metadata[mode.column].to_numpy()
    raise ValueError(
        f"metadata has no {mode.column!r} column for color mode {mode_name!r} - "
        "run the pipeline step that produces it first (clustering.py for 'cluster_label')"
    )


def _values_from_registry(
    metadata: pd.DataFrame, mode: ColorMode, mode_name: str, registry_column: str
) -> np.ndarray:
    """Resolve a subject-level clinical mode from assets/metadata/participants.csv.

    Used when the run's own metadata.csv doesn't carry the column - which is the normal
    case since these values stopped being copied into each run's metadata (2026-09-06).
    Reached only for modes that declare a registry_column, never as a blanket fallback.

    Raises ValueError if the registry hasn't been enriched with that variable yet
    (src/pipeline/enrich_metadata.py).

    A plotted subject with NO registry row is NOT an error (30-09-26): it gets the same
    missing value as a subject that has a row with an empty cell - NaN for a continuous mode
    (drawn neutral gray by plot_embedding_continuous), the "unknown" bucket for a categorical
    one - and the count is logged once. For a colour, "absent from the registry" and "present
    but blank" are the same fact: there is no value to paint with. Raising instead would make
    a whole run unplottable because a handful of its subjects predate the last
    populate_metadata.py pass, which is the same trade the cluster-description panel settled
    the same way (src/analysis/cluster_description.py::cluster_composition).
    """
    if "subject_id" not in metadata.columns:
        raise ValueError(
            f"color mode {mode_name!r} resolves from the subject registry, which needs a "
            f"'subject_id' column in metadata; got {list(metadata.columns)}"
        )
    registry = load_participants_registry()
    if registry_column not in registry.columns:
        raise ValueError(
            f"the subject registry has no {registry_column!r} column for color mode "
            f"{mode_name!r} - run src/pipeline/enrich_metadata.py to populate it"
        )

    lookup = registry.set_index("subject_id")[registry_column]
    unregistered = sorted(set(metadata["subject_id"]) - set(lookup.index))
    if unregistered:
        logging.warning(
            "color mode %r: %d/%d subject(s) have no row in the subject registry - drawn as "
            "missing (%s): %s",
            mode_name, len(unregistered), len(metadata),
            "gray" if mode.kind == "continuous" else UNKNOWN_CATEGORICAL, unregistered[:5],
        )

    # .map leaves an unregistered subject as NaN, which is exactly the missing value an
    # empty registry cell already produces - handled identically below.
    values = metadata["subject_id"].map(lookup)
    if mode.kind == "categorical":
        # This mode's values get sorted as plain strings downstream - a NaN would raise
        # TypeError, so an unresolved subject becomes the explicit "unknown" bucket.
        return values.fillna(UNKNOWN_CATEGORICAL).to_numpy()
    # coerce, not raise: an unregistered subject (or a blank cell) is NaN here by design.
    return pd.to_numeric(values, errors="coerce").to_numpy()
