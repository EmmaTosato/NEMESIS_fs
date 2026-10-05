"""Per-cluster demographic/clinical composition summary and plot (29-09-26, on request) - feeds
the "Descrizione del cluster" panel in src/analysis/embedding_app.py.

Every variable here is read from assets/metadata/participants.csv (the project's single subject
registry, src.utils.participants.load_participants_registry) - never from a run's own
metadata.csv. Two reasons, not one: (1) age/sex/education/NIHSS are properties of the subject,
not of the run, exactly the same reasoning src.analysis.embedding_coloring.py's own
registry_column modes already follow for "side"/"nihss"; (2) lesion volume specifically is NOT
read from a run's own metadata.csv here even though embedding_coloring.py's "volume" mode can be
- a run's own lesion_volume_voxels column reflects whichever resample grid (1mm/2mm) that run's
build_lesion_matrix.py call used, not guaranteed the same across runs, while
participants.csv's own lesion_volume_voxels_2mm is computed once, on one fixed grid, for every
admitted subject (100% coverage) - the one comparable-across-runs source for a demographic
summary, where "which grid" is a distinction that doesn't matter the way it does for the
overlap-map's own voxel-level display.

CLUSTER_DESCRIPTION_VARIABLES is a declarative registry (same shape as embedding_coloring.py's
own COLOR_MODES) precisely so that adding a new variable, once assets/metadata/participants.csv
gains one (e.g. stroke type - not in the registry as of 29-09-26, though PSP's own raw
lesion_type already has the datum), is a one-line addition here and nothing else changes.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.analysis.embedding_coloring import COLOR_MODES
from src.utils.participants import load_participants_registry, participants_registry_path

VariableKind = Literal["continuous", "categorical"]

_CLUSTER_LABEL_COLUMN = COLOR_MODES["cluster_label"].column

# Same values as src.analysis.embedding_app's own _FONT_STACK/_TEXT_COLOR (kept as a small,
# deliberate duplication rather than importing from embedding_app - that module is this one's
# own consumer, code_standards.md §1's layering runs analysis -> pipeline/app, never the other
# way, even for a two-constant style import).
_TEXT_COLOR = "#333"
# Every mark in a subplot is that variable's own color (ClusterDescriptionVariable.color): a
# 2px outline at full strength, a pale fill, and semi-transparent points so a few hundred of
# them read as density instead of a solid block.
_BOX_FILL_ALPHA = 0.13
_POINT_ALPHA = 0.45
# One shade off the white surface: present enough to read a value against, recessive enough not
# to compete with the marks (and solid, never dashed - a dashed grid reads as a threshold).
_GRIDLINE_COLOR = "#ececec"
# 3 subplots per row at the app's 1100px page width ~ 330px each, the width at which a 12-13px
# axis stays readable; 1 row of 5 (the 29-09-26 original) gave ~200px and forced tiny type.
_GRID_COLUMNS = 3
_ROW_HEIGHT = 330
# Secondary ink for the coverage line under each subplot title - text wears a text token, never
# a series color.
_MUTED_COLOR = "#767676"
# An explicit trace width, not a bargap: with only 2-3 categories, Plotly's default fills about
# a third of the subplot per bar, which reads as a heavy block rather than a thin mark.
_BAR_WIDTH = 0.42
_BAR_FILL_ALPHA = 0.22


def _rgba(hex_color: str, alpha: float) -> str:
    """#rrggbb -> rgba(r,g,b,alpha), for the pale fills and semi-transparent points derived from
    a variable's own single declared color (one source of truth per variable, not a second hex
    literal per mark that could drift out of step with it)."""
    if not (len(hex_color) == 7 and hex_color.startswith("#")):
        raise ValueError(f"expected a '#rrggbb' color, got {hex_color!r}")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)


@dataclass(frozen=True)
class ClusterDescriptionVariable:
    """decimals: how many digits this variable is worth reporting to in the comparison table
    (continuous only, ignored for categorical). Declared per variable rather than inferred from
    the values at render time, so the same variable formats identically in every cluster's row -
    a column whose precision changed per row would be unreadable to compare down, which is the
    one thing that table exists for. 1 suits age/education/NIHSS; a voxel count is an integer
    and reads as false precision with a decimal.

    color: this variable's own hue, used for its subplot's marks and for its column header in
    the comparison table (29-09-26 feedback: "vorrei più varietà nei colori dato che stiamo
    plottando variabili diverse"). Declared per variable, never assigned by position at render
    time - so a variable keeps the same color whatever else is on screen, and the figure and the
    table can never disagree about what color a variable is. Every value is a member of
    plotting._CATEGORICAL_PALETTE (a test asserts it); the ORDER is deliberately NOT the
    palette's own and was chosen by running the dataviz validator over candidate subsets. This
    5-set passes lightness, chroma, CVD adjacency AND the 3:1 contrast check - the palette's own
    first 5 fail the last one (its pink and sky slots sit at 2.62 and 2.58 against white, too
    washed for a 2px box outline)."""

    name: str
    label: str
    kind: VariableKind
    registry_column: str
    decimals: int = 1
    color: str = "#1a6bab"


@dataclass(frozen=True)
class ClusterStats:
    """One cluster's whole row in the cross-cluster comparison table (29-09-26, on request).

    summaries maps a ClusterDescriptionVariable.name to that variable's own variable_summary
    dict - the exact same function the per-cluster figure uses, never a second, parallel
    implementation of the same statistics that could drift from it."""

    cluster_label: int
    n_total: int
    n_unregistered: int
    summaries: dict[str, dict]


# 29-09-26: today's 5 variables out of the 7 originally requested (istruzione/education kept
# despite 14.7% coverage project-wide - shown with an explicit n/total, never hidden, see
# variable_summary - rather than dropped; hemorrhagic/ischemic stroke type excluded because
# assets/metadata/participants.csv has no column for it yet. The underlying datum is NOT
# absent from the project, only from the registry: participants_PSP.tsv's own lesion_type
# already carries it per subject. Once enrich_metadata.py surfaces it into participants.csv,
# adding it here is exactly the one-line change this registry shape exists for.)
CLUSTER_DESCRIPTION_VARIABLES: list[ClusterDescriptionVariable] = [
    ClusterDescriptionVariable("age", "Età (anni)", "continuous", "age", color="#1a6bab"),
    ClusterDescriptionVariable("sex", "Sesso", "categorical", "sex", color="#d97a29"),
    ClusterDescriptionVariable("education", "Istruzione (anni)", "continuous", "education", color="#7b4fa0"),
    ClusterDescriptionVariable("nihss", "NIHSS", "continuous", "NIHSS", color="#008300"),
    ClusterDescriptionVariable(
        "lesion_volume_voxels", "Volume lesione (voxel)", "continuous", "lesion_volume_voxels_2mm",
        decimals=0, color="#b03d68",
    ),
]


def cluster_composition(metadata: pd.DataFrame, cluster_label: int) -> tuple[pd.DataFrame, list[str]]:
    """(composition, unregistered) for the subjects of `cluster_label` in `metadata` - the
    shared input every stat/plot in this module is built from, computed once (a single registry
    read + join, not one per variable). `composition` is subject_id -> its raw value for every
    CLUSTER_DESCRIPTION_VARIABLES entry; `unregistered` lists, sorted, the cluster's subjects
    that have no row at all in the subject registry.

    A subject missing from the registry is a warning, not a failure (29-09-26, on request -
    it was a hard ValueError until then): a clustering run legitimately outlives the registry
    it was built against, and refusing to describe the other 300 subjects of a cluster because
    13 of them predate the last populate_metadata.py run is a worse answer than describing them
    and saying exactly who is missing. It is not a silent fallback (code_standards.md §0): the
    ids are logged at WARNING here AND returned to the caller, which the app renders as a
    visible line above the figure (embedding_app._unregistered_subjects_warning).

    Such a subject is deliberately KEPT as a row, with a missing value for every variable,
    rather than dropped - so variable_summary's n_total stays the cluster's true size and the
    subject is counted as missing exactly once, for each variable. Dropping it instead would
    shrink the reported denominator, which is the one thing this panel's whole
    n_available/n_total contract exists to prevent.

    Still raises ValueError if `cluster_label` has no subjects in `metadata` at all - an empty
    cluster has nothing to describe, which is a different fact from a described cluster with
    incomplete metadata."""
    cluster_metadata = metadata.loc[metadata[_CLUSTER_LABEL_COLUMN] == cluster_label]
    if cluster_metadata.empty:
        raise ValueError(f"no subjects with {_CLUSTER_LABEL_COLUMN}={cluster_label!r} in this run's metadata")

    registry = load_participants_registry().set_index("subject_id")
    composition, unregistered = _join_registry(cluster_metadata["subject_id"].to_numpy(), registry)
    if unregistered:
        logging.warning(
            "cluster_label=%r: %d/%d subject(s) have no row in %s - kept in the cluster's own "
            "n_total and counted as missing for every variable: %s",
            cluster_label, len(unregistered), len(composition), participants_registry_path(), unregistered,
        )
    return composition, unregistered


def _join_registry(subject_ids: np.ndarray, registry: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """The join itself, split out from cluster_composition so clusters_comparison_stats can run
    it for every cluster against ONE registry read instead of re-reading participants.csv once
    per cluster (5853 rows x however many clusters, on every panel render).

    Deliberately silent: cluster_composition logs the ids for the one cluster whose subjects a
    caller actually needs to chase down, while clusters_comparison_stats reports the same gap
    per cluster as a visible column in its own table. Logging here instead would re-emit the
    whole set on every panel render, once per cluster, drowning the one line that matters."""
    unregistered = sorted(set(subject_ids) - set(registry.index))
    # reindex, not .loc: an unregistered subject becomes a row of missing values instead of a
    # KeyError, which is what keeps it inside n_total (see cluster_composition's docstring).
    aligned = registry.reindex(subject_ids)
    composition = pd.DataFrame({"subject_id": subject_ids})
    for variable in CLUSTER_DESCRIPTION_VARIABLES:
        raw = aligned[variable.registry_column].to_numpy()
        composition[variable.name] = pd.to_numeric(raw, errors="coerce") if variable.kind == "continuous" else raw
    return composition, unregistered


def clusters_comparison_stats(metadata: pd.DataFrame) -> list[ClusterStats]:
    """Every cluster of `metadata`, in ascending label order, each with the same per-variable
    summaries the single-cluster figure shows (29-09-26, on request: "statistiche numeriche a
    confronto tra tutti i vari cluster").

    Built on variable_summary, the same function build_cluster_description_figure calls, so a
    number in the comparison table and the corresponding box plot can never disagree.

    Noise (cluster_label == -1, hdbscan/dbscan's "unassigned" bucket) is included like any other
    row rather than filtered out: it is a real group of this run's subjects and the whole point
    of the table is to see how the groups differ. It is the caller's job to label it as noise -
    this function only reports what is there.

    Raises ValueError if `metadata` has no cluster labels at all (not a clustering run)."""
    if _CLUSTER_LABEL_COLUMN not in metadata.columns:
        raise ValueError(f"this run's metadata has no {_CLUSTER_LABEL_COLUMN!r} column - not a clustering run")
    labels = sorted(int(label) for label in pd.unique(metadata[_CLUSTER_LABEL_COLUMN]))
    if not labels:
        raise ValueError(f"this run's metadata has no {_CLUSTER_LABEL_COLUMN} values at all")

    registry = load_participants_registry().set_index("subject_id")
    stats: list[ClusterStats] = []
    for label in labels:
        subject_ids = metadata.loc[metadata[_CLUSTER_LABEL_COLUMN] == label, "subject_id"].to_numpy()
        composition, unregistered = _join_registry(subject_ids, registry)
        stats.append(
            ClusterStats(
                cluster_label=label,
                n_total=len(composition),
                n_unregistered=len(unregistered),
                summaries={v.name: variable_summary(composition, v) for v in CLUSTER_DESCRIPTION_VARIABLES},
            )
        )
    return stats


def variable_summary(composition: pd.DataFrame, variable: ClusterDescriptionVariable) -> dict:
    """One variable's summary over `composition` (cluster_composition's own output) - n_total is
    the cluster's own size (every row of `composition`, regardless of this variable's own
    missingness), n_available is how many of those actually have a non-missing value for THIS
    variable specifically. Never silently reports a stat computed over fewer subjects than
    stated without saying so - a sparse variable (education, NIHSS) must be read next to its own
    coverage, not mistaken for the cluster's full size."""
    values = composition[variable.name]
    n_total = len(composition)
    if variable.kind == "continuous":
        available = values.dropna()
        return {
            "n_available": int(available.size),
            "n_total": n_total,
            "mean": float(available.mean()) if available.size else None,
            "median": float(available.median()) if available.size else None,
            "std": float(available.std()) if available.size > 1 else None,
            "min": float(available.min()) if available.size else None,
            "max": float(available.max()) if available.size else None,
        }
    # categorical: an empty-string/NaN registry cell is "missing", not its own category.
    available = values[(values != "") & pd.notna(values)]
    counts = available.value_counts().to_dict()
    return {"n_available": int(available.size), "n_total": n_total, "counts": counts}


def build_cluster_description_figure(
    composition: pd.DataFrame, cluster_label: int, color: str | None = None
) -> go.Figure:
    """One Plotly figure, one subplot per CLUSTER_DESCRIPTION_VARIABLES entry - a box plot (with
    the individual subjects overlaid as points) for a continuous variable, a bar chart of counts
    for a categorical one.

    Laid out on a 3-column grid over as many rows as it takes (29-09-26 feedback: "così non si
    capisce niente, con label e assi così piccoli"). The 5 variables used to sit in a single
    row of 5, which at the app's 1100px page width left each subplot ~200px wide - too narrow
    for a readable axis, so every tick and title had to be tiny. Three per row roughly doubles
    that, which is what buys the larger type below; any unused trailing cell has its axes
    hidden rather than showing an empty framed box.

    color: the cluster's own color in the embedding scatter (plotting._palette_for_labels), used
    ONLY for a swatch in the title, never for the marks. The marks keep one fixed hue because
    inside this figure color already has a job - the categorical subplot encodes sex with the
    same _CATEGORICAL_PALETTE the scatter uses - and letting the box outlines also carry cluster
    identity would make one palette mean two different things in one figure. The title swatch is
    outside the plotting area, so it ties the panel to the scatter without competing.
    """
    variables = CLUSTER_DESCRIPTION_VARIABLES
    n_cols = min(_GRID_COLUMNS, len(variables))
    n_rows = math.ceil(len(variables) / n_cols)
    # The n=available/total line lives in the subplot TITLE, not the x-axis title. As an axis
    # title it sat lower under the one subplot that has tick labels (the categorical bar chart,
    # whose F/M labels push the title down) than under the box plots, which have none - five
    # coverage figures that are meant to be scanned together, on two different baselines.
    # In the title they align by construction.
    titles = []
    for variable in variables:
        summary = variable_summary(composition, variable)
        # Two <br> between the label and the n= line (02-10-26 feedback: "più spazio tra
        # titolo plot e n=") - a single <br> read as cramped at this font size, the label and
        # its coverage looked like one run-on line instead of two.
        titles.append(
            f'<b><span style="color:{variable.color}">{variable.label}</span></b><br><br>'
            f'<span style="font-size:13.5px;color:{_MUTED_COLOR}">'
            f"n={summary['n_available']}/{summary['n_total']}</span>"
        )
    fig = make_subplots(
        rows=n_rows, cols=n_cols, subplot_titles=titles,
        vertical_spacing=0.18, horizontal_spacing=0.09,
    )

    for index, variable in enumerate(variables):
        row, col = divmod(index, n_cols)
        row, col = row + 1, col + 1
        summary = variable_summary(composition, variable)
        if variable.kind == "continuous":
            available = composition[variable.name].dropna()
            fig.add_trace(
                go.Box(
                    y=available, name="", boxpoints="all", jitter=0.6, pointpos=0, boxmean=True,
                    marker=dict(color=_rgba(variable.color, _POINT_ALPHA), size=5, line=dict(width=0)),
                    line=dict(color=variable.color, width=2), fillcolor=_rgba(variable.color, _BOX_FILL_ALPHA),
                    showlegend=False, hovertemplate="%{y}<extra></extra>",
                ),
                row=row, col=col,
            )
            fig.update_xaxes(showticklabels=False, ticks="", row=row, col=col)
        else:
            categories = sorted(summary["counts"])
            counts = [summary["counts"][c] for c in categories]
            fig.add_trace(
                go.Bar(
                    x=categories, y=counts,
                    # Every bar direct-labeled: with 2-3 categories that is a handful of numbers,
                    # not the "a value on every point" clutter the rule warns about, and it is
                    # what keeps the counts readable without hovering (the bar fills sit below
                    # 3:1 against a white surface, so a visible label is required, not optional).
                    text=counts, textposition="outside", textfont=dict(size=14, color=_TEXT_COLOR),
                    cliponaxis=False,
                    # ONE color for every bar, this variable's own - not one per category.
                    # This is a single series, and the categories are already named by the tick
                    # labels and counted by the direct labels above them, so a per-category hue
                    # would re-encode what is already unambiguous. It would also make the same
                    # palette mean two different things in one figure ("which variable" in the
                    # box plots, "which category" here), which is the one thing the color rules
                    # are strictest about.
                    # Same pale-fill + 2px-outline treatment as the box plots, not a solid
                    # block: two saturated bars at this size read far heavier than the light
                    # boxes beside them, and a large saturated fill is exactly what the mark
                    # rules reserve saturation against (it belongs on small marks and accents).
                    marker=dict(
                        color=_rgba(variable.color, _BAR_FILL_ALPHA),
                        line=dict(color=variable.color, width=2),
                    ),
                    showlegend=False,
                    width=_BAR_WIDTH, hovertemplate="%{x}: %{y}<extra></extra>",
                ),
                row=row, col=col,
            )
            fig.update_xaxes(tickfont=dict(size=14), row=row, col=col)
            # Headroom so an "outside" label above the tallest bar isn't clipped by the subplot.
            fig.update_yaxes(range=[0, max(counts) * 1.18] if counts else None, row=row, col=col)

        fig.update_yaxes(tickfont=dict(size=13), gridcolor=_GRIDLINE_COLOR, zeroline=False, row=row, col=col)

    # Trailing empty cells of the last row: no frame, no ticks - an empty axis box reads as a
    # subplot whose data failed to load.
    for empty in range(len(variables), n_rows * n_cols):
        row, col = divmod(empty, n_cols)
        fig.update_xaxes(visible=False, row=row + 1, col=col + 1)
        fig.update_yaxes(visible=False, row=row + 1, col=col + 1)

    for annotation in fig.layout.annotations:  # the subplot titles make_subplots created
        annotation.font.update(size=17, color=_TEXT_COLOR, family=_FONT_STACK)
        # Pushed further above its own subplot (02-10-26 feedback: "più spazio tra queste due
        # cose e plot") - yshift is in pixels, applied after make_subplots' own title position,
        # so this only widens the gap to the plot below without moving the title's row/col.
        annotation.yshift = 8

    swatch = "" if color is None else f'<span style="color:{color}">■</span> '
    fig.update_layout(
        title=dict(
            # Bold, and pinned to the very top with a wide margin below it (29-09-26 feedback:
            # "distanza tra intestazione e plot maggiore, fai la scritta Cluster in grassetto").
            # y/yanchor keep the heading against the top edge so the extra top margin becomes a
            # gap under it, not padding above it.
            text=f"<b>{swatch}Cluster {cluster_label}</b> · {len(composition)} soggetti",
            font=dict(size=24, family=_FONT_STACK, color=_TEXT_COLOR),
            x=0.02, xanchor="left", y=0.975, yanchor="top",
        ),
        template="simple_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR),
        margin=dict(l=20, r=20, t=170, b=45), height=_ROW_HEIGHT * n_rows + 180,
    )
    return fig
