"""Comparison of two clusters of the same clustering run (08-10-26, on request) - feeds the
"Dentro lo stesso clustering" mode of the "Confronto" section in src/analysis/embedding_app.py.

Four views of "cluster 1 versus cluster 2", all on the subjects of those two clusters only:

- clinical profile: one test per subject variable (`pair_clinical_comparison`);
- which variables tell the two clusters apart, together (`pair_regression`, a logistic regression
  with outcome "in cluster 1" among the subjects of the two clusters);
- how far apart the two clusters sit in the embedding (`centroid_separation`);
- where in the brain they differ (`difference_image`, the voxelwise difference of two maps).

Every subject variable is read from assets/metadata/participants.csv (the project's single
subject registry), never from the run's own metadata.csv - the same rule as
src.analysis.cluster_description. The statistics are a Mann-Whitney test per numeric variable and a
Fisher exact test per category, cluster 1 against cluster 2, with p corrected for all of them together.
"""

from __future__ import annotations

from dataclasses import dataclass

import nibabel as nib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from src.analysis.cluster_comparison import cluster_centroids, cluster_name
from src.analysis.cluster_description import CLUSTER_DESCRIPTION_VARIABLES
from src.analysis.cluster_drivers import RegressionResult, cluster_vs_rest_regression
from src.analysis.embedding_coloring import COLOR_MODES
from src.utils.participants import load_participants_registry

_CLUSTER_LABEL_COLUMN = COLOR_MODES["cluster_label"].column

# (name, label, registry column): the share of the lesion in each anatomical location, from the
# subject registry (2mm grid, one fixed grid for every subject).
LOCATION_FRACTIONS: list[tuple[str, str, str]] = [
    ("loc_infratentorial", "Infratentorial share", "location_infratentorial_2mm"),
    ("loc_subcortical_gray", "Subcortical gray share", "location_subcortical_gray_2mm"),
    ("loc_cortex_only", "Cortical share", "location_cortex_only_2mm"),
    ("loc_cortex_white_boundary", "Cortex-white matter boundary share", "location_cortex_white_boundary_2mm"),
    ("loc_white_matter_only", "White matter share", "location_white_matter_only_2mm"),
    ("loc_ventricle", "Ventricular share", "location_ventricle_2mm"),
    ("loc_unlabeled", "Unlabeled share", "location_unlabeled_2mm"),
]

# (name, label, registry column) of the categorical variables tested besides sex.
CATEGORICAL_VARIABLES: list[tuple[str, str, str]] = [
    ("sex", "Sex", "sex"),
    ("dataset", "Dataset", "dataset"),
    ("lesion_side", "Lesion side", "lesion_side"),
    ("location_dominant", "Dominant location", "location_dominant_2mm"),
]

REGRESSION_NUMERIC = ["age", "nihss", "log_lesion_volume", "loc_cortex_only", "loc_subcortical_gray", "loc_infratentorial"]
REGRESSION_CATEGORICAL = ["sex", "dataset"]
REGRESSION_LABELS: dict[str, str] = {
    "age": "age",
    "nihss": "NIHSS",
    "log_lesion_volume": "lesion volume (log10)",
    "loc_cortex_only": "cortical share",
    "loc_subcortical_gray": "subcortical gray share",
    "loc_infratentorial": "infratentorial share",
    "sex": "sex",
    "dataset": "dataset",
}

_SIGNIFICANT_COLOR = "#1a6bab"
_NOT_SIGNIFICANT_COLOR = "#9a9a9a"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)


@dataclass(frozen=True)
class PairFrame:
    """One row per subject of the two clusters. `frame` has subject_id, cluster_label and one
    column per variable (numeric ones as floats, categorical ones as strings or missing).
    `unregistered` lists, sorted, the subjects that have no row in the registry: they stay in the
    frame with a missing value everywhere, so the cluster sizes are the true ones."""

    frame: pd.DataFrame
    unregistered: list[str]


@dataclass(frozen=True)
class PairComparison:
    """numeric: variable, n_1, n_2, median_1, median_2, r, p, p_fdr. r is the rank-biserial
    correlation of a Mann-Whitney test, between -1 and 1, positive when cluster 1 has the higher
    values. categorical: variable, category, n_1, n_2, share_1, share_2, odds_ratio, p, p_fdr, with
    the odds ratio above 1 when the category is more common in cluster 1. p_fdr is corrected for
    every test of both tables together (Benjamini-Hochberg)."""

    numeric: pd.DataFrame
    categorical: pd.DataFrame


@dataclass(frozen=True)
class CentroidSeparation:
    """distance: Euclidean distance between the two centroids. radius_1/radius_2: mean distance of
    each cluster's subjects from its own centroid, the scale to read the distance against."""

    distance: float
    radius_1: float
    radius_2: float


def _require_two_clusters(metadata: pd.DataFrame, label_1: int, label_2: int) -> None:
    if _CLUSTER_LABEL_COLUMN not in metadata.columns:
        raise ValueError(f"this run's metadata has no {_CLUSTER_LABEL_COLUMN!r} column - not a clustering run")
    if label_1 == label_2:
        raise ValueError(f"the two clusters are the same cluster ({cluster_name(label_1)}): nothing to compare")
    present = set(int(value) for value in pd.unique(metadata[_CLUSTER_LABEL_COLUMN]))
    for label in (label_1, label_2):
        if label not in present:
            raise ValueError(f"no subjects with {_CLUSTER_LABEL_COLUMN}={label!r} in this run's metadata")


def pair_frame(metadata: pd.DataFrame, label_1: int, label_2: int) -> PairFrame:
    """The subjects of `label_1` and `label_2` with every variable of the comparison.

    Raises ValueError if the metadata is not a clustering run's, the two labels are equal, or one
    of them has no subjects."""
    _require_two_clusters(metadata, label_1, label_2)
    chosen = metadata.loc[metadata[_CLUSTER_LABEL_COLUMN].isin([label_1, label_2]), ["subject_id", _CLUSTER_LABEL_COLUMN]]
    subject_ids = chosen["subject_id"].to_numpy()

    registry = load_participants_registry().set_index("subject_id")
    needed = (
        [v.registry_column for v in CLUSTER_DESCRIPTION_VARIABLES if v.kind == "continuous"]
        + [column for _name, _label, column in LOCATION_FRACTIONS]
        + [column for _name, _label, column in CATEGORICAL_VARIABLES]
    )
    missing_columns = [column for column in needed if column not in registry.columns]
    if missing_columns:
        raise ValueError(f"the subject registry has no column(s) {missing_columns}")
    unregistered = sorted(set(subject_ids) - set(registry.index))
    aligned = registry.reindex(subject_ids)  # reindex: an unregistered subject becomes a row of missing values

    frame = pd.DataFrame({"subject_id": subject_ids, "cluster_label": chosen[_CLUSTER_LABEL_COLUMN].astype(int).to_numpy()})
    for variable in CLUSTER_DESCRIPTION_VARIABLES:
        if variable.kind == "continuous":
            frame[variable.name] = pd.to_numeric(aligned[variable.registry_column].to_numpy(), errors="coerce")
    for name, _label, column in LOCATION_FRACTIONS:
        frame[name] = pd.to_numeric(aligned[column].to_numpy(), errors="coerce")
    for name, _label, column in CATEGORICAL_VARIABLES:
        frame[name] = aligned[column].replace("", np.nan).to_numpy()
    volume = frame["lesion_volume_voxels"]
    frame["log_lesion_volume"] = np.log10(volume.where(volume > 0))
    return PairFrame(frame=frame.reset_index(drop=True), unregistered=unregistered)


def _numeric_rows(frame: pd.DataFrame, in_1: np.ndarray) -> pd.DataFrame:
    columns = [(v.name, v.label) for v in CLUSTER_DESCRIPTION_VARIABLES if v.kind == "continuous"]
    columns += [(name, label) for name, label, _column in LOCATION_FRACTIONS]
    rows = []
    for name, label in columns:
        group_1, group_2 = frame.loc[in_1, name].dropna(), frame.loc[~in_1, name].dropna()
        row = {
            "variable": label, "n_1": len(group_1), "n_2": len(group_2),
            "median_1": group_1.median() if len(group_1) else np.nan,
            "median_2": group_2.median() if len(group_2) else np.nan,
            "r": np.nan, "p": np.nan,
        }
        # A test needs at least two values per side; a side with fewer leaves r/p missing, never 0.
        if len(group_1) >= 2 and len(group_2) >= 2:
            u_statistic, row["p"] = stats.mannwhitneyu(group_1, group_2, alternative="two-sided")
            row["r"] = 2 * u_statistic / (len(group_1) * len(group_2)) - 1
        rows.append(row)
    return pd.DataFrame(rows)


def _categorical_rows(frame: pd.DataFrame, in_1: np.ndarray) -> pd.DataFrame:
    rows = []
    for name, label, _column in CATEGORICAL_VARIABLES:
        values = frame[name]
        valid = values.notna().to_numpy()
        for category in sorted(values[valid].unique()):
            has = (values == category).to_numpy()
            table = [
                [(has & in_1).sum(), (~has & valid & in_1).sum()],
                [(has & ~in_1).sum(), (~has & valid & ~in_1).sum()],
            ]
            n_1, n_2 = sum(table[0]), sum(table[1])
            row = {
                "variable": label, "category": category, "n_1": n_1, "n_2": n_2,
                "share_1": np.nan, "share_2": np.nan, "odds_ratio": np.nan, "p": np.nan,
            }
            if n_1 >= 2 and n_2 >= 2:
                row["share_1"], row["share_2"] = table[0][0] / n_1, table[1][0] / n_2
                row["odds_ratio"], row["p"] = stats.fisher_exact(table)
            rows.append(row)
    return pd.DataFrame(rows)


def pair_clinical_comparison(pair: PairFrame, label_1: int) -> PairComparison:
    """A Mann-Whitney test for every numeric variable and a Fisher exact test for every category
    of every categorical variable, cluster 1 against the other cluster of `pair`, with p corrected
    for all of them together (Benjamini-Hochberg). `label_1` says which cluster is "1".

    Raises ValueError if `label_1` is not one of the two clusters of `pair`, or if either is empty."""
    frame = pair.frame
    in_1 = (frame["cluster_label"] == label_1).to_numpy()
    if in_1.all() or not in_1.any():
        raise ValueError(f"cluster {cluster_name(label_1)} is empty or is the whole frame: nothing to compare")
    numeric = _numeric_rows(frame, in_1)
    categorical = _categorical_rows(frame, in_1)

    all_p = pd.concat([numeric["p"], categorical["p"]], ignore_index=True)
    valid = all_p.notna().to_numpy()
    adjusted = np.full(len(all_p), np.nan)
    if valid.any():
        adjusted[valid] = stats.false_discovery_control(all_p[valid].to_numpy(), method="bh")
    numeric["p_fdr"] = adjusted[: len(numeric)]
    categorical["p_fdr"] = adjusted[len(numeric):]
    return PairComparison(numeric=numeric, categorical=categorical)


def pair_regression(pair: PairFrame, label_1: int) -> RegressionResult:
    """Logistic regression of "the subject is in cluster 1" among the subjects of the two clusters,
    on REGRESSION_NUMERIC and REGRESSION_CATEGORICAL. An odds ratio above 1 means the variable makes
    a subject more likely to be in cluster 1 than in the other cluster.

    Raises ValueError for whatever cluster_vs_rest_regression refuses (too few subjects per term,
    collinear terms, perfect separation, ...): the message says why, it is never a fit that looks
    fine and is not."""
    frame = pair.frame
    return cluster_vs_rest_regression(
        frame, (frame["cluster_label"] == label_1).to_numpy(),
        numeric=REGRESSION_NUMERIC, categorical=REGRESSION_CATEGORICAL,
    )


def regression_term_label(term: str) -> str:
    """The reading of a coefficient name: "age" -> "età", "sex: M (ref. F)" -> "sex: M (ref. F)"."""
    name, separator, rest = term.partition(": ")
    if name not in REGRESSION_LABELS:
        raise ValueError(f"unknown regression term {term!r}, expected one of {sorted(REGRESSION_LABELS)}")
    return REGRESSION_LABELS[name] + separator + rest


def build_odds_ratio_figure(result: RegressionResult, label_1: int, label_2: int) -> go.Figure:
    """One point per term (the odds ratio) with its 95% confidence interval, on a log axis. Blue
    when the interval excludes 1, gray when it contains it."""
    table = result.coefficients.iloc[::-1]
    significant = ((table["ci_low"] > 1) | (table["ci_high"] < 1)).to_numpy()
    figure = go.Figure(
        go.Scatter(
            x=table["odds_ratio"], y=[regression_term_label(term) for term in table.index], mode="markers",
            marker={"size": 10, "color": [_SIGNIFICANT_COLOR if s else _NOT_SIGNIFICANT_COLOR for s in significant]},
            error_x={
                "type": "data", "symmetric": False, "thickness": 2, "width": 5,
                "array": (table["ci_high"] - table["odds_ratio"]).to_numpy(),
                "arrayminus": (table["odds_ratio"] - table["ci_low"]).to_numpy(),
                "color": "#7a7a7a",
            },
            hovertemplate="%{y}<br>odds ratio %{x:.2f}<extra></extra>",
        )
    )
    figure.add_vline(x=1, line={"color": "#555", "width": 1, "dash": "dash"})
    figure.update_xaxes(
        type="log", title=f"odds ratio  ←  more likely in cluster {cluster_name(label_2)} | "
        f"more likely in cluster {cluster_name(label_1)}  →",
        gridcolor="#ececec",
    )
    figure.update_yaxes(showgrid=False)
    figure.update_layout(
        height=120 + 46 * len(table), margin={"l": 10, "r": 10, "t": 20, "b": 10}, showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white", font={"family": _FONT_STACK, "color": "#333"},
    )
    return figure


def centroid_separation(embedding: np.ndarray, metadata: pd.DataFrame, label_1: int, label_2: int) -> CentroidSeparation:
    """Distance between the centroids of the two clusters in `embedding`, and the radius of each.

    `embedding` rows are the rows of `metadata`. Raises ValueError for a row-count mismatch, a
    metadata that is not a clustering run's, equal labels, or an empty cluster."""
    _require_two_clusters(metadata, label_1, label_2)
    if len(embedding) != len(metadata):
        raise ValueError(f"embedding has {len(embedding)} rows but metadata has {len(metadata)}")
    labels = metadata[_CLUSTER_LABEL_COLUMN].to_numpy()
    centroids = cluster_centroids(embedding, labels)
    centroid_1, centroid_2 = centroids.loc[label_1].to_numpy(), centroids.loc[label_2].to_numpy()
    radii = [
        float(np.linalg.norm(embedding[labels == label] - centroid, axis=1).mean())
        for label, centroid in ((label_1, centroid_1), (label_2, centroid_2))
    ]
    return CentroidSeparation(distance=float(np.linalg.norm(centroid_1 - centroid_2)), radius_1=radii[0], radius_2=radii[1])


def difference_image(image_1: nib.Nifti1Image, image_2: nib.Nifti1Image) -> nib.Nifti1Image:
    """`image_1` minus `image_2`, voxel by voxel, on their common grid. Raises ValueError if the
    two images are not on the same grid: subtracting them would compare different voxels."""
    if image_1.shape != image_2.shape or not np.allclose(image_1.affine, image_2.affine):
        raise ValueError(
            f"the two maps are not on the same grid (shapes {image_1.shape} and {image_2.shape}, or different affines)"
        )
    data = image_1.get_fdata(dtype=np.float32) - image_2.get_fdata(dtype=np.float32)
    return nib.Nifti1Image(data, image_1.affine)
