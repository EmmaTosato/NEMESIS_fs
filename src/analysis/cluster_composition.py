"""Composition of every cluster of a clustering run, side by side - feeds the "Composizione dei
cluster" panel in src/analysis/embedding_app.py.

Where cluster_description.py describes one chosen cluster, this module compares all of them: for
each variable, one plot with a bar or box per cluster. Categorical variables (dataset, lesion
side, dominant lesion location) are 100%-stacked bars, so clusters of different sizes are
comparable; continuous ones (NIHSS, lesion volume, disconnection load) are box plots per cluster.

Every variable is read from assets/metadata/participants.csv, never from a run's own metadata.csv,
for the same reasons as in cluster_description.py (docs/dev/cluster_description.md).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import pandas as pd
import plotly.graph_objects as go

from src.analysis.embedding_coloring import COLOR_MODES
from src.analysis.plotting import _palette_for_categories, _palette_for_labels
from src.utils.participants import load_participants_registry, participants_registry_path

_CLUSTER_LABEL_COLUMN = COLOR_MODES["cluster_label"].column

_TEXT_COLOR = "#333"
_MUTED_COLOR = "#767676"
_GRIDLINE_COLOR = "#ececec"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)
_BOX_FILL_ALPHA = 0.25
_FIGURE_HEIGHT = 400

VariableKind = Literal["continuous", "categorical"]


@dataclass(frozen=True)
class CompositionVariable:
    """category_order fixes the order (and colors) of a closed categorical vocabulary; None sorts
    the categories found. log_scale draws a continuous variable on a log axis, for a quantity
    spanning orders of magnitude (lesion volume) that a linear axis would squash."""

    name: str
    label: str
    kind: VariableKind
    registry_column: str
    category_order: tuple[str, ...] | None = None
    log_scale: bool = False


COMPOSITION_VARIABLES: list[CompositionVariable] = [
    CompositionVariable("dataset", "Dataset", "categorical", "dataset"),
    CompositionVariable("lesion_side", "Lato della lesione", "categorical", "lesion_side", category_order=("left", "right", "both")),
    CompositionVariable("location_dominant", "Localizzazione dominante della lesione", "categorical", "location_dominant_2mm"),
    CompositionVariable("nihss", "NIHSS", "continuous", "NIHSS"),
    CompositionVariable("lesion_volume", "Volume della lesione (voxel, 2mm)", "continuous", "lesion_volume_voxels_2mm", log_scale=True),
    CompositionVariable("disconnection_load", "Carico di disconnessione (voxel, 2mm)", "continuous", "disconnection_load_voxels_2mm"),
]


def composition_frame(metadata: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """(frame, unregistered): one row per subject of `metadata` with its cluster_label and every
    COMPOSITION_VARIABLES entry read from the subject registry. `unregistered` lists, sorted, the
    subjects with no registry row; they stay in the frame with missing values, so each variable's
    n_total is the run's true size, and a warning is logged.

    Raises ValueError if `metadata` has no cluster labels (not a clustering run) or the registry
    lacks a column a variable needs (it is written by populate_metadata.py/enrich_metadata.py)."""
    if _CLUSTER_LABEL_COLUMN not in metadata.columns:
        raise ValueError(f"this run's metadata has no {_CLUSTER_LABEL_COLUMN!r} column - not a clustering run")

    registry = load_participants_registry().set_index("subject_id")
    missing_columns = [v.registry_column for v in COMPOSITION_VARIABLES if v.registry_column not in registry.columns]
    if missing_columns:
        raise ValueError(
            f"{participants_registry_path()} has no column(s) {missing_columns} - "
            "run src/pipeline/enrich_metadata.py to populate them (docs/dev/metadata.md)"
        )

    subject_ids = metadata["subject_id"].to_numpy()
    unregistered = sorted(set(subject_ids) - set(registry.index))
    if unregistered:
        logging.warning(
            "%d/%d subject(s) have no row in %s - kept with missing values: %s",
            len(unregistered), len(subject_ids), participants_registry_path(), unregistered,
        )
    aligned = registry.reindex(subject_ids)

    frame = pd.DataFrame({"subject_id": subject_ids, _CLUSTER_LABEL_COLUMN: metadata[_CLUSTER_LABEL_COLUMN].to_numpy()})
    for variable in COMPOSITION_VARIABLES:
        raw = aligned[variable.registry_column].to_numpy()
        frame[variable.name] = pd.to_numeric(raw, errors="coerce") if variable.kind == "continuous" else raw
    return frame, unregistered


def cluster_colors(frame: pd.DataFrame) -> dict[int, str]:
    """Color of each cluster, the same one the embedding scatter gives it."""
    return _palette_for_labels(sorted(int(label) for label in pd.unique(frame[_CLUSTER_LABEL_COLUMN])))


def build_composition_figure(frame: pd.DataFrame, variable: CompositionVariable) -> go.Figure:
    """One Plotly figure for `variable` across every cluster of `frame` (composition_frame's output).

    Categorical: horizontal bars, one per cluster, each summing to 100% and split by category -
    percentages, so a cluster of 50 and one of 500 are readable on the same scale. Continuous: one
    box per cluster, in that cluster's scatter color. Subjects with a missing value are left out,
    and the subtitle says how many that leaves ("n=1500/1570"), so a sparse variable is never read
    as if it covered everyone."""
    labels = sorted(int(label) for label in pd.unique(frame[_CLUSTER_LABEL_COLUMN]))
    values = frame[variable.name]
    if variable.kind == "continuous":
        n_available = int(values.notna().sum())
    else:
        n_available = int((values.notna() & (values != "")).sum())
    title = (
        f'<b>{variable.label}</b><br><span style="font-size:13.5px;color:{_MUTED_COLOR}">'
        f"n={n_available}/{len(frame)}</span>"
    )

    fig = go.Figure()
    if variable.kind == "continuous":
        colors = cluster_colors(frame)
        for label in labels:
            cluster_values = frame.loc[frame[_CLUSTER_LABEL_COLUMN] == label, variable.name].dropna()
            fig.add_trace(go.Box(
                y=cluster_values, name=str(label), boxpoints="outliers", boxmean=True,
                marker=dict(color=colors[label], size=4, opacity=0.5),
                line=dict(color=colors[label], width=2), fillcolor=_rgba(colors[label], _BOX_FILL_ALPHA),
                showlegend=False, hovertemplate="%{y}<extra></extra>",
            ))
        fig.update_xaxes(title_text="cluster", type="category")
        fig.update_yaxes(type="log" if variable.log_scale else "linear")
    else:
        present = frame.loc[values.notna() & (values != ""), [_CLUSTER_LABEL_COLUMN, variable.name]]
        categories = (
            list(variable.category_order) if variable.category_order is not None else sorted(present[variable.name].unique())
        )
        unexpected = sorted(set(present[variable.name]) - set(categories))
        if unexpected:
            raise ValueError(f"{variable.name}: value(s) {unexpected} are outside the closed category list {categories}")
        palette = _palette_for_categories(categories, category_order=variable.category_order)
        counts = pd.crosstab(present[_CLUSTER_LABEL_COLUMN], present[variable.name]).reindex(index=labels, columns=categories, fill_value=0)
        # barnorm="percent" makes Plotly's %{x} the percentage, not the count, so the hover reads
        # both from customdata: the count (what "soggetti" means) and the share of the cluster.
        shares = counts.div(counts.sum(axis=1), axis=0).fillna(0.0) * 100
        for category in categories:
            fig.add_trace(go.Bar(
                y=[str(label) for label in labels], x=counts[category], name=category, orientation="h",
                customdata=list(zip(counts[category], shares[category])),
                marker=dict(color=palette[category], line=dict(color="white", width=1)),
                hovertemplate=(
                    "cluster %{y}<br>" + category + ": %{customdata[0]} soggetti (%{customdata[1]:.1f}% del cluster)<extra></extra>"
                ),
            ))
        fig.update_layout(barmode="stack", barnorm="percent", legend=dict(orientation="h", y=-0.38, x=0))
        fig.update_xaxes(title_text="% del cluster", range=[0, 100])
        fig.update_yaxes(title_text="cluster", type="category", autorange="reversed")

    fig.update_xaxes(gridcolor=_GRIDLINE_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=_GRIDLINE_COLOR, zeroline=False)
    fig.update_layout(
        title=dict(text=title, font=dict(size=17, family=_FONT_STACK, color=_TEXT_COLOR), x=0.02, xanchor="left"),
        template="simple_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR), margin=dict(l=50, r=20, t=90, b=70 if variable.kind == "continuous" else 120), height=_FIGURE_HEIGHT,
    )
    return fig


def _rgba(hex_color: str, alpha: float) -> str:
    if not (len(hex_color) == 7 and hex_color.startswith("#")):
        raise ValueError(f"expected a '#rrggbb' color, got {hex_color!r}")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"
