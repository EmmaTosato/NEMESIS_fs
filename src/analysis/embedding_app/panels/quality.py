"""How good the clustering is, read from the run itself: silhouette, density, the ADP
indices, and what the method's own saved model says.

Every index comes with the sentence that says what it measures and what it cannot say; the
slow ones (a distance matrix of thousands of subjects) are computed in a background thread and
polled, never in the click.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from dash import Dash, Input, Output
from dash import dcc, html
from dash.exceptions import PreventUpdate

from src.analysis.cluster_quality import build_dbcv_figure, build_mean_membership_figure, build_silhouette_figure
from src.analysis.clustering_evaluation import (
    AdpSummary,
    SilhouetteBreakdown,
    SoftMembership,
    adp_summary,
    per_cluster_silhouette,
    require_applicable,
    run_metric,
    soft_membership_summary,
)
from src.analysis.embedding_app.blocks import _table
from src.analysis.embedding_app.picker import UNSET
from src.analysis.embedding_app.runs import ProductionRun, _matrix_shape, run_metadata, run_params
from src.analysis.embedding_app.style import _italian_figure
from src.analysis.embedding_app.tabs import TAB_CLUSTERING, tab_is_active
from src.analysis.production_results import RESULTS_METHODS, SavedResults, read_production_results
from src.analysis.raw_distances import RawDistanceStore
from src.utils.artifacts import MATRIX_FILENAME, load_matrix
from src.utils.number_format import format_number


# --- Clustering quality (16-10-26) ----------------------------------------------------------------

# The silhouette of every subject reads every pair of subjects, so its cost grows with the number of columns:
# about a second for 5845 subjects x 10 components, minutes for the 221955 voxels of a raw lesion matrix.
# Past this many columns the panel does not draw it (the notebook reads such a run memory-mapped).
MAX_QUALITY_COLUMNS = 1000


def _require_narrow_matrix(run: ProductionRun) -> None:
    """Raises ValueError if the matrix `run` was clustered on has more than MAX_QUALITY_COLUMNS columns."""
    n_columns = _matrix_shape(run)[1]
    if n_columns > MAX_QUALITY_COLUMNS:
        raise ValueError(
            f"the run was computed on {n_columns} columns (raw data, not an embedding): not drawn here "
            f"beyond {MAX_QUALITY_COLUMNS} columns (read the indices of the tuning: tuning_results.csv and report.md)"
        )


def run_production_results(run: ProductionRun) -> SavedResults:
    """The numbers the production run saved (production_results.csv and production_results_per_cluster.csv): the panel
    shows them, it does not compute them again. Raises FileNotFoundError for a run without the files and ValueError
    for files that are not the method's (read_production_results)."""
    return read_production_results(run.path, run.method)


def run_distance_metric(run: ProductionRun) -> str:
    """The distance the run was clustered with (the one its silhouette is measured in)."""
    return run_metric(run_params(run))


def run_silhouette_samples(run: ProductionRun) -> SilhouetteBreakdown:
    """The silhouette of every subject of a clustering run, on the matrix it was clustered on (matrix.npy) and in the
    run's own distance: the one thing the saved tables do not hold, because it has a value per subject.

    Raises ValueError, with the cause, for a matrix with more than MAX_QUALITY_COLUMNS columns or a run the silhouette
    is not defined for (fewer than 2 clusters, a non-Euclidean affinity)."""
    _require_narrow_matrix(run)
    matrix, metadata, _extra_arrays = load_matrix(run.path)
    return per_cluster_silhouette(matrix, metadata["cluster_label"].to_numpy(), run_params(run))


def run_soft_membership(run: ProductionRun) -> SoftMembership:
    """The soft clustering of a hdbscan_soft run: the per-cluster summary with the mean
    membership vectors. Read from the membership.npy the run saved, no refit. Raises ValueError, with the
    cause, for another method or a run without membership.npy."""
    require_applicable("soft_membership", run.method)
    _matrix, metadata, extra_arrays = load_matrix(run.path, mmap=True)  # only the labels and membership are wanted
    if "membership" not in extra_arrays:
        raise ValueError("the run has no membership.npy: it is not an hdbscan_soft production run")
    return soft_membership_summary(metadata["cluster_label"].to_numpy(), extra_arrays["membership"])


# How often the panel looks again at a background computation (milliseconds).
_QUALITY_POLL_MS = 5000

# Neighbours counted by the purity of an adp run.
ADP_K_NEIGHBORS = 10


def run_adp_summary(run: ProductionRun, store: RawDistanceStore) -> AdpSummary | None:
    """k-neighbour purity and silhouette on the dice distance of an adp run, or None while the distance
    matrix is still being computed in the background (RawDistanceStore.request).

    Reads the run's own matrix.npy (what adp clustered: the matrix may have been rebuilt since, the
    run keeps its copy) memory-mapped, and only metadata.csv for the subjects and labels. Raises
    ValueError for a run that is not adp, or whatever adp_summary refuses."""
    require_applicable("knn_purity", run.method)
    metadata = run_metadata(run)
    distances = store.request(run.path / MATRIX_FILENAME, metadata["subject_id"].tolist(), run_params(run)["metric"])
    if distances is None:
        return None
    return adp_summary(distances.distances, distances.non_empty, metadata["cluster_label"].to_numpy(), ADP_K_NEIGHBORS)


def _guide(title: str, points: list[tuple[str, str]], limits: list[str] | None = None) -> html.Details:
    """A collapsed explanation under a panel's heading: one bullet per idea ("Name: sentence"), then, if any,
    the limits of the reading, one bullet each."""
    children: list = [
        html.Summary(title),
        html.Ul([html.Li([html.B(f"{name}: "), text]) for name, text in points], className="comparison-points"),
    ]
    if limits:
        children += [
            html.P("Limits", className="comparison-subheading"),
            html.Ul([html.Li(limit) for limit in limits], className="comparison-points"),
        ]
    return html.Details(className="comparison-guide", children=children)


def _adp_guide() -> html.Details:
    """How to read the adp indices (the adp indices)."""
    return _guide(
        "How to read these indices",
        [
            ("Neighbor purity", (
                f"for each subject, the share of its {ADP_K_NEIGHBORS} nearest neighbors (dice distance, the one adp used to "
                "cluster) that lies in its own cluster. From 0 to 1; near 1 the neighbors almost always lie in its "
                "cluster. Read it next to the value expected by chance, (cluster n - 1) / (total n - 1)"
            )),
            ("Small clusters", (
                f"a cluster with {ADP_K_NEIGHBORS} subjects or fewer cannot reach 1: it stays in the table but is left out of the summary"
            )),
            ("Pairs at distance 1", (
                "share of subject pairs with no voxel in common, to be looked at before the silhouette. If it is high "
                "(lesions: 84%) almost all distances equal 1 and the silhouette stays near 0 whatever the structure: "
                "use the purity. If it is low (voxelwise disconnectome: 0.0015%) the silhouette is read as for the other methods"
            )),
            ("Share with ties", (
                "subjects whose last counted neighbor has the same distance as the next one; for them the purity is the value "
                "expected when choosing at random among the ties"
            )),
        ],
        [
            "Purity is partly circular: adp forms the clusters on exactly these neighbors. A high purity says the clusters are coherent, not that they are \"true\".",
            "The silhouette is on the dice distance: it is not comparable with the Euclidean one of the runs on embeddings.",
            "Noise (-1) and the subjects with an all-zero matrix (dice distance undefined, adp labels them -1) are excluded.",
        ],
    )


def adp_quality_content_for(
    run: ProductionRun, summary_of: Callable[[ProductionRun], AdpSummary | None]
) -> tuple[html.Div | html.P, bool]:
    """(content, pending) of the "Valutazione del clustering" panel for an adp run: the k-neighbour purity,
    the silhouette on the dice distance and the share of pairs at distance 1, with a per-cluster table.
    `pending` is True while the distance matrix is still being computed: the content then says so and
    the caller keeps polling. Same never-raises contract as the other *_content_for functions."""
    try:
        summary = summary_of(run)
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message"), False
    if summary is None:
        return html.P(
            "Computing the dice distance matrix between the subjects (about 4 minutes for lesions, "
            "up to about 25 for the voxelwise disconnectome). It is saved to disk: next time it is instant. "
            "The page updates by itself.",
            className="status-message",
        ), True

    def share(value: float) -> str:
        return f"{format_number(value * 100, 1)}%"

    purity, silhouette = summary.purity, summary.silhouette
    rows = [
        [f"Purity of the {summary.k} neighbors", format_number(purity.purity, 3), "higher is better, from 0 to 1"],
        ["Purity expected by chance", format_number(purity.chance, 3), "to be read next to the purity"],
        ["Dice silhouette (mean over subjects)", format_number(silhouette.micro, 3), "higher is better, from -1 to 1"],
        ["Pairs at distance 1", share(summary.pairs_at_distance_1), "if it is high the silhouette is not informative"],
        ["Clusters (noise excluded)", str(len(purity.clusters)), ""],
        ["Noise", share(summary.noise_fraction), "of the subjects"],
        [f"Subjects in clusters of {summary.k} or fewer", str(purity.n_not_evaluable), "left out of the purity summary"],
        ["Share with ties", share(purity.tied_share), "subjects with neighbors at equal distance"],
    ]
    cluster_rows = [
        [
            str(label), str(int(row.n)), format_number(row.purity, 3), format_number(row.chance, 3),
            "yes" if row.evaluable else "no", format_number(row.silhouette_mean, 3), share(row.share_negative),
        ]
        for label, row in summary.clusters.iterrows()
    ]
    children: list = [_adp_guide()]
    children += [
        html.P(
            f"Computed on the dice distance of the raw data, the one adp clustered with, on {summary.n_clustered} "
            f"clustered subjects out of {summary.n_subjects}.",
            className="quality-intro",
        ),
        _table(["Index", "Value", "Reading"], rows, text_columns=(0, 2)),
        html.P("Per cluster", className="comparison-subheading"),
        _table(
            ["Cluster", "Subjects", "Purity", "Expected by chance", "Evaluable", "Mean silhouette", "Negative silhouette"],
            cluster_rows, text_columns=(0,),
        ),
        _chart_heading("Silhouette per cluster", "one panel per cluster, noise excluded"),
        dcc.Graph(
            figure=_italian_figure(build_silhouette_figure(summary.silhouette.subject_labels, summary.silhouette.subject_values)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        ),
    ]
    return html.Div(children), False


def _quality_guide() -> html.Details:
    """How to read the geometric indices (the geometric indices)."""
    return _guide(
        "How to read these indices",
        [
            ("Silhouette", (
                "for each subject, compares the mean distance from its own cluster with that from the nearest cluster. "
                "From -1 to 1, higher is better: near 1 the clusters are sharp, near 0 the boundaries are ambiguous, "
                "negative the subject is in the wrong cluster"
            )),
            ("Calinski-Harabasz", "dispersion between clusters divided by that within clusters. Higher is better"),
            ("Davies-Bouldin", "for each cluster, similarity to the most similar cluster. Lower is better, 0 = compact and separated clusters"),
            ("Dunn", "minimum distance between clusters divided by the maximum diameter of a cluster. Higher is better, it is sensitive to outliers"),
            ("Plot per cluster", (
                "one panel per cluster with the silhouette of each subject, highest at the top: it shows which clusters have "
                "ambiguous boundaries even if the overall mean is good (how many subjects are below zero, how homogeneous "
                "the cluster is). The panel height follows the cluster size, with a minimum so that a small cluster "
                "stays readable; a one-subject cluster has silhouette 0 by convention. The red line is the mean over the "
                "subjects. Hovering over a point shows the cluster, its size and the silhouette of that subject"
            )),
        ],
        [
            "None of the four indices has a reference value.",
            "A cloud with no clusters, split by an algorithm, still has a positive silhouette (ward, 3 clusters, "
            "2-component Gaussian cloud: about 0.4): the value alone does not say whether there is structure.",
            "Calinski-Harabasz, Davies-Bouldin and Dunn of a single run have no scale.",
            "Different embeddings (2 or 10 components, lesion or sdc) are not comparable with each other.",
        ],
    )


def _soft_membership_block(
    run: ProductionRun, soft_of: Callable[[ProductionRun], SoftMembership]
) -> html.Div:
    """Section 3.2 for a hdbscan_soft run: per cluster table and mean membership vectors."""
    heading = html.P("Cluster membership (soft clustering)", className="comparison-subheading")
    try:
        summary = soft_of(run)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])

    def other(value) -> str:
        return "—" if pd.isna(value) else str(int(value))

    cluster_rows = [
        [
            str(label), str(int(row.n)), format_number(row.own_mean, 3),
            other(row.top_other), format_number(row.top_other_mean, 3) if pd.notna(row.top_other_mean) else "—",
        ]
        for label, row in summary.clusters.iterrows()
    ]
    return html.Div([
        heading,
        _guide(
            "How to read these tables",
            [
                ("Rows", "do not sum to 1: the rest is the probability of being noise"),
                ("Heatmap", "diagonal = mean probability in the own cluster; off-diagonal = clusters that overlap"),
            ],
            [
                "It depends on the density of the clustered space: on UMAP with min_dist = 0 it also measures how tightly UMAP packed the groups.",
                "There is no reference value for a probability: the tables report means, with no threshold.",
            ],
        ),
        html.P(f"{summary.n_noise} noise subjects: they have no cluster of their own, and have a separate row in the matrix.", className="quality-intro"),
        _table(
            ["Cluster", "Subjects", "Mean probability in own", "Most likely other cluster", "Mean probability in the other"],
            cluster_rows, text_columns=(0,),
        ),
        _chart_heading("Mean membership vectors", "rows: subjects cluster; columns: membership cluster"),
        dcc.Graph(
            figure=_italian_figure(build_mean_membership_figure(summary.mean_vectors)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        ),
    ])


def _density_guide(soft: bool) -> html.Details:
    """How to read DBCV, the probability of a subject in its cluster and (hdbscan_soft) the persistence of a cluster, and
    why the silhouette-family indices are not shown for hdbscan / hdbscan_soft."""
    points = [
        ("DBCV", (
            "density-based cluster validity (Moulavi et al. 2014). For each cluster it compares how sparse the cluster is "
            "inside with how far it is from the nearest cluster. From -1 to 1, higher is better"
        )),
        ("The run's score", (
            "the average of the clusters' own scores, each weighted by its share of all the subjects, noise included: "
            "the noise lowers the score by itself, so a clustering that throws the hard subjects away is not rewarded"
        )),
        ("Plot per cluster", "one bar per cluster with its own score and size; the dashed line is the run's score, which is not the mean of the bars"),
        ("Probability", (
            "from 0 to 1, within the cluster: near 1 the subject is at the core, near 0 at the margin. It is not the probability "
            "of being in this cluster rather than another, nor comparable across clusters of different density"
        )),
    ]
    if soft:
        points.append((
            "Persistence",
            "from 0 to 1 for each cluster: 1 is a cluster that lasts over all the distance scales of the tree, 0 one that vanishes at once",
        ))
    return _guide(
        "How to read DBCV",
        points,
        [
            "Silhouette, Calinski-Harabasz, Davies-Bouldin and Dunn are not computed for these methods: they use the non-noise subjects only "
            "(the hardest ones, thrown into the noise, make them rise) and assume compact clusters.",
            "DBCV has no reference value, and it is not comparable across different embeddings.",
            "It is undefined with fewer than 2 clusters.",
            "The probability depends on the density of the clustered space: on UMAP with min_dist = 0 it tells how tightly UMAP packed "
            "the cluster, not that it is real. There is no reference value for a probability"
            + (" or a persistence" if soft else "") + ": the tables report means, with no threshold.",
        ],
    )


def _saved_row(label: str, saved: SavedResults, name: str, decimals: int, reading: str, percent: bool = False) -> list[str]:
    """[label, value, reading] of a metric a run saved. A metric that is not defined for the run is a dash and the reason
    saved with it (its note)."""
    value = saved.values[name]
    if np.isnan(value):
        return [label, "—", saved.notes[name]]
    return [label, f"{format_number(value * 100, 1)}%" if percent else format_number(value, decimals), reading]


def _cell(value: float, decimals: int) -> str:
    """A number of a per-cluster table, a dash where the run saved none."""
    return "—" if pd.isna(value) else format_number(value, decimals)


def _share_cell(value: float) -> str:
    return "—" if pd.isna(value) else f"{format_number(value * 100, 1)}%"


def _tree_block(saved: SavedResults, n_clusters: int) -> html.Div:
    """The "Model statistic" block of an agglomerative run: the cophenetic correlation and the dendrogram jump it saved."""
    rows = [
        _saved_row("Cophenetic correlation", saved, "cophenetic_correlation", 3, ""),
        _saved_row(f"Dendrogram jump (k={n_clusters})", saved, "dendrogram_jump", 2, ""),
    ]
    return html.Div([
        html.P("Model statistic", className="comparison-subheading"),
        # the third column only says why a statistic is not defined: no column when every one is
        _table(["Statistic", "Value", "Reading"], rows, text_columns=(0, 2))
        if any(row[2] for row in rows)
        else _table(["Statistic", "Value"], [row[:2] for row in rows], text_columns=(0,)),
        html.P(
            "Cophenetic correlation: how faithfully the tree reflects the real distances between subjects. From -1 to 1: "
            "the higher, the better the tree reproduces them. It is measured with the run's own distance, so it is not "
            "comparable between runs with a different metric.",
            className="comparison-note centered",
        ),
        html.P(
            "Dendrogram jump (at the run's k): how sharp the cut at k is. It is the height of the merge that takes the tree "
            "from k to k-1 clusters divided by the height of the merge from k+1 to k. Near 1 the tree has no clear gap at k; "
            "the higher, the sharper the cut. Heights are in the units of each linkage, so it is not comparable between linkages.",
            className="comparison-note centered",
        ),
    ])


def _agglomerative_quality_content(
    run: ProductionRun,
    saved: SavedResults,
    metric: str,
    silhouette_of: Callable[[ProductionRun], SilhouetteBreakdown],
) -> html.Div:
    """The panel of an agglomerative run: the indices and the tree statistics it saved, its table per cluster, and the
    silhouette of every subject (the one part computed here, `silhouette_of`; a run it cannot be drawn for says why)."""
    clusters = saved.per_cluster
    n_clusters = len(clusters)
    rows = [
        _saved_row("Silhouette (mean over subjects)", saved, "silhouette", 3, "higher is better, from -1 to 1"),
        _saved_row("Calinski-Harabasz", saved, "calinski_harabasz", 1, "higher is better"),
        _saved_row("Davies-Bouldin", saved, "davies_bouldin", 3, "lower is better"),
        _saved_row("Dunn", saved, "dunn", 4, "higher is better"),
        ["Clusters", str(n_clusters), ""],
        _saved_row("Largest cluster", saved, "largest_cluster_share", 1, "of the subjects", percent=True),
    ]
    cluster_rows = [
        [str(int(row.cluster)), str(int(row.n)), _cell(row.silhouette_mean, 3), _share_cell(row.share_negative)]
        for row in clusters.itertuples()
    ]
    try:
        breakdown = silhouette_of(run)
    except (ValueError, OSError) as exc:
        silhouette_chart: list = [html.P(str(exc), className="status-message")]
    else:
        silhouette_chart = [dcc.Graph(
            figure=_italian_figure(build_silhouette_figure(breakdown.subject_labels, breakdown.subject_values)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        )]
    return html.Div([
        _quality_guide(),
        html.P(
            f"{int(clusters['n'].sum())} subjects, as the production run saved them (production_results.csv)"
            + ("." if metric == "euclidean" else f". The silhouette uses the {metric} distance, the one the clustering used."),
            className="quality-intro",
        ),
        _table(["Index", "Value", "Reading"], rows, text_columns=(0, 2)),
        html.P("Per cluster", className="comparison-subheading"),
        _table(["Cluster", "Subjects", "Mean silhouette", "Negative silhouette"], cluster_rows, text_columns=(0,)),
        _chart_heading("Silhouette per cluster", "one panel per cluster"),
        *silhouette_chart,
        _tree_block(saved, n_clusters),
    ])


def _density_quality_content(
    run: ProductionRun, saved: SavedResults, soft_of: Callable[[ProductionRun], SoftMembership]
) -> html.Div:
    """The panel of an hdbscan / hdbscan_soft run: DBCV, the shares of clusters and noise and the mean probability of the
    subjects in their cluster (and, for hdbscan_soft, the persistence of the clusters) as the run saved them, its table
    per cluster and the DBCV of every cluster. A DBCV not defined for the run is a dash with the reason and no chart.
    hdbscan_soft adds its soft membership, read from the membership.npy the run saved."""
    soft = run.method == "hdbscan_soft"
    rows = [
        _saved_row("DBCV", saved, "dbcv", 3, "higher is better, from -1 to 1"),
        ["Clusters (noise excluded)", str(int(saved.values["n_clusters_found"])), ""],
        _saved_row("Largest cluster", saved, "largest_cluster_share", 1, "of the subjects", percent=True),
        _saved_row("Noise", saved, "noise_fraction", 1, "of the subjects", percent=True),
        _saved_row("Mean probability in own cluster", saved, "membership_mean", 3, "mean over the clustered subjects"),
    ]
    if soft:
        rows.append(_saved_row("Mean persistence", saved, "persistence_mean", 3, "mean over the clusters"))
    columns = ["Cluster", "Subjects", "DBCV", "Mean probability"] + (["Persistence"] if soft else [])
    cluster_rows = [
        [str(int(row.cluster)), str(int(row.n)), _cell(row.dbcv, 3), _cell(row.membership_mean, 3)]
        + ([_cell(row.persistence, 3)] if soft else [])
        for row in saved.per_cluster.itertuples()
    ]
    chart: list = []
    if not np.isnan(saved.values["dbcv"]):
        clusters = saved.per_cluster.set_index("cluster")[["n", "dbcv"]]
        try:
            figure = build_dbcv_figure(clusters, saved.values["dbcv"])
        except ValueError as exc:
            chart = [_chart_heading("DBCV per cluster", "one bar per cluster; the dashed line is the run's score"), html.P(str(exc), className="status-message")]
        else:
            chart = [
                _chart_heading("DBCV per cluster", "one bar per cluster; the dashed line is the run's score"),
                dcc.Graph(
                    figure=_italian_figure(figure),
                    config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
                    style={"width": "100%"},
                ),
            ]
    return html.Div([
        _density_guide(soft),
        html.P("As the production run saved them (production_results.csv).", className="quality-intro"),
        _table(["Index", "Value", "Reading"], rows, text_columns=(0, 2)),
        html.P("Per cluster", className="comparison-subheading"),
        _table(columns, cluster_rows, text_columns=(0,)),
        *chart,
        *([_soft_membership_block(run, soft_of)] if soft else []),
    ])


def cluster_quality_content_for(
    run: ProductionRun,
    results_of: Callable[[ProductionRun], SavedResults] = run_production_results,
    silhouette_of: Callable[[ProductionRun], SilhouetteBreakdown] = run_silhouette_samples,
    soft_of: Callable[[ProductionRun], SoftMembership] = run_soft_membership,
    metric_of: Callable[[ProductionRun], str] = run_distance_metric,
) -> html.Div:
    """Panel "Clustering evaluation" of an agglomerative, hdbscan or hdbscan_soft run: under the collapsed guide to the
    indices, the numbers the production run saved (`results_of`: production_results.csv and
    production_results_per_cluster.csv, never computed again) and its table per cluster. An agglomerative run adds the
    silhouette of every subject (`silhouette_of`), the one part computed here; an hdbscan_soft run its soft membership.
    Not tied to the chosen cluster.

    Same never-raises contract as every other *_content_for: a run without the saved files (written before production
    runs saved them) or with files that are not its method's renders the cause instead of a table, and so does a method
    the panel has no numbers for."""
    if run.method not in RESULTS_METHODS:
        return html.Div([html.P(
            f"The panel has no numbers for the method {run.method!r}: production runs of {list(RESULTS_METHODS)} save them.",
            className="status-message",
        )])
    agglomerative = run.method == "agglomerative"
    try:
        saved = results_of(run)
        metric = metric_of(run) if agglomerative else ""
    except (ValueError, OSError) as exc:
        guide = _quality_guide() if agglomerative else _density_guide(run.method == "hdbscan_soft")
        return html.Div([guide, html.P(str(exc), className="status-message")])
    if agglomerative:
        return _agglomerative_quality_content(run, saved, metric, silhouette_of)
    return _density_quality_content(run, saved, soft_of)


def _chart_heading(title: str, subtitle: str) -> html.Div:
    """The title of a chart as page text (a sub-heading and one line under it), not inside the figure."""
    return html.Div([
        html.P(title, className="comparison-subheading"),
        html.P(subtitle, className="quality-intro"),
    ])


if TYPE_CHECKING:  # importing it for real would close a loop through the panels
    from src.analysis.embedding_app.context import AppContext


def register_callbacks(app: Dash, context: AppContext) -> None:
    """Wires this panel to the app. Called once by build_app, which owns the layout the ids
    below refer to."""
    @app.callback(
        Output("cluster-quality-content", "children"),
        Output("cluster-quality-poll", "disabled"),
        Input("run-picker", "value"),
        Input("cluster-quality-poll", "n_intervals"),
        Input("selected-page-tab", "data"),
    )
    def _update_cluster_quality(run_key: str | None, _n_intervals: int, selected_tab: str | None):
        if run_key in (None, UNSET):
            raise PreventUpdate
        run = context.runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        if not tab_is_active(run, selected_tab, TAB_CLUSTERING):
            return [], True  # nothing shown, so nothing to poll for (reopening the tab restarts it)
        if run.method == "adp":
            content, pending = adp_quality_content_for(run, summary_of=context.adp_summary)
            return content, not pending
        return cluster_quality_content_for(run, silhouette_of=context.silhouette, soft_of=context.soft_membership), True
