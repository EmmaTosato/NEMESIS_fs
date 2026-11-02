"""Two clusterings side by side: how much they agree, and on which subjects they disagree.

Either two clusters of the same run or two runs of different modalities on the same cohort
(COMPARISON_MODE_RULES says which pairs are comparable at all). Parked: built and tested, not
mounted in the app - see code_standards.md section 2.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from dash import dcc, html

from src.analysis.cluster_comparison import (
    AGREEMENT_LEVELS,
    AGREEMENT_SCALE,
    AlignedRuns,
    ContingencyTables,
    agreement_level,
    agreement_metrics,
    align_runs,
    build_table_heatmap,
    chi_square_independence,
    cluster_name,
    contingency_tables,
    purity_table,
)
from src.analysis.cluster_description import clusters_comparison_stats
from src.analysis.embedding_app.blocks import _table
from src.analysis.embedding_app.embedding_view import _CLUSTER_LABEL_COLUMN
from src.analysis.embedding_app.panels.description import _clusters_comparison_table
from src.analysis.embedding_app.picker import _load_tag_params_or_none, _run_tag_param_label
from src.analysis.embedding_app.runs import ProductionRun, _run_chronological_key, run_metadata, run_reduction_axis
from src.analysis.embedding_app.style import _italian_figure
from src.utils.number_format import format_number, format_scientific


# --- Comparison inside a run and between two runs (08-10-26) ------------------------------------

COMPARISON_MODE_CLUSTERS = "clusters"
COMPARISON_MODE_MODALITY = "modality"
COMPARISON_MODE_LABELS: dict[str, str] = {
    COMPARISON_MODE_CLUSTERS: "Within the same clustering",
    COMPARISON_MODE_MODALITY: "Between modalities (lesion vs sdc)",
}
COMPARISON_MODE_RULES: dict[str, str] = {
    COMPARISON_MODE_CLUSTERS: (
        "Two clusters of the same run (also the HDBSCAN noise, -1): demographic and clinical profile, "
        "variables that distinguish them, distance between centroids and anatomy, on the subjects of the two clusters only."
    ),
    COMPARISON_MODE_MODALITY: (
        "Two runs of different modalities (lesion and sdc) with the same clustering method, the same parameters "
        "and the same starting embedding (reduction method, components, metric): "
        "only the modality changes, and the comparison is made on the subjects in common."
    ),
}


def comparison_run_label(run: ProductionRun) -> str:
    return f"{run.modality} · {run.method} · {run.run_name}"


def comparison_candidates(runs: list[ProductionRun]) -> list[ProductionRun]:
    """Runs that can be the first side of a comparison, in either mode: every clustering run.
    Ordered by modality, method, then chronologically."""
    candidates = [run for run in runs if run.pipeline == "clustering"]
    return sorted(candidates, key=lambda run: (run.modality, run.method, _run_chronological_key(run)))


def comparison_incompatibility(run_a: ProductionRun, run_b: ProductionRun, clustering_params_file: str | Path) -> str | None:
    """Why `run_a` and `run_b` cannot be compared across modalities, or None if they can: different
    modality, but same clustering method, same values of that method's registered tag_param
    (k, linkage, ...) and same upstream embedding settings - so that the only thing that varies is
    the modality, never also the clustering criterion.

    Raises ValueError when a run's config.md/params cannot be read."""
    if run_a.key == run_b.key:
        return "the two runs are the same run"
    for run in (run_a, run_b):
        if run.pipeline != "clustering":
            return f"{run.key} is not a clustering run"
    if run_a.modality == run_b.modality:
        return f"both runs have modality {run_a.modality!r}: different modalities are needed"
    if run_a.method != run_b.method:
        return f"different clustering methods ({run_a.method} ≠ {run_b.method}): in this mode only the modality must change"
    if run_a.reduction_method != run_b.reduction_method:
        return f"different reduction methods ({run_a.reduction_method} ≠ {run_b.reduction_method})"
    axis_a, axis_b = run_reduction_axis(run_a), run_reduction_axis(run_b)
    if axis_a != axis_b:
        return f"different starting embeddings (metric, components): {axis_a} ≠ {axis_b}"
    tag_param = _load_tag_params_or_none(clustering_params_file, run_a.method)
    if tag_param:
        label_a, label_b = _run_tag_param_label(run_a, tag_param), _run_tag_param_label(run_b, tag_param)
        if label_a is None or label_b is None:
            raise ValueError(f"{run_a.path} / {run_b.path}: cannot read the {run_a.method} parameters of both runs")
        if label_a != label_b:
            return f"different method parameters ({label_a} ≠ {label_b})"
    return None


def comparable_runs(runs: list[ProductionRun], run_a: ProductionRun, clustering_params_file: str | Path) -> list[ProductionRun]:
    """The runs that can sit opposite `run_a` across modalities (the options of the second picker).
    A run whose config.md or params cannot be read is left out and logged, like the other pickers:
    one broken run must not hide every other option."""
    compatible = []
    for candidate in comparison_candidates(runs):
        try:
            reason = comparison_incompatibility(run_a, candidate, clustering_params_file)
        except ValueError as exc:
            logging.warning("%s: excluded from the comparison options: %s", candidate.path, exc)
            continue
        if reason is None:
            compatible.append(candidate)
    return compatible


def _points(lead: str, points: list) -> html.Div:
    """A note as one lead sentence and one short line per idea; a point is a string or a list of
    children (so a term can be bold)."""
    return html.Div([
        html.P(lead, className="comparison-lead"),
        html.Ul([html.Li(point) for point in points], className="comparison-points"),
    ])


def _agreement_guide() -> html.Details:
    """How to read the four agreement metrics, collapsed under the metrics table."""
    scale_rows = [
        [level, f"{_scale_range(AGREEMENT_SCALE['ARI'], i)}", f"{_scale_range(AGREEMENT_SCALE['NMI'], i)}"]
        for i, level in enumerate(AGREEMENT_LEVELS)
    ]
    return html.Details(
        className="comparison-guide",
        children=[
            html.Summary("How to read these metrics"),
            html.Ul([
                html.Li([html.B("ARI (Adjusted Rand Index): "), (
                    "agreement between the two partitions, corrected for chance. It counts the pairs of subjects put together "
                    "(or separated) by both. 1 = identical, 0 = as by chance, it can go below 0. "
                    "It does not inflate when there are many clusters."
                )]),
                html.Li([html.B("NMI (Normalized Mutual Information): "), (
                    "how much information the two partitions share, between 0 and 1. It is the harmonic mean of "
                    "homogeneity and completeness. More intuitive than ARI, but it can overestimate the agreement with many clusters."
                )]),
                html.Li([html.B("Homogeneity: "), "how much each cluster of A contains subjects of a single cluster of B (1 if A is a finer subdivision of B)."]),
                html.Li([html.B("Completeness: "), "how much the subjects of a cluster of B stay together in a single cluster of A (1 if B is a finer subdivision of A)."]),
            ]),
            html.P(
                "NMI, being a mean, hides the direction of an imbalance: two pairs with the same NMI "
                "can have low homogeneity and high completeness, or the opposite. That is why the two should "
                "also be read separately. High homogeneity and low completeness means A is finer than B "
                "(it splits the clusters of B); the opposite, that B is finer than A. The contingency table below "
                "tells which clusters cause the imbalance.",
                className="comparison-note",
            ),
            _table(["Level", "ARI", "NMI"], scale_rows),
        ],
    )


def _scale_range(bounds: tuple[float, ...], level_index: int) -> str:
    if level_index == 0:
        return f"< {bounds[0]}"
    if level_index == len(bounds):
        return f"> {bounds[-1]}"
    return f"{bounds[level_index - 1]}–{bounds[level_index]}"


def _comparison_summary(run_a: ProductionRun, run_b: ProductionRun, aligned: AlignedRuns) -> html.Div:
    """Which run is A and B, and how many subjects the comparison actually covers: the
    intersection is always stated against each run's full size, never absorbed silently."""
    return html.Div(
        className="comparison-summary",
        children=[
            html.P([html.B("A: "), comparison_run_label(run_a), f" · {format_number(aligned.n_a, 0)} subjects"]),
            html.P([html.B("B: "), comparison_run_label(run_b), f" · {format_number(aligned.n_b, 0)} subjects"]),
            html.P(
                [
                    html.B("Compared: "),
                    f"{format_number(aligned.n_common, 0)} subjects in common "
                    f"(only in A: {format_number(aligned.n_only_a, 0)} · only in B: {format_number(aligned.n_only_b, 0)}).",
                ]
            ),
        ],
    )


def _agreement_block(aligned: AlignedRuns) -> html.Div:
    metrics = agreement_metrics(aligned.labels_a, aligned.labels_b)
    rows = [
        [name, html.Span(format_number(value, 3), className="stat-value"), agreement_level(name, value) or "—"]
        for name, value in metrics.items()
    ]
    return html.Div([
        html.H3("Agreement between the partitions", className="comparison-heading"),
        _table(["Metric", "Value", "Reading"], rows, text_columns=(0, 2)),
        _agreement_guide(),
    ])


def _contingency_block(tables: ContingencyTables) -> html.Div:
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    figures = [
        build_table_heatmap(
            tables.counts, title="Subjects per pair of clusters", row_axis_title="cluster of A",
            column_axis_title="cluster of B", decimals=0, colorbar_title="subjects",
        ),
        build_table_heatmap(
            tables.row_pct, title="By row: where each cluster of A goes", row_axis_title="cluster of A",
            column_axis_title="cluster of B", decimals=1, suffix="%", colorbar_title="% of the row",
        ),
        build_table_heatmap(
            tables.col_pct, title="By column: where each cluster of B comes from", row_axis_title="cluster of A",
            column_axis_title="cluster of B", decimals=1, suffix="%", colorbar_title="% of the column",
        ),
    ]
    return html.Div([
        html.H3("Where each cluster ends up", className="comparison-heading"),
        html.P(
            "The numeric labels of the two clusterings are independent: cluster 0 of A is not “the same” as 0 of B. "
            "Only where the mass goes matters. By row: if almost everything is in one column, that cluster of A coincides with a "
            "cluster of B; if it is spread out, the two clusterings split it differently. By column the same holds, read "
            "from the side of B.",
            className="comparison-note",
        ),
        html.Div(
            className="composition-grid",
            children=[dcc.Graph(figure=_italian_figure(figure), config=config, style={"width": "100%"}) for figure in figures],
        ),
    ])


def _chi_square_block(counts: pd.DataFrame) -> html.Div:
    heading = html.H3("Statistical association", className="comparison-heading")
    try:
        result = chi_square_independence(counts)
    except ValueError as exc:
        return html.Div([heading, html.P(str(exc), className="status-message")])
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    figure = build_table_heatmap(
        result.residuals, title="Standardized residuals", row_axis_title="cluster of A",
        column_axis_title="cluster of B", decimals=1, diverging=True, colorbar_title="residual",
    )
    return html.Div([
        heading,
        html.P(
            [
                html.B("Chi-square test of independence: "),
                f"χ² = {format_number(result.chi2, 1)}, degrees of freedom = {result.dof}, p = {format_scientific(result.p_value, 2)}.",
            ],
            className="comparison-summary-line",
        ),
        html.P(
            "H0: membership in a cluster of A is independent of membership in a cluster of B. With low p (< 0.05) the two "
            "partitions are not independent. The residuals tell where: red = the pair of clusters co-occurs more than "
            "expected, blue = less, gray = in line with independence. The p-value tells whether there is an association, the residuals "
            "which pairs drive it.",
            className="comparison-note",
        ),
        dcc.Graph(figure=_italian_figure(figure), config=config, style={"width": "100%"}),
    ])


def _purity_table(counts: pd.DataFrame, source: str, target: str) -> html.Div:
    table = purity_table(counts)
    rows = [
        [
            f"{source}: {cluster_name(int(label))}",
            format_number(int(row.n_subjects), 0),
            f"{target}: {cluster_name(int(row.dominant_target_cluster))}",
            html.Span(f"{format_number(float(row.purity_pct), 1)}%", className="stat-value"),
        ]
        for label, row in table.iterrows()
    ]
    return html.Div([
        html.P(f"Clusters of {source} to {target}", className="comparison-subheading"),
        _table(["Cluster", "Subjects", "Mostly goes to", "Share"], rows, text_columns=(0, 2)),
    ])


def _purity_block(counts: pd.DataFrame) -> html.Div:
    return html.Div([
        html.H3("Cluster purity", className="comparison-heading"),
        html.P(
            "For each cluster: where the largest share of its subjects ends up and how much it weighs. From the least pure (spread over "
            "several clusters) to the purest (almost all in one). The two directions are complementary: a cluster of A may "
            "flow entirely into one of B, while that of B also collects subjects of other clusters of A.",
            className="comparison-note",
        ),
        html.Div(
            className="composition-grid",
            children=[_purity_table(counts, "A", "B"), _purity_table(counts.T, "B", "A")],
        ),
    ])


def _clinical_profile_block(aligned: AlignedRuns, run_a: ProductionRun, run_b: ProductionRun) -> html.Div:
    """Clinical/demographic table of each run's clusters, on the common subjects. The centroids of
    two modalities live in different feature spaces and cannot be compared; what can be compared
    is the clinical phenotype of each cluster, which does not depend on coordinates."""
    heading = html.H3("Clinical profile of the clusters", className="comparison-heading")
    children: list = [
        heading,
        html.P(
            "The two modalities have different feature spaces: the centroids are not comparable. The comparison is on the "
            "clinical phenotype of each cluster, which does not depend on the coordinates. Subjects in common.",
            className="comparison-note",
        ),
    ]
    for side, run, labels in (("A", run_a, aligned.labels_a), ("B", run_b, aligned.labels_b)):
        frame = pd.DataFrame({"subject_id": aligned.subject_ids, _CLUSTER_LABEL_COLUMN: labels})
        children.append(html.P(f"{side}: {comparison_run_label(run)}", className="comparison-subheading"))
        try:
            children.append(_clusters_comparison_table(clusters_comparison_stats(frame), None))
        except (ValueError, OSError) as exc:
            children.append(html.P(str(exc), className="status-message"))
    return html.Div(children)


def comparison_content_for(run_a: ProductionRun, run_b: ProductionRun, clustering_params_file: str | Path) -> html.Div | html.P:
    """Mode "Tra modalità" of the "Confronto" section (08-10-26, on request): how two clustering
    runs of different modalities relate on the subjects they share - agreement metrics, contingency
    tables, chi-square test, purity, and the clinical profile of each cluster. Centroids are not
    compared: the two modalities live in different feature spaces.

    Same never-raises contract as every other *_content_for function here: a pair that is not
    comparable, a run that cannot be read or an empty intersection renders an html.P status
    message naming the cause, never a half-built section."""
    try:
        reason = comparison_incompatibility(run_a, run_b, clustering_params_file)
        if reason is not None:
            return html.P(f"The two runs are not comparable: {reason}.", className="status-message")
        aligned = align_runs(run_metadata(run_a), run_metadata(run_b))
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message")

    tables = contingency_tables(aligned.labels_a, aligned.labels_b)
    return html.Div([
        _comparison_summary(run_a, run_b, aligned),
        _agreement_block(aligned),
        _contingency_block(tables),
        _chi_square_block(tables.counts),
        _purity_block(tables.counts),
        _clinical_profile_block(aligned, run_a, run_b),
    ])
