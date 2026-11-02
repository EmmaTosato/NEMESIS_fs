"""Two clusters of one run against each other: what separates them clinically, which
variables predict membership, and how far apart their centroids are.

The other half of the parked comparison section, kept apart the same way its two source
modules are (cluster_comparison vs cluster_pair): this one never leaves a single run.
"""

from __future__ import annotations

from collections.abc import Callable

import nibabel as nib
import numpy as np
import pandas as pd
from dash import dcc, html
from nilearn import plotting as nilearn_plotting
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.cluster_pair import (
    PairComparison,
    PairFrame,
    build_odds_ratio_figure,
    centroid_separation,
    difference_image,
    pair_clinical_comparison,
    pair_frame,
    pair_regression,
    regression_term_label,
)
from src.analysis.embedding_app.anatomy import (
    DISCONNECTION_PERCENT_MODE,
    _ANATOMY_VIEWER_WIDTH,
    LesionViewerConfig,
    SdcViewerConfig,
    _anatomy_viewer,
    _build_cluster_disconnection_view,
    _build_cluster_overlap_view,
)
from src.analysis.embedding_app.blocks import _missing_subjects_warning, _table, _warning_box
from src.analysis.embedding_app.embedding_view import _CLUSTER_LABEL_COLUMN, cluster_options
from src.analysis.embedding_app.panels.comparison import _points, comparison_run_label
from src.analysis.embedding_app.runs import ProductionRun, run_metadata
from src.analysis.embedding_app.style import _italian_figure
from src.utils.artifacts import load_matrix
from src.utils.number_format import format_number, format_scientific


# --- Two clusters of the same run (08-10-26) --------------------------------------------------

_PAIR_SIGNIFICANCE_LEVEL = 0.05


def _pair_name(label: int) -> str:
    """"cluster 3", or "rumore" for HDBSCAN's -1 bucket. The two clusters are always called by
    their real label, never "1" and "2": a run's labels start at 0, and "cluster 1" would then
    name a different cluster than the one labelled 1."""
    return "noise" if label == -1 else f"cluster {label}"


def pair_cluster_option_label(label: int, metadata: pd.DataFrame) -> str:
    n_subjects = int((metadata[_CLUSTER_LABEL_COLUMN] == label).sum())
    return f"{_pair_name(label).capitalize()} · {format_number(n_subjects, 0)} subjects"


def _format_p(value: float) -> str:
    if np.isnan(value):
        return "—"
    return format_number(value, 3) if value >= 0.001 else format_scientific(value, 1)


def _p_fdr_cell(value: float):
    """The corrected p, in bold when it is under the 0.05 level."""
    text = _format_p(value)
    return html.Span(text, className="stat-value") if not np.isnan(value) and value < _PAIR_SIGNIFICANCE_LEVEL else text


def _format_optional(value: float, decimals: int) -> str:
    return "—" if np.isnan(value) else format_number(value, decimals)


def _format_median(value: float) -> str:
    """Whole numbers from 100 up (a voxel count), two decimals below (an age is read to the year
    elsewhere, but a share of the lesion is 0.xx)."""
    return "—" if np.isnan(value) else format_number(value, 0 if abs(value) >= 100 else 2)


def _cluster_pair_summary(run: ProductionRun, metadata: pd.DataFrame, label_1: int, label_2: int) -> html.Div:
    def line(role: str, label: int) -> html.P:
        n_subjects = int((metadata[_CLUSTER_LABEL_COLUMN] == label).sum())
        return html.P([html.B(f"{role}: "), f"{_pair_name(label)} · {format_number(n_subjects, 0)} subjects"])

    return html.Div(
        className="comparison-summary",
        children=[html.P([html.B("Run: "), comparison_run_label(run)]), line("First cluster", label_1), line("Second cluster", label_2)],
    )


def _cluster_pair_clinical_block(pair: PairFrame, label_1: int, label_2: int) -> html.Div:
    heading = html.H3("Demographic and clinical profile", className="comparison-heading")
    try:
        comparison: PairComparison = pair_clinical_comparison(pair, label_1)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)

    numeric_rows = [
        [
            row.variable, format_number(int(row.n_1), 0), format_number(int(row.n_2), 0),
            _format_median(row.median_1), _format_median(row.median_2), _format_optional(row.r, 2),
            _format_p(row.p), _p_fdr_cell(row.p_fdr),
        ]
        for row in comparison.numeric.itertuples()
    ]
    categorical_rows = [
        [
            row.variable, row.category, format_number(int(row.n_1), 0), format_number(int(row.n_2), 0),
            "—" if np.isnan(row.share_1) else f"{format_number(100 * row.share_1, 1)}%",
            "—" if np.isnan(row.share_2) else f"{format_number(100 * row.share_2, 1)}%",
            _format_optional(row.odds_ratio, 2), _format_p(row.p), _p_fdr_cell(row.p_fdr),
        ]
        for row in comparison.categorical.itertuples()
    ]
    children: list = [
        heading,
        _points(
            f"Each row compares a variable between {name_1} and {name_2}, on the subjects of the two clusters.",
            [
                [html.B("Numeric variables"), f" (Mann-Whitney test): the medians are compared. “r” measures the difference, "
                 f"from -1 to 1: positive if the values of {name_1} are higher, negative if they are lower, 0 if there is no difference. "
                 "Beyond 0.3 (in absolute value) the difference is already visible."],
                [html.B("Categorical variables"), f" (Fisher exact test, one category against all the others): the share "
                 f"of subjects with that category is compared. The odds ratio is above 1 if the category is more frequent in {name_1}, "
                 f"below 1 if it is more frequent in {name_2}."],
                [html.B("p"), " is the probability that the difference is due to chance; ", html.B("p (FDR)"),
                 " is the same value corrected for the number of comparisons made together. In bold below 0.05: "
                 "the difference is probably real."],
                [html.B("“—”"), ": the test was not run, because on one side there are fewer than 2 subjects with the data."],
            ],
        ),
    ]
    warning = _pair_unregistered_warning(pair.unregistered)
    if warning is not None:
        children.append(warning)
    children += [
        html.P("Numeric variables", className="comparison-subheading"),
        _table(
            ["Variable", f"n\n{name_1}", f"n\n{name_2}", f"Median\n{name_1}", f"Median\n{name_2}", "r", "p", "p\n(FDR)"],
            numeric_rows,
        ),
        html.P("Categorical variables", className="comparison-subheading"),
        _table(
            ["Variable", "Category", f"n\n{name_1}", f"n\n{name_2}", f"Share\n{name_1}", f"Share\n{name_2}", "Odds\nratio", "p", "p\n(FDR)"],
            categorical_rows,
            text_columns=(0, 1),
        ),
    ]
    return html.Div(children)


def _pair_unregistered_warning(unregistered: list[str]) -> html.Div | None:
    if not unregistered:
        return None
    return _warning_box(
        f"{len(unregistered)} subjects of the two clusters have no row in the registry (assets/metadata/participants.csv). "
        "They count in the number of subjects of each cluster, but carry no value.",
        detail=", ".join(unregistered),
    )


def _cluster_pair_regression_block(pair: PairFrame, label_1: int, label_2: int) -> html.Div:
    heading = html.H3("What distinguishes the two clusters", className="comparison-heading")
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)
    note = _points(
        f"For each variable: how much the probability of being in {name_1} rather than in {name_2} changes, all the others being equal. "
        "Only the subjects of the two clusters are used (logistic regression).",
        [
            [html.B("Variables considered"), ": age, NIHSS, lesion volume (log10), cortical share, subcortical gray share "
             "and infratentorial share, sex and dataset."],
            [html.B("Odds ratio"), f": above 1 the variable makes more likely {name_1}, below 1 {name_2}, equal to 1 it does not "
             "change anything. For numeric variables it is per one more standard deviation."],
            [html.B("Blue dot"), ": the 95% confidence interval does not contain 1, so the effect is distinguishable from “no effect”."],
            [html.B("Warning"), ": it is an association, not a cause. A variable derived from the clustering input "
             "(the volume, for a lesion run) is associated with the clusters by construction too."],
            ["Subjects with missing data in any of the variables are excluded."],
        ],
    )
    try:
        result = pair_regression(pair, label_1)
    except ValueError as exc:
        return html.Div([heading, note, html.P(str(exc), className="status-message")])

    config = {"displayModeBar": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"], "displaylogo": False}
    rows = [
        [
            regression_term_label(term), format_number(row.odds_ratio, 2),
            f"{format_number(row.ci_low, 2)} – {format_number(row.ci_high, 2)}", _format_p(row.p_value),
            format_number(row.vif, 1),
        ]
        for term, row in result.coefficients.iterrows()
    ]
    return html.Div([
        heading,
        note,
        html.P(
            f"{format_number(result.n_used, 0)} subjects used ({format_number(result.n_in_cluster, 0)} in {name_1}, "
            f"{format_number(result.n_used - result.n_in_cluster, 0)} in {name_2}; "
            f"{format_number(result.n_dropped_missing, 0)} excluded for missing data) · AUC = {format_number(result.auc, 2)} · "
            f"pseudo-R² = {format_number(result.pseudo_r2, 2)}",
            className="comparison-summary-line",
        ),
        dcc.Graph(figure=_italian_figure(build_odds_ratio_figure(result, label_1, label_2)), config=config, style={"width": "100%"}),
        _table(["Variable", "Odds\nratio", "Interval\n95%", "p", "VIF"], rows),
        _points(
            "How to read the quality measures:",
            [
                [html.B("AUC"), ": how well the variables together distinguish the two clusters. 0.5 = as by chance, 1 = perfectly. "
                 "It is computed on the same subjects as the model, so it is slightly optimistic."],
                [html.B("Pseudo-R² (McFadden)"), ": 0.2-0.4 is already a good fit."],
                [html.B("VIF"), ": how much a variable is already explained by the others. Above about 5 its odds ratio is unstable."],
            ],
        ),
    ])


def _cluster_pair_centroid_block(
    run: ProductionRun, embedding: np.ndarray, metadata: pd.DataFrame, label_1: int, label_2: int
) -> html.Div:
    heading = html.H3("Distance between centroids", className="comparison-heading")
    if run.reduction_method == "raw":
        return html.Div([
            heading,
            html.P(
                "The run is on raw data: its matrix is the feature space, not an embedding, and the centroids "
                "are not computed.",
                className="status-message",
            ),
        ])
    try:
        separation = centroid_separation(embedding, metadata, label_1, label_2)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)
    return html.Div([
        heading,
        _points(
            "How far apart the two clusters are in the space the clustering was run on.",
            [
                [html.B("Distance between centroids"), ": the straight-line distance between the centers of the two clusters."],
                [html.B("Radius"), ": the mean distance of the subjects of a cluster from its own center, i.e. how “wide” the cluster is."],
                [html.B("How to read them"), ": distance much larger than the two radii = well separated clusters; "
                 "distance similar to the radii = clusters that touch."],
            ],
        ),
        _table(
            ["Distance between\ncentroids", f"Radius\n{name_1}", f"Radius\n{name_2}"],
            [[
                html.Span(format_number(separation.distance, 2), className="stat-value"),
                format_number(separation.radius_1, 2), format_number(separation.radius_2, 2),
            ]],
        ),
    ])


def cluster_pair_content_for(run: ProductionRun, label_1: int, label_2: int) -> html.Div | html.P:
    """Mode "Dentro lo stesso clustering" of the "Confronto" section (08-10-26, on request), without
    the anatomy (cluster_pair_anatomy_for, a separate and much slower panel): the clinical profile,
    the regression and the centroid distance of two clusters of `run`.

    Same never-raises contract as every other *_content_for function here: a run that is not a
    clustering run, a cluster that is empty or the same as the other, or a registry that cannot be
    read renders an html.P status message naming the cause."""
    try:
        if run.pipeline != "clustering":
            raise ValueError(f"{run.key} is not a clustering run")
        embedding, metadata, _extra = load_matrix(run.path)
        pair = pair_frame(metadata, label_1, label_2)
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message")
    return html.Div([
        _cluster_pair_summary(run, metadata, label_1, label_2),
        _cluster_pair_clinical_block(pair, label_1, label_2),
        _cluster_pair_regression_block(pair, label_1, label_2),
        _cluster_pair_centroid_block(run, embedding, metadata, label_1, label_2),
    ])


def _pair_map_viewers(
    build: Callable[[int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]],
    label_1: int, label_2: int, what: str,
) -> list:
    """The map of each cluster and their difference, as three anatomy viewers. `build(label)` is the
    same per-cluster builder the single-cluster panels use (cached in the running app); what comes
    back is each cluster's own image, subtracted voxel by voxel. `what` names the quantity ("lesione"
    or "disconnessione"). A failure of either cluster (no subject with a file on disk) is one status
    message, never a difference built from half of it."""
    name_1, name_2 = _pair_name(label_1), _pair_name(label_2)
    try:
        view_1, n_1, image_1, missing_1 = build(label_1)
        view_2, n_2, image_2, missing_2 = build(label_2)
        difference = difference_image(image_1, image_2)
    except ValueError as exc:
        return [html.P(str(exc), className="status-message")]
    difference_view = nilearn_plotting.view_img(
        difference, bg_img="MNI152", black_bg=False, threshold=1e-6, cmap="RdBu_r", symmetric_cmap=True, title=None,
        width_view=_ANATOMY_VIEWER_WIDTH,
    )
    caption = f"Color = % of subjects in the cluster with {what} in that voxel (0-100%)"
    return [
        _anatomy_viewer(view_1, f"{_pair_name(label_1).capitalize()} (n={n_1})", caption, warning=_missing_subjects_warning(missing_1)),
        _anatomy_viewer(view_2, f"{_pair_name(label_2).capitalize()} (n={n_2})", caption, warning=_missing_subjects_warning(missing_2)),
        _anatomy_viewer(
            difference_view, f"Difference: {name_1} minus {name_2}",
            f"Red: {what} more frequent in {name_1}. Blue: more frequent in {name_2}. The intensity is the difference "
            "between the two percentages of subjects, in percentage points, voxel by voxel.",
        ),
    ]


def cluster_pair_anatomy_for(
    run: ProductionRun, label_1: int, label_2: int, lesion_cfg: LesionViewerConfig, sdc_cfg: SdcViewerConfig,
    build_overlap_view: Callable[..., tuple[StatMapView, int, nib.Nifti1Image, list[str]]] = _build_cluster_overlap_view,
    build_disconnection_view: Callable[..., tuple[StatMapView, int, nib.Nifti1Image, list[str]]] = _build_cluster_disconnection_view,
) -> html.Div | html.P:
    """The anatomy of two clusters of `run` (08-10-26, on request): the lesion overlap map of each and
    their difference and, for an sdc run, the same three for the disconnection (percent mode, so the
    difference is in points of the same quantity as the lesion one).

    A separate panel from cluster_pair_content_for because building a cluster's map reads every one of
    its subjects' NIfTI files the first time (build_app passes cached builders, as for the
    single-cluster panels): the numbers above must not wait for it. Never raises (same contract as
    overlap_map_content_for): a failure is an html.P status message."""
    try:
        if run.pipeline != "clustering":
            raise ValueError(f"{run.key} is not a clustering run")
        metadata = run_metadata(run)
        if label_1 == label_2:
            raise ValueError(f"the two clusters are the same ({_pair_name(label_1)}): nothing to compare")
        present = set(cluster_options(metadata))
        for label in (label_1, label_2):
            if label not in present:
                raise ValueError(f"no subjects with {_CLUSTER_LABEL_COLUMN}={label!r} in this run's metadata")
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message")

    children: list = [
        html.H3("Lesion anatomy", className="comparison-heading"),
        *_pair_map_viewers(
            lambda label: build_overlap_view(run, metadata, label, lesion_cfg), label_1, label_2, "lesion"
        ),
    ]
    if run.modality == "sdc":
        children += [
            html.H3("Disconnection anatomy", className="comparison-heading"),
            *_pair_map_viewers(
                lambda label: build_disconnection_view(run, metadata, label, sdc_cfg, DISCONNECTION_PERCENT_MODE),
                label_1, label_2, "disconnection",
            ),
        ]
    return html.Div(children)
