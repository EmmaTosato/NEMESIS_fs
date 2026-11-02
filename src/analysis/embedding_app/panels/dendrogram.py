"""The walk down an agglomerative run's tree: at each split, which subjects went left and
which went right, and what their brains look like.

Needs the tuning output the run came from (the linkage matrix is not saved with a production
run), which tuning_root_of/run_compatible_tunings locate; a run with no compatible tuning gets
the note saying so, never a silently empty tree.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import nibabel as nib
import numpy as np
import pandas as pd
from dash import Dash, Input, Output, dcc, html, no_update
from dash import dcc, html
from dash.exceptions import PreventUpdate
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.cluster_description import group_stats
from src.analysis.clustering_tuning_analysis import load_clustering_tuning_run
from src.analysis.dendrogram_splits import (
    SplitTree,
    build_split_tree,
    build_step_embedding_figure,
    build_tree_figure,
    replay_splits,
    saved_labels_for,
    single_label,
)
from src.analysis.embedding_app.blocks import _missing_subjects_warning
from src.analysis.embedding_app.embedding_view import _CLUSTER_LABEL_COLUMN, cluster_options
from src.analysis.embedding_app.panels.description import _stats_table
from src.analysis.embedding_app.panels.overview import _map_tile, _static_graph
from src.analysis.embedding_app.panels.quality import _require_narrow_matrix
from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import ProductionRun, run_metadata, run_params
from src.analysis.embedding_app.tabs import TAB_DENDROGRAM, tab_is_active
from src.analysis.plotting import _palette_for_labels
from src.analysis.tuning_match import TuningMatch, find_compatible_tunings
from src.utils.artifacts import load_matrix
from src.utils.number_format import format_number
from src.utils.participants import load_participants_registry


# --- Dendrogram and splits (21-10-26) --------------------------------------------------------

# Which map the two children of a split are drawn with: both exist for any run of this app (both viewer configs are
# always loaded), whatever modality the run itself is.
DENDROGRAM_MAP_MODALITIES = {"lesion": "Lesion", "sdc": "Disconnection"}


def tuning_root_of(run: ProductionRun) -> Path:
    """The folder holding the tuning runs of `run`'s method and modality: results/<modality>/clustering/tuning/<method>.
    Raises ValueError for a run that is not a clustering production run with a reduction segment in its path."""
    if run.pipeline != "clustering" or run.reduction_method is None:
        raise ValueError(f"{run.path} is not a clustering production run: it has no tuning to look for")
    # <results>/<modality>/clustering/production/<method>/<reduction>/<run_name>
    return run.path.parents[3] / "tuning" / run.method


def run_compatible_tunings(run: ProductionRun) -> list[TuningMatch]:
    """Every agglomerative tuning that clustered the same matrix as `run` (src.analysis.tuning_match), compatible or
    not. The `input_path`s of config.md are relative to the working directory the app is launched from. Raises
    ValueError for a run that is not agglomerative or whose params cannot be matched."""
    if run.method != "agglomerative":
        raise ValueError(f"{run.path}: the dendrogram is only defined for agglomerative runs, not {run.method!r}")
    return find_compatible_tunings(run.path, tuning_root_of(run), Path.cwd())


def build_run_split_tree(run: ProductionRun, tuning_dir: Path) -> SplitTree:
    """The tree of the matrix `run` clustered, with the labels `tuning_dir` saved for the run's (linkage, metric).
    Raises ValueError when the run's params lack them, when the matrix is not narrow enough to compute a tree on, or
    when the recomputed tree does not reproduce the tuning's labels (src.analysis.dendrogram_splits)."""
    _require_narrow_matrix(run)
    params = run_params(run)
    missing = [name for name in ("linkage", "metric") if name not in params]
    if missing:
        raise ValueError(f"{run.path}: params lack {missing}, the tree cannot be rebuilt")
    saved = saved_labels_for(load_clustering_tuning_run(tuning_dir), params["linkage"], params["metric"])
    matrix, metadata, _extra_arrays = load_matrix(run.path)
    run_labels = metadata[_CLUSTER_LABEL_COLUMN].to_numpy()
    return build_split_tree(
        matrix, params["linkage"], params["metric"], saved, run_labels, _palette_for_labels(cluster_options(metadata))
    )


def dendrogram_tuning_note(matches: list[TuningMatch]) -> html.Div:
    """Under the tuning picker: what the compatible ones are, and why each other candidate is not."""
    rejected = [match for match in matches if not match.compatible]
    children: list = []
    if not any(match.compatible for match in matches):
        children.append(
            html.P(
                "No compatible tuning: an agglomerative tuning on the same matrix is needed, with the "
                "labels saved (save_tuning_clusterings) for this run combination.",
                className="status-message",
            )
        )
    if rejected:
        children.append(html.P("Same matrix but not compatible:", className="anatomy-caption"))
        children.append(html.Ul([html.Li(f"{match.run_dir.name}: {match.reason_rejected}") for match in rejected]))
    return html.Div(children)


def dendrogram_k_options(tree: SplitTree) -> list[int]:
    """The k the tuning swept (up to the highest the palette can colour): the ones that can be picked."""
    return list(tree.saved_ks)


# build_view(run, metadata whose cluster_label is a cut of the tree, label of the cluster in that cut, modality, name of
# the cluster, map width) -> its anatomy view. The name (the leaves it holds) identifies the subjects of a cluster across
# the k, so the app caches by it: a cluster that survives several splits is built once.
DendrogramViewBuilder = Callable[
    [ProductionRun, pd.DataFrame, int, str, str, int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]
]

_STEP_PARENT_WIDTH = 640  # native width of the map of the cluster that splits, and of the two it gives (pixels)
_STEP_CHILD_WIDTH = 495


def _color_of(members: np.ndarray, leaf_color: np.ndarray, tree: SplitTree) -> str:
    """The colour (hex) of a group of subjects that is one whole cluster of the cut `leaf_color` belongs to."""
    return tree.palette[single_label(leaf_color[tree.leaf_of_subject], members, "group colour")]


def _dendrogram_map_tile(
    run: ProductionRun, metadata: pd.DataFrame, labels: np.ndarray, label: int, name: str, title: str, color: str,
    width: int, modality: str, build_view: DendrogramViewBuilder, large: bool,
) -> html.Div | html.P:
    """The map of one cluster of the cut `labels`; a cluster that cannot be drawn shows its own status message."""
    try:
        view, n_subjects, _img, missing = build_view(
            run, metadata.assign(**{_CLUSTER_LABEL_COLUMN: labels}), label, modality, name, width
        )
    except ValueError as exc:
        return html.P(f"{name}: {exc}", className="status-message")
    return _map_tile(view, f"{title} (n={n_subjects})", color, large=large, warning=_missing_subjects_warning(missing))


@dataclass(frozen=True)
class DendrogramStep:
    """What one screen of the walk down the tree shows. `parent` is the cluster that splits (as it was at k-1, labelled
    `parent_label` in the cut `parent_labels`) and `children` the two it gives; on the first screen there are no children
    and `parent` is the cluster that will split next. `leaf_color` are the colours of the leaves at `k`,
    `previous_leaf_color` those at k-1 (None on the first screen), `highlighted` the labels of the cut at k whose names
    are drawn bigger in the embedding."""

    head: str
    k: int
    leaf_color: np.ndarray
    previous_leaf_color: np.ndarray | None
    highlighted: set[int]
    note: str
    parent: dict
    parent_title: str
    parent_labels: np.ndarray
    parent_label: int
    children: list[dict]
    first: bool


def _subject_ids_of(metadata: pd.DataFrame, rows: np.ndarray) -> np.ndarray:
    """The subject ids of the given rows of a run's metadata (the rows of its matrix, which the tree's members index)."""
    return metadata["subject_id"].to_numpy()[rows]


def dendrogram_step_content_for(
    run: ProductionRun, metadata: pd.DataFrame, registry: pd.DataFrame, tree: SplitTree, embedding: np.ndarray,
    step: DendrogramStep, modality: str, build_view: DendrogramViewBuilder,
) -> html.Div:
    """One screen of the walk down the tree. On the left the tree and the embedding at `step.k`; on the right the map of
    the parent, under it the maps of its children side by side, under them a table describing those groups. Never
    raises into the callback: an embedding that cannot be drawn (not 2D) shows a status message in place of its figure,
    a cluster that cannot be mapped one in place of its map."""
    parent = step.parent
    try:
        embedding_figure: dcc.Graph | html.P = _static_graph(
            build_step_embedding_figure(
                embedding, tree.labels_by_k[step.k], step.leaf_color, tree.palette, tree.leaf_of_subject, step.highlighted,
                step.note
            )
        )
    except ValueError as exc:
        embedding_figure = html.P(str(exc), className="status-message")
    parent_color = _color_of(parent["members"], step.leaf_color if step.previous_leaf_color is None else step.previous_leaf_color, tree)
    groups = [(f"{step.parent_title} {parent['name']}", parent_color, parent["members"])]
    rows = [html.Div(
        _dendrogram_map_tile(
            run, metadata, step.parent_labels, step.parent_label, parent["name"], f"{step.parent_title}: {parent['name']}",
            parent_color, _STEP_PARENT_WIDTH, modality, build_view, large=True,
        ),
        className="dendrogram-step-row",
    )]
    if step.children:
        child_colors = [_color_of(child["members"], step.leaf_color, tree) for child in step.children]
        rows.append(html.Div(
            [
                _dendrogram_map_tile(
                    run, metadata, tree.labels_by_k[step.k], child["label"], child["name"], f"New: {child['name']}", color,
                    _STEP_CHILD_WIDTH, modality, build_view, large=True,
                )
                for child, color in zip(step.children, child_colors)
            ],
            className="dendrogram-step-row",
        ))
        groups += [(f"New {child['name']}", color, child["members"]) for child, color in zip(step.children, child_colors)]
    entries = [(name, color, group_stats(0, _subject_ids_of(metadata, members), registry), False) for name, color, members in groups]
    return html.Div(
        className="dendrogram-step first" if step.first else "dendrogram-step",
        children=[
            html.H3(step.head, className="dendrogram-step-title"),
            html.Div(
                className="dendrogram-step-body",
                children=[
                    html.Div([_static_graph(build_tree_figure(tree.Z, tree.layout, tree.members, step.leaf_color, tree.palette, step.k)), embedding_figure]),
                    html.Div(rows, className="dendrogram-step-maps"),
                ],
            ),
            html.Div(_stats_table(entries), className="stats-table-wrap dendrogram-step-table"),
        ],
    )


def dendrogram_steps_content_for(
    run: ProductionRun, metadata: pd.DataFrame, tree: SplitTree, embedding: np.ndarray, k: int, modality: str,
    build_view: DendrogramViewBuilder, registry: pd.DataFrame,
) -> html.Div | html.P:
    """The walk down the tree, from the tuning's smallest k to `k`, one screen each. The first shows that k's
    embedding and the one cluster that splits next; every later one shows the embedding with the split already done, the
    cluster that split (as it was at k-1) and the two it gave, with a table describing the three. `metadata` is the run's
    own: the labels the clusters are looked up by are the tree's cut at each k, not the run's `cluster_label`.
    `registry` is the participants registry indexed by subject_id. Raises ValueError for an unknown modality."""
    if modality not in DENDROGRAM_MAP_MODALITIES:
        raise ValueError(f"unknown map modality {modality!r} - known: {sorted(DENDROGRAM_MAP_MODALITIES)}")
    options = dendrogram_k_options(tree)
    if k not in options:
        return html.P(f"k={k} is not among those of the tuning (from {options[0]} to {options[-1]})", className="status-message")
    k0 = options[0]
    last = min(max(k, k0 + 1), tree.k_max)
    steps = {step_k: (colors, split) for step_k, colors, split in replay_splits(tree.Z, tree.labels_by_k, tree.leaf_of_subject, len(tree.members), last)}

    colors0, _ = steps[k0]
    if k0 + 1 in steps:
        following = steps[k0 + 1][1]["parent"]
        label = single_label(tree.labels_by_k[k0], following["members"], "parent")
        first = dendrogram_step_content_for(
            run, metadata, registry, tree, embedding,
            DendrogramStep(
                head=f"k={k0}: {k0} clusters. The next one to split is {following['name']} (n={following['n']})", k=k0,
                leaf_color=colors0, previous_leaf_color=None, highlighted={label}, note="in bold the one that will split",
                parent=following, parent_title="Will split", parent_labels=tree.labels_by_k[k0], parent_label=label,
                children=[], first=True,
            ),
            modality, build_view,
        )
    else:
        first = html.P(f"k={k0}: {k0} clusters, no further split in the tuning", className="status-message")
    screens = [first]

    for step_k in range(k0 + 1, k + 1):
        colors, split = steps[step_k]
        parent, (child_a, child_b) = split["parent"], split["children"]
        head = (
            f"k={step_k}: {parent['name']} (n={parent['n']}) split into {child_a['name']} (n={child_a['n']}) and "
            f"{child_b['name']} (n={child_b['n']}), merge distance {format_number(split['distance'], 1)}"
        )
        parent_label = single_label(tree.labels_by_k[step_k - 1], parent["members"], "parent")
        screens.append(dendrogram_step_content_for(
            run, metadata, registry, tree, embedding,
            DendrogramStep(
                head=head, k=step_k, leaf_color=colors, previous_leaf_color=steps[step_k - 1][0],
                highlighted={child_a["label"], child_b["label"]}, note="in bold the two born from the split",
                parent=parent, parent_title="Was", parent_labels=tree.labels_by_k[step_k - 1], parent_label=parent_label,
                children=[child_a, child_b], first=False,
            ),
            modality, build_view,
        ))
    return html.Div(screens, className="dendrogram-steps wide-block")


if TYPE_CHECKING:  # importing it for real would close a loop through the panels
    from src.analysis.embedding_app.context import AppContext


def register_callbacks(app: Dash, context: AppContext) -> None:
    """Wires this panel to the app. Called once by build_app, which owns the layout the ids
    below refer to."""
    def _chosen_tuning_dir(run: ProductionRun, tuning_value: str | None) -> Path:
        """The compatible tuning picked in the panel. PreventUpdate for a value that is not one of this run's compatible
        tunings: the callbacks of the panel also fire with the value left over from the previously chosen run."""
        if tuning_value is None:
            raise PreventUpdate
        try:
            compatible = {str(match.run_dir) for match in context.compatible_tunings(run) if match.compatible}
        except ValueError:
            raise PreventUpdate
        if tuning_value not in compatible:
            raise PreventUpdate
        return Path(tuning_value)

    def _is_agglomerative(run: ProductionRun) -> bool:
        return run.pipeline == "clustering" and run.method == "agglomerative"

    @app.callback(
        Output("dendrogram-panel", "style"),
        Output("dendrogram-tuning-picker", "options"),
        Output("dendrogram-tuning-picker", "value"),
        Output("dendrogram-tuning-note", "children"),
        Output("dendrogram-map-picker", "value"),
        Input("run-picker", "value"),
    )
    def _update_dendrogram_panel(run_key: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        if not _is_agglomerative(run):
            return {"display": "none"}, [], None, [], no_update
        default_map = "lesion"
        try:
            matches = context.compatible_tunings(run)
        except ValueError as exc:
            return {}, [], None, html.P(str(exc), className="status-message"), default_map
        options = [{"label": match.run_dir.name, "value": str(match.run_dir)} for match in matches if match.compatible]
        return {}, options, (options[0]["value"] if options else None), dendrogram_tuning_note(matches), default_map

    @app.callback(
        Output("dendrogram-k-picker", "options"),
        Output("dendrogram-k-picker", "value"),
        Input("run-picker", "value"),
        Input("dendrogram-tuning-picker", "value"),
    )
    def _update_dendrogram_k(run_key: str | None, tuning_value: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        if not _is_agglomerative(run):
            raise PreventUpdate
        tuning_dir = _chosen_tuning_dir(run, tuning_value)
        try:
            tree = context.split_tree(run, tuning_dir)
        except ValueError:
            return [], None  # the figure callback shows why
        k_values = dendrogram_k_options(tree)
        production_k = run_params(run)["n_clusters"]
        # The production k, or the nearest one the tuning swept (a sweep can have holes: 2..6, 8, 10).
        return [{"label": str(k), "value": k} for k in k_values], min(k_values, key=lambda k: abs(k - production_k))

    def _dendrogram_context(run_key: str | None, tuning_value: str | None, k: int | None, modality: str | None):
        """(run, tuning dir, tree) the two callbacks below work on, or a status message in their place when the tree
        cannot be built. PreventUpdate while the pickers still hold values of the previously chosen run."""
        if run_key in (None, UNSET) or k is None or modality is None:
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        if not _is_agglomerative(run):
            raise PreventUpdate
        tuning_dir = _chosen_tuning_dir(run, tuning_value)
        try:
            tree = context.split_tree(run, tuning_dir)
        except ValueError as exc:
            return html.P(str(exc), className="status-message")
        if k not in dendrogram_k_options(tree):
            raise PreventUpdate  # the k left over from the previous tuning, until the k picker is refilled
        return run, tuning_dir, tree

    def _dendrogram_build_view(tuning_dir: Path) -> DendrogramViewBuilder:
        return lambda run_, metadata_at_k, label, modality_, name, width: context.dendrogram_view(
            run_, metadata_at_k, label, modality_, name, width, tuning_dir
        )

    @app.callback(
        Output("dendrogram-steps-content", "children"),
        Input("run-picker", "value"),
        Input("dendrogram-tuning-picker", "value"),
        Input("dendrogram-k-picker", "value"),
        Input("dendrogram-map-picker", "value"),
        Input("selected-page-tab", "data"),
    )
    def _update_dendrogram_steps(
        run_key: str | None, tuning_value: str | None, k: int | None, modality: str | None, selected_tab: str | None
    ):
        if run_key not in (None, UNSET) and not tab_is_active(context.runs_by_key[run_key], selected_tab, TAB_DENDROGRAM):
            return []
        chosen = _dendrogram_context(run_key, tuning_value, k, modality)
        if isinstance(chosen, html.P):
            return chosen
        run, tuning_dir, tree = chosen
        embedding, embedding_message = context.embedding(run)
        if embedding is None:
            return html.P(embedding_message, className="status-message")
        return dendrogram_steps_content_for(
            run, run_metadata(run), tree, embedding, k, modality, _dendrogram_build_view(tuning_dir),
            load_participants_registry().set_index("subject_id"),
        )

def layout() -> html.Div:
    """The panel as it sits in the page. build_app places it; the callbacks above fill it."""
    return html.Div(
        id="dendrogram-panel",
        className="section-divider",
        style={"display": "none"},
        children=[
            html.H2("Dendrogram Explorer", className="section-title"),
            html.P(
                "Going from k-1 to k clusters, one cluster splits in two. Choose a k: the tree is walked from the "
                "smallest k up to that k. Each step shows the tree and the embedding, the anatomy of the cluster "
                "that splits and of the two it gives, and a table describing them. The labels for each k come from "
                "a tuning compatible with this run.",
                className="section-intro",
            ),
            html.Div(
                className="cluster-chooser cluster-chooser-wide",
                children=[
                    html.Label("Compatible tuning", className="picker-label"),
                    dcc.Dropdown(id="dendrogram-tuning-picker", clearable=False),
                ],
            ),
            html.Div(id="dendrogram-tuning-note"),
            html.Div(
                className="cluster-chooser",
                children=[
                    html.Label("k", className="picker-label"),
                    dcc.Dropdown(id="dendrogram-k-picker", clearable=False),
                ],
            ),
            html.Div(
                className="cluster-chooser",
                children=[
                    html.Label("Map", className="picker-label"),
                    dcc.Dropdown(
                        id="dendrogram-map-picker", clearable=False, value="lesion",
                        options=[{"label": label, "value": value} for value, label in DENDROGRAM_MAP_MODALITIES.items()],
                    ),
                ],
            ),
            html.H2("Agglomerative decomposed", className="dendrogram-steps-title"),
            dcc.Loading(html.Div(id="dendrogram-steps-content")),
        ],
    )
