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
    # One or two sentences (Italian, like the rest of the app's own prose) shown above the plot
    # while this mode is active: what the colour means and what grey means. Lives here, next to
    # the label and the scale, so a mode's meaning and its description cannot drift apart.
    description: str
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
    # categorical only: the closed vocabulary of this mode's values, in display order. When set,
    # every renderer gives each label the colour of its position HERE, not of its position among
    # the labels a given run happens to contain - a label absent from a run (a rare category in a
    # small cohort) would otherwise shift the colour of every label after it, so the same
    # category would change colour from run to run. A value outside it (and outside
    # UNKNOWN_CATEGORICAL) raises in color_values. None: an open vocabulary (dataset, side),
    # coloured by sorted position among the labels present.
    categories: tuple[str, ...] | None = None


# Lesion volume and overall disconnection are measured on a voxel grid, and the registry holds one
# column per grid (src/pipeline/enrich_metadata.py's lesion_metadata/sdc_metadata copy_columns).
# The app offers whichever of these grids actually exists in participants.csv today
# (available_grids) as a small button row of its own, shown while one of GRID_MODES is active, so
# the choice of grid is explicit instead of buried in whichever column a run happened to write.
# A closed vocabulary: an unknown grid raises rather than being looked up.
#
# The column names are those compute_lesion_metadata / compute_sdc_metadata write - their prefixes
# plus the grid name configured in config/pipelines/compute_{lesion,sdc}_metadata.json - repeated
# here rather than imported, so this module stays free of the imaging stack;
# tests/unit/test_embedding_coloring.py pins that the two agree.
# The categories of src.features.lesion_location.LOCATION_CATEGORIES, repeated here for the same
# reason as the grid column prefixes below (this module stays free of the imaging stack);
# tests/unit/test_embedding_coloring.py pins that the two agree. Same order, which is the legend
# order.
_LOCATION_CATEGORIES: tuple[str, ...] = (
    "infratentorial",
    "subcortical_gray",
    "cortex_only",
    "cortex_white_boundary",
    "white_matter_only",
    "ventricle",
    "unlabeled",
)
# The one grid lesion location is measured on (config/pipelines/compute_lesion_metadata.json,
# `location.grid`): unlike volume and disconnection it has no 1mm column, so it is not a grid mode.
_LOCATION_COLUMN = "location_dominant_2mm"

DEFAULT_GRID = "2mm"
KNOWN_GRIDS: tuple[str, ...] = (DEFAULT_GRID, "1mm")
_GRID_MODE_PREFIXES: dict[str, str] = {
    "volume": "lesion_volume_voxels",
    "disconnection_load": "disconnection_load_voxels",
    "disconnection_mean": "disconnection_mean",
}
GRID_MODES: tuple[str, ...] = tuple(_GRID_MODE_PREFIXES)


def grid_column(mode_name: str, grid: str) -> str:
    """The participants.csv column holding `mode_name`'s value on `grid`.

    Raises ValueError for a mode that is not grid-dependent or an unregistered grid - a typo'd
    name must fail with the known list, never resolve to a column built by string interpolation."""
    if mode_name not in _GRID_MODE_PREFIXES:
        raise ValueError(f"color mode {mode_name!r} has no grid choice - grid modes: {list(GRID_MODES)}")
    if grid not in KNOWN_GRIDS:
        raise ValueError(f"unknown grid {grid!r} - known: {list(KNOWN_GRIDS)}")
    return f"{_GRID_MODE_PREFIXES[mode_name]}_{grid}"


def available_grids() -> list[str]:
    """The grids the registry can serve right now for at least one grid mode, in KNOWN_GRIDS
    order (DEFAULT_GRID first).

    Read from participants.csv rather than declared, because a grid's column only exists once
    enrich_metadata.py has copied it - the app must offer what is there, not what is
    theoretically supported. A grid present for one mode but not another stays offered: picking
    it for the mode that lacks it shows that mode's own "run enrich_metadata" message instead of
    a silently different plot.
    """
    columns = set(load_participants_registry().columns)
    return [
        grid for grid in KNOWN_GRIDS
        if any(grid_column(mode_name, grid) in columns for mode_name in GRID_MODES)
    ]


COLOR_MODES: dict[str, ColorMode] = {
    "dataset": ColorMode(
        kind="categorical", column="dataset", label="dataset",
        description=(
            "Punti colorati per coorte di provenienza. Mostra se l'embedding separa i pazienti "
            "per sito o per acquisizione invece che per la lesione."
        ),
    ),
    # "unknown" sentinel for an unresolvable subject (dataset-wide gap, e.g. PASPORT has no
    # lesion_side column at all, or a per-subject missing cell). The sentinel is applied here,
    # on read: the registry itself stores a plain empty cell, but this mode sorts its values as
    # plain strings, so a NaN mixed in would raise TypeError.
    "side": ColorMode(
        kind="categorical", column="lesion_side", label="lesion side", registry_column="lesion_side",
        description=(
            "Punti colorati per lato della lesione (left, right, both), preso dalla clinica dove è "
            "registrato e altrimenti dalla maschera della lesione. Grigio: lato non disponibile."
        ),
    ),
    # The anatomical category holding most of the lesion (compute_lesion_metadata's
    # `location_dominant_2mm`), one of seven. Grey for the few subjects with no lesion voxel
    # inside the brain, who have no location. Not restricted to a modality: where the lesions of
    # a disconnection cluster sit is exactly what an sdc run is looked at for.
    "location": ColorMode(
        kind="categorical", column=_LOCATION_COLUMN, registry_column=_LOCATION_COLUMN, label="lesion location",
        categories=_LOCATION_CATEGORIES,
        description=(
            "Punti colorati per sede della lesione: la categoria anatomica che ne contiene la quota maggiore. "
            "cortex_white_boundary sono i voxel su cui i due atlanti non concordano (corteccia o bianca). "
            "Grigio: sede non disponibile."
        ),
    ),
    "volume": ColorMode(
        kind="continuous",
        column="lesion_volume_voxels",
        registry_column=grid_column("volume", DEFAULT_GRID),
        label="lesion volume",
        description=(
            "Punti colorati per volume della lesione, in voxel sulla griglia scelta, con scala "
            "logaritmica. Grigio: volume nullo o mancante."
        ),
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
        column=grid_column("disconnection_load", DEFAULT_GRID),
        registry_column=grid_column("disconnection_load", DEFAULT_GRID),
        label="disconnection load",
        description=(
            "Punti colorati per quanta disconnessione strutturale ha il paziente in totale: somma "
            "della probabilità di disconnessione sui voxel del cervello, nella griglia scelta, con "
            "scala lineare."
        ),
        # Restricted to sdc runs, unlike volume/side/nihss (26-10-06, on request): a "lesion"
        # run's own embedding is about lesion location/volume, and this app does not yet have a
        # production use for colouring it by overall disconnection - revisit if one comes up.
        restricted_to_modality="sdc",
    ),
    "disconnection_mean": ColorMode(
        kind="continuous",
        column=grid_column("disconnection_mean", DEFAULT_GRID),
        registry_column=grid_column("disconnection_mean", DEFAULT_GRID),
        label="mean disconnection",
        description=(
            "Punti colorati per probabilità media di disconnessione sul cervello (da 0 a 1). "
            "Ordina i pazienti come il carico di disconnessione: cambia solo l'unità."
        ),
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
        description=(
            "Punti colorati per gravità clinica del deficit (NIHSS, più alto è più grave). "
            "Grigio: NIHSS non registrato, come in tutta la coorte UCL-UK."
        ),
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
    "cluster_label": ColorMode(
        kind="categorical", column="cluster_label", label="cluster",
        description="Punti colorati per cluster assegnato. Il rumore di HDBSCAN compare come categoria -1.",
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
    switch a grid mode (volume, disconnection) between the 2mm and 1mm grids (grid_column)
    without a second, near-identical ColorMode entry per grid.
    """
    mode = resolve_color_mode(mode_name)
    column = mode.registry_column if registry_column is None else registry_column
    if column is not None:
        values = _values_from_registry(metadata, mode, mode_name, column)
    elif mode.column in metadata.columns:
        values = metadata[mode.column].to_numpy()
    else:
        raise ValueError(
            f"metadata has no {mode.column!r} column for color mode {mode_name!r} - "
            "run the pipeline step that produces it first (clustering.py for 'cluster_label')"
        )
    if mode.categories is not None:
        _check_closed_vocabulary(values, mode, mode_name)
    return values


def _check_closed_vocabulary(values: np.ndarray, mode: ColorMode, mode_name: str) -> None:
    """A categorical mode with a closed vocabulary must not meet a value outside it: a label the
    palette has no colour for would otherwise be drawn in whichever colour is left, or crash a
    renderer far from the cause."""
    unexpected = sorted(set(pd.unique(values).tolist()) - set(mode.categories) - {UNKNOWN_CATEGORICAL})
    if unexpected:
        raise ValueError(
            f"color mode {mode_name!r} met value(s) {unexpected} outside its categories "
            f"{list(mode.categories)} - the registry column {mode.registry_column or mode.column!r} "
            "was written by a different version of the pipeline"
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
