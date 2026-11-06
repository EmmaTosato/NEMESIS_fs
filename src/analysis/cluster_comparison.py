"""Comparison of two clustering runs - feeds the "Tra modalità" mode of the "Confronto" section in
src/analysis/embedding_app/panels/comparison.py (two clusters of the same run are compared in cluster_pair.py).

Two runs are compared on the subjects they have in common: how much their partitions agree
(ARI, NMI, homogeneity, completeness), where each cluster of one lands in the other (contingency
table, as counts and as row/column percentages), whether the association is statistically real
(chi-square test and standardized residuals) and how pure each cluster is.

Which pairs of runs may be compared at all (same method and parameters on two modalities) is
decided by src.analysis.embedding_app, which knows the run layout; this module only receives the
two runs' metadata and never reads from disk. The only registry read is the demographic profile,
which lives in cluster_description.py.

The pair-counting external indices (ARI from agreement_metrics; Jaccard, Fowlkes-Mallows and Gamma from
external_indices) compare two whole partitions of the same subjects. They are symmetric, so neither run
is a reference, and they say how much two clusterings agree, not which one is right.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats
from sklearn.metrics import (
    adjusted_rand_score,
    completeness_score,
    homogeneity_score,
    normalized_mutual_info_score,
)
from sklearn.metrics.cluster import pair_confusion_matrix

from src.analysis.embedding_coloring import COLOR_MODES
from src.analysis.partition_shape import NOISE_LABEL

_CLUSTER_LABEL_COLUMN = COLOR_MODES["cluster_label"].column

_TEXT_COLOR = "#333"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)
# Sequential: one hue, light (near zero) to dark. Diverging: blue (fewer than expected) to a
# neutral gray midpoint to red (more than expected).
_SEQUENTIAL_SCALE = [[0.0, "#cde2fb"], [0.5, "#3987e5"], [1.0, "#0d366b"]]
_DIVERGING_SCALE = [[0.0, "#256abf"], [0.5, "#f0efec"], [1.0, "#d03b3b"]]
# Text inside a cell turns white once the fill is dark enough to need it: from 50% of the scale
# on the one-hue ramp, from 75% of either arm on the diverging one (its midpoint is a light gray,
# so its arms stay pale for longer).
_DARK_FILL_THRESHOLD = 0.5
_DARK_FILL_THRESHOLD_DIVERGING = 0.75
_CELL_HEIGHT = 56
_FIGURE_MARGIN_HEIGHT = 150

AGREEMENT_METRICS: tuple[str, ...] = ("ARI", "NMI", "homogeneity", "completeness")
PAIR_COUNTING_METRICS: tuple[str, ...] = ("Jaccard", "Fowlkes-Mallows", "Gamma")

# Reading scale for the two metrics that have one: upper bounds of the first four levels (a value
# equal to a bound belongs to the level above it). Homogeneity and completeness have no scale -
# they are read as a pair, by their imbalance.
AGREEMENT_LEVELS: tuple[str, ...] = ("debole/trascurabile", "moderato", "discreto", "forte", "quasi identiche")
AGREEMENT_SCALE: dict[str, tuple[float, float, float, float]] = {
    "ARI": (0.2, 0.4, 0.6, 0.8),
    "NMI": (0.3, 0.5, 0.7, 0.85),
}


@dataclass(frozen=True)
class AlignedRuns:
    """The two runs restricted to their common subjects, in run A's order.

    n_a/n_b are the runs' full sizes, kept so the intersection is always reported against them."""

    subject_ids: np.ndarray
    labels_a: np.ndarray
    labels_b: np.ndarray
    n_a: int
    n_b: int

    @property
    def n_common(self) -> int:
        return len(self.subject_ids)

    @property
    def n_only_a(self) -> int:
        return self.n_a - self.n_common

    @property
    def n_only_b(self) -> int:
        return self.n_b - self.n_common


@dataclass(frozen=True)
class ContingencyTables:
    """counts[i, j] = subjects in cluster i of run A and cluster j of run B. row_pct sums to 100
    along each row (where a cluster of A goes), col_pct along each column (where a cluster of B
    comes from)."""

    counts: pd.DataFrame
    row_pct: pd.DataFrame
    col_pct: pd.DataFrame


@dataclass(frozen=True)
class PairCounts:
    """Pairs of subjects by how two partitions A and B treat them: `a` together in both, `b` together
    only in A, `c` together only in B, `d` apart in both (Bicego's a, b, c, d)."""

    a: int
    b: int
    c: int
    d: int

    @property
    def total(self) -> int:
        return self.a + self.b + self.c + self.d


@dataclass(frozen=True)
class ChiSquareResult:
    chi2: float
    p_value: float
    dof: int
    residuals: pd.DataFrame


def cluster_name(label: int) -> str:
    """Display name of a cluster label: hdbscan's -1 bucket is noise, not a cluster named "-1"."""
    return "noise" if label == NOISE_LABEL else str(label)


def _require_comparable_metadata(metadata: pd.DataFrame, name: str) -> None:
    for column in ("subject_id", _CLUSTER_LABEL_COLUMN):
        if column not in metadata.columns:
            raise ValueError(f"run {name}: metadata has no {column!r} column - not a clustering run")
    duplicated = metadata.loc[metadata["subject_id"].duplicated(), "subject_id"].tolist()
    if duplicated:
        raise ValueError(f"run {name}: duplicate subject_id in metadata, cannot align by subject: {duplicated[:5]}")


def align_runs(metadata_a: pd.DataFrame, metadata_b: pd.DataFrame) -> AlignedRuns:
    """Inner join of the two runs on subject_id, in run A's order. A partial intersection is the
    expected case between two modalities, so it is not an error, but the counts of subjects left
    out on each side are part of the result and the caller must show them.

    Raises ValueError if either metadata lacks subject_id/cluster_label, has a repeated
    subject_id, or the two runs share no subject at all."""
    _require_comparable_metadata(metadata_a, "A")
    _require_comparable_metadata(metadata_b, "B")
    left = pd.DataFrame({
        "subject_id": metadata_a["subject_id"].to_numpy(),
        "label_a": metadata_a[_CLUSTER_LABEL_COLUMN].to_numpy(),
    })
    right = pd.DataFrame({
        "subject_id": metadata_b["subject_id"].to_numpy(),
        "label_b": metadata_b[_CLUSTER_LABEL_COLUMN].to_numpy(),
    })
    merged = left.merge(right, on="subject_id", how="inner")
    if merged.empty:
        raise ValueError("the two runs share no subject_id: the intersection is empty, there is nothing to compare")
    return AlignedRuns(
        subject_ids=merged["subject_id"].to_numpy(),
        labels_a=merged["label_a"].to_numpy(),
        labels_b=merged["label_b"].to_numpy(),
        n_a=len(metadata_a),
        n_b=len(metadata_b),
    )


def contingency_tables(labels_a: np.ndarray, labels_b: np.ndarray) -> ContingencyTables:
    counts = pd.crosstab(pd.Series(labels_a, name="A"), pd.Series(labels_b, name="B"))
    row_pct = counts.div(counts.sum(axis=1), axis=0) * 100
    col_pct = counts.div(counts.sum(axis=0), axis=1) * 100
    return ContingencyTables(counts=counts, row_pct=row_pct, col_pct=col_pct)


def agreement_metrics(labels_a: np.ndarray, labels_b: np.ndarray) -> dict[str, float]:
    """ARI, NMI, homogeneity and completeness, in AGREEMENT_METRICS order. A noise label (-1)
    counts as a group of its own.

    homogeneity: every cluster of A holds subjects of a single cluster of B (1 when A is a
    refinement of B). completeness: all the subjects of a cluster of B land in the same cluster of
    A (1 when B is a refinement of A). sklearn's scores take (labels_true, labels_pred) and define
    them on the predicted clusters, so B is passed as "true" and A as "predicted"."""
    return {
        "ARI": float(adjusted_rand_score(labels_a, labels_b)),
        "NMI": float(normalized_mutual_info_score(labels_a, labels_b)),
        "homogeneity": float(homogeneity_score(labels_b, labels_a)),
        "completeness": float(completeness_score(labels_b, labels_a)),
    }


def agreement_level(metric: str, value: float) -> str | None:
    """The AGREEMENT_LEVELS entry `value` falls in, for a metric with a reading scale (ARI, NMI);
    None for the others. Raises ValueError for a name that is not one of AGREEMENT_METRICS."""
    if metric not in AGREEMENT_METRICS:
        raise ValueError(f"unknown agreement metric {metric!r}, expected one of {AGREEMENT_METRICS}")
    if metric not in AGREEMENT_SCALE:
        return None
    return AGREEMENT_LEVELS[bisect_right(AGREEMENT_SCALE[metric], value)]


def noise_as_singletons(labels: np.ndarray) -> np.ndarray:
    """Give every noise subject (-1) a label of its own. Pair counting would otherwise count each pair
    of noise subjects as "together", inventing a similarity between subjects hdbscan assigned to no
    cluster."""
    labels = np.asarray(labels)
    noise = labels == NOISE_LABEL
    relabeled = labels.copy()
    first_free = int(labels.max()) + 1 if labels.size else 0
    relabeled[noise] = np.arange(first_free, first_free + int(noise.sum()))
    return relabeled


def pair_counts(labels_a: np.ndarray, labels_b: np.ndarray) -> PairCounts:
    """a, b, c, d over the unordered pairs of subjects. Labels are taken as they are (a -1 is a cluster
    like any other here: see noise_as_singletons). Raises ValueError for vectors of different length
    or fewer than 2 subjects, where there are no pairs."""
    if len(labels_a) != len(labels_b):
        raise ValueError(f"the two label vectors differ in length: {len(labels_a)} vs {len(labels_b)}")
    if len(labels_a) < 2:
        raise ValueError(f"pair counting needs at least 2 subjects, got {len(labels_a)}")
    matrix = pair_confusion_matrix(labels_a, labels_b)
    # sklearn counts ordered pairs, so every cell is twice the number of pairs. With A as "true" and B as
    # "predicted": [1,1] together in both, [1,0] together in A only, [0,1] in B only, [0,0] apart in both.
    return PairCounts(
        a=int(matrix[1, 1]) // 2, b=int(matrix[1, 0]) // 2, c=int(matrix[0, 1]) // 2, d=int(matrix[0, 0]) // 2
    )


def external_indices(labels_a: np.ndarray, labels_b: np.ndarray) -> dict[str, float]:
    """Jaccard, Fowlkes-Mallows and Gamma between two partitions of the same subjects, in
    PAIR_COUNTING_METRICS order (Bicego, L4b slides 61-66). The ARI, which replaces the Rand index, is not
    here: agreement_metrics already computes it. Every noise subject (-1) counts as a cluster of one.

    With m1 = a+b and m2 = a+c the pairs together in A and in B, and M the total: Jaccard = a/(a+b+c),
    Fowlkes-Mallows = a/sqrt(m1 m2), Gamma = (M a - m1 m2)/sqrt(m1 m2 (M-m1)(M-m2)) (the correlation
    between the two 0/1 pair matrices, from -1 to 1). All three are symmetric in A and B.

    Raises ValueError if either partition puts every subject in one cluster or every subject alone
    (noise included): Gamma has a zero denominator there and the others stop meaning agreement."""
    labels_a, labels_b = noise_as_singletons(labels_a), noise_as_singletons(labels_b)
    counts = pair_counts(labels_a, labels_b)
    total, together_a, together_b = counts.total, counts.a + counts.b, counts.a + counts.c
    for name, together in (("A", together_a), ("B", together_b)):
        if together == total:
            raise ValueError(f"run {name} puts every subject in one cluster: the indices are undefined")
        if together == 0:
            raise ValueError(f"run {name} leaves every subject alone (noise included): the indices are undefined")
    gamma_denominator = math.sqrt(together_a * together_b * (total - together_a) * (total - together_b))
    return {
        "Jaccard": counts.a / (counts.a + counts.b + counts.c),
        "Fowlkes-Mallows": counts.a / math.sqrt(together_a * together_b),
        "Gamma": (total * counts.a - together_a * together_b) / gamma_denominator,
    }


def chi_square_independence(counts: pd.DataFrame) -> ChiSquareResult:
    """Chi-square test of independence on `counts`, plus Pearson standardized residuals
    ((observed - expected) / sqrt(expected)): positive where two clusters co-occur more than
    independence predicts, negative where less.

    Raises ValueError if the table has fewer than 2 rows or 2 columns - with a single cluster on
    one side the two partitions cannot be associated or independent, the test is undefined."""
    if counts.shape[0] < 2 or counts.shape[1] < 2:
        raise ValueError(
            f"chi-square needs at least 2 clusters on each side, got a {counts.shape[0]}x{counts.shape[1]} table"
        )
    chi2, p_value, dof, expected = stats.chi2_contingency(counts)
    residuals = pd.DataFrame(
        (counts.to_numpy() - expected) / np.sqrt(expected), index=counts.index, columns=counts.columns
    )
    return ChiSquareResult(chi2=float(chi2), p_value=float(p_value), dof=int(dof), residuals=residuals)


def purity_table(counts: pd.DataFrame) -> pd.DataFrame:
    """For each row (source cluster) of `counts`: its size, the column (target cluster) holding
    most of its subjects, and that share in %. Sorted from the least pure (spread over several
    targets) to the purest. Pass `counts.T` for the opposite direction."""
    row_pct = counts.div(counts.sum(axis=1), axis=0) * 100
    table = pd.DataFrame({
        "n_subjects": counts.sum(axis=1),
        "dominant_target_cluster": row_pct.idxmax(axis=1),
        "purity_pct": row_pct.max(axis=1),
    })
    return table.sort_values("purity_pct")


def cluster_centroids(embedding: np.ndarray, labels: np.ndarray) -> pd.DataFrame:
    """Mean embedding coordinates of each cluster (rows: cluster label, columns dim0, dim1, ...)."""
    columns = [f"dim{i}" for i in range(embedding.shape[1])]
    return pd.DataFrame(embedding, columns=columns).assign(cluster_label=labels).groupby("cluster_label").mean()


def _text_color(fraction: float, diverging: bool) -> str:
    threshold = _DARK_FILL_THRESHOLD_DIVERGING if diverging else _DARK_FILL_THRESHOLD
    return "#ffffff" if fraction > threshold else _TEXT_COLOR


def build_table_heatmap(
    table: pd.DataFrame,
    *,
    title: str,
    row_axis_title: str,
    column_axis_title: str,
    decimals: int,
    suffix: str = "",
    diverging: bool = False,
    colorbar_title: str | None = None,
) -> go.Figure:
    """A heatmap of `table` with its value written in every cell, so the chart is also its own
    table view. Rows are the clusters of one run, columns those of the other; cluster 0 is on top.

    diverging=True draws a blue-gray-red scale centered on 0 (standardized residuals); otherwise
    a one-hue scale from 0 to the table's maximum (counts, percentages, distances)."""
    values = table.to_numpy(dtype=float)
    row_names = [cluster_name(int(label)) for label in table.index]
    column_names = [cluster_name(int(label)) for label in table.columns]
    if diverging:
        limit = float(np.abs(values).max()) or 1.0
        z_min, z_max, scale = -limit, limit, _DIVERGING_SCALE
    else:
        z_min, z_max, scale = 0.0, float(values.max()) or 1.0, _SEQUENTIAL_SCALE

    fig = go.Figure(go.Heatmap(
        z=values, x=column_names, y=row_names, zmin=z_min, zmax=z_max, colorscale=scale,
        xgap=2, ygap=2, hovertemplate=f"A={{y}} · B={{x}}: %{{z:.{decimals}f}}{suffix}<extra></extra>",
        colorbar=dict(title=dict(text=colorbar_title or "", font=dict(size=12)), thickness=12, len=0.9),
    ))
    for i, row_name in enumerate(row_names):
        for j, column_name in enumerate(column_names):
            fraction = abs(values[i, j]) / z_max if diverging else values[i, j] / z_max
            fig.add_annotation(
                x=column_name, y=row_name, text=f"{values[i, j]:.{decimals}f}{suffix}", showarrow=False,
                font=dict(size=14, color=_text_color(fraction, diverging)),
            )
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0, xanchor="left", font=dict(size=17)),
        xaxis=dict(title=column_axis_title, type="category", side="bottom"),
        yaxis=dict(title=row_axis_title, type="category", autorange="reversed"),
        height=_CELL_HEIGHT * len(row_names) + _FIGURE_MARGIN_HEIGHT,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR, size=13),
        margin=dict(l=70, r=20, t=70, b=70),
    )
    return fig
