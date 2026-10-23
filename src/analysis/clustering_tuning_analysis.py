"""A stored clustering tuning run and what is measured on it, without refitting anything.

`clustering.py --fine_tuning true` writes `tuning_results.csv` (the indices of every combination), `clusterings.npz`
(every combination's labels) and the plots the sweep itself draws. The functions here read those files and compute what
the sweep does not write; src/analysis/clustering_tuning_evaluations.py runs them and writes their files, and
src/analysis/clustering_tuning_report.py lays the files out as report.md:

- agglomerative: cophenetic correlation and dendrogram jump per (metric, linkage), agreement between linkages,
  silhouette and Davies-Bouldin curves per n_clusters (the linkages other than `single`, on axes shared by the run);
- hdbscan / hdbscan_soft: the number of clusters, the share of the largest cluster and DBCV of every combination, the
  curves of those against min_cluster_size and the map of every column over min_cluster_size x min_samples;
- agglomerative / hdbscan / hdbscan_soft: the columns the sweep writes that can be recomputed from the stored labels
  (silhouette, Calinski-Harabasz, Davies-Bouldin of agglomerative; noise_fraction of the density methods).
"""

from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from sklearn.metrics import adjusted_rand_score

from src.analysis.clustering_tuning import (
    compute_clustering_metrics_metric_aware,
    compute_dendrogram_linkage,
    cophenetic_correlation,
    is_invalid_ward_metric_combo,
)
from src.analysis.dbcv import run_dbcv
from src.analysis.partition_shape import partition_shape

AGGLOMERATIVE = "agglomerative"
DENSITY_METHODS = ("hdbscan", "hdbscan_soft")
SUPPORTED_METHODS = (AGGLOMERATIVE, *DENSITY_METHODS)

# The columns each method sweeps, in the order clustering.py writes them into the keys of clusterings.npz.
SWEPT_COLUMNS: dict[str, tuple[str, ...]] = {
    AGGLOMERATIVE: ("n_clusters", "linkage", "metric"),
    "hdbscan": ("min_cluster_size", "min_samples"),
    "hdbscan_soft": ("min_cluster_size", "min_samples", "cluster_selection_method"),
}

ADP = "adp"


SINGLE_LINKAGE = "single"
LINKAGE_ORDER = ("ward", "average", "complete", SINGLE_LINKAGE)
METRIC_ORDER = ("euclidean", "cosine", "manhattan")


@dataclass(frozen=True)
class ClusteringTuningRun:
    """A clustering tuning run on disk: its method, the matrix it clustered, one row per combination
    and every combination's labels keyed like clusterings.npz."""

    run_dir: Path
    method: str
    input_path: Path
    results: pd.DataFrame
    labels: dict[str, np.ndarray]


def combo_key(row: dict, columns: tuple[str, ...]) -> str:
    """The clusterings.npz key of one tuning_results.csv row: `column=value` for each swept column."""
    return ",".join(f"{column}={row[column]}" for column in columns)


def read_run_config(run_dir: Path) -> dict:
    """The fenced ```json block of a clustering tuning run's config.md, with the fields this module needs.
    Raises FileNotFoundError / ValueError naming the file and the missing piece."""
    config_path = run_dir / "config.md"
    if not config_path.is_file():
        raise FileNotFoundError(f"tuning config not found: {config_path}")
    text = config_path.read_text()
    if "```json" not in text:
        raise ValueError(f"{config_path} has no ```json config block")
    config = json.loads(text.split("```json", 1)[1].split("```", 1)[0])
    for field in ("clustering_method", "input_path", "fine_tuning"):
        if field not in config:
            raise ValueError(f"{config_path}: config block is missing {field!r}")
    if config["fine_tuning"] is not True:
        raise ValueError(f"{config_path}: fine_tuning is {config['fine_tuning']!r}, this is not a tuning run")
    return config


def load_clustering_tuning_run(run_dir: Path) -> ClusteringTuningRun:
    """Loads tuning_results.csv, clusterings.npz and config.md of one run.

    config.md alone is not proof of what is in the directory (lessons_learned.md #18): the keys of
    clusterings.npz must be exactly those of the rows of tuning_results.csv, or this raises.
    """
    run_dir = Path(run_dir)
    config = read_run_config(run_dir)
    method = config["clustering_method"]
    if method == "adp":
        raise ValueError(f"{run_dir}: adp is not analysed here - it has its own diagnostics (docs/guides/clustering.md)")
    if method not in SUPPORTED_METHODS:
        raise ValueError(f"{run_dir}: unsupported clustering_method {method!r} - supported: {list(SUPPORTED_METHODS)}")

    for name in ("tuning_results.csv", "clusterings.npz"):
        if not (run_dir / name).is_file():
            raise FileNotFoundError(f"{run_dir / name} not found (clusterings.npz needs save_tuning_clusterings=true)")
    results = pd.read_csv(run_dir / "tuning_results.csv")
    columns = SWEPT_COLUMNS[method]
    missing = [column for column in columns if column not in results.columns]
    if missing:
        raise ValueError(f"{run_dir / 'tuning_results.csv'} has no column(s) {missing} - expected {list(columns)}")

    expected = {combo_key(row, columns) for row in results.to_dict("records")}
    with np.load(run_dir / "clusterings.npz") as archive:
        labels = {key: archive[key] for key in archive.files}
    if set(labels) != expected:
        raise ValueError(
            f"{run_dir}: clusterings.npz does not match tuning_results.csv - {len(labels)} arrays against "
            f"{len(expected)} rows (a directory reused by a run with another grid?)"
        )
    return ClusteringTuningRun(run_dir, method, Path(config["input_path"]), results, labels)


def dendrogram_jump(linkage_matrix: np.ndarray, k_values: range) -> dict[int, float]:
    """Height of the merge from k to k-1 clusters divided by that of the merge from k+1 to k, for each k.
    Close to 1 the tree has no natural cut at k; the larger it is, the sharper the cut.

    Raises ValueError if a k needs more merges than the tree has, or if the merge from k+1 to k happens at
    height 0 (duplicated subjects), where the ratio is undefined.
    """
    n_merges = len(linkage_matrix)
    jumps = {}
    for k in k_values:
        if k < 2 or k > n_merges:
            raise ValueError(f"k={k} is outside 2..{n_merges} (a tree of {n_merges + 1} subjects)")
        denominator = linkage_matrix[-k, 2]
        if denominator == 0:
            raise ValueError(f"the merge from {k + 1} to {k} clusters is at height 0: the jump at k={k} is undefined")
        jumps[k] = float(linkage_matrix[-(k - 1), 2] / denominator)
    return jumps


def _valid_metric_linkage_pairs(run: ClusteringTuningRun, caller: str) -> list[dict]:
    """The `{"linkage", "metric"}` params of every (metric, linkage) of an agglomerative run that sklearn accepts:
    a ward row with a non-euclidean metric is invalid and absent from the run, so it is skipped."""
    if run.method != AGGLOMERATIVE:
        raise ValueError(f"{caller} needs an agglomerative run, got {run.method!r}")
    pairs = run.results[["metric", "linkage"]].drop_duplicates().itertuples(index=False)
    params = [{"linkage": linkage, "metric": metric} for metric, linkage in pairs]
    return [p for p in params if not is_invalid_ward_metric_combo(p)]


def cophenetic_table(run: ClusteringTuningRun, X: np.ndarray, distance_cache: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    """Cophenetic correlation of every valid (metric, linkage) of an agglomerative run: one row per pair,
    columns `metric`, `linkage`, `cophenetic_correlation`."""
    distance_cache = {} if distance_cache is None else distance_cache
    rows = [
        {"metric": p["metric"], "linkage": p["linkage"], "cophenetic_correlation": cophenetic_correlation(X, p, distance_cache)}
        for p in _valid_metric_linkage_pairs(run, "cophenetic_table")
    ]
    return pd.DataFrame(rows)


def jump_table(
    run: ClusteringTuningRun, X: np.ndarray, k_values: range, distance_cache: dict[str, np.ndarray] | None = None
) -> pd.DataFrame:
    """Dendrogram jump of every valid (metric, linkage) of an agglomerative run at each k of `k_values`: one row
    per (metric, linkage, n_clusters), columns `metric`, `linkage`, `n_clusters`, `jump`."""
    distance_cache = {} if distance_cache is None else distance_cache
    rows = []
    for p in _valid_metric_linkage_pairs(run, "jump_table"):
        jumps = dendrogram_jump(compute_dendrogram_linkage(X, p, distance_cache), k_values)
        rows += [{"metric": p["metric"], "linkage": p["linkage"], "n_clusters": k, "jump": jump} for k, jump in jumps.items()]
    return pd.DataFrame(rows)


def linkage_agreement(run: ClusteringTuningRun) -> pd.DataFrame:
    """Adjusted Rand index between the partitions of every two linkages of an agglomerative run, at each `n_clusters`
    and `metric`. One row per (metric, n_clusters, linkage_a, linkage_b), with the linkages in LINKAGE_ORDER; a linkage
    that was not swept for that metric (ward with a non-euclidean one) has no pair. Computed from the stored labels."""
    if run.method != AGGLOMERATIVE:
        raise ValueError(f"linkage_agreement needs an agglomerative run, got {run.method!r}")
    columns = SWEPT_COLUMNS[AGGLOMERATIVE]
    rows = []
    for (metric, k), group in run.results.groupby(["metric", "n_clusters"], sort=True):
        labels = {row["linkage"]: run.labels[combo_key(row, columns)] for row in group.to_dict("records")}
        for linkage_a, linkage_b in itertools.combinations(ordered(labels, LINKAGE_ORDER), 2):
            ari = adjusted_rand_score(labels[linkage_a], labels[linkage_b])
            rows.append({"metric": metric, "n_clusters": int(k), "linkage_a": linkage_a, "linkage_b": linkage_b, "ari": float(ari)})
    return pd.DataFrame(rows, columns=["metric", "n_clusters", "linkage_a", "linkage_b", "ari"])


def ordered(values, preferred: tuple[str, ...]) -> list[str]:
    """`values` without repeats: those in `preferred` first, in its order, then any other, sorted - none is dropped."""
    present = set(values)
    return [*(value for value in preferred if value in present), *sorted(present - set(preferred))]


def silhouette_zoom_limits(silhouette: pd.Series) -> tuple[float, float]:
    """The y-limits of a panel fitted to the data of one column: its range plus 8% on each side (0.05 if it is flat)."""
    values = silhouette.dropna()
    if values.empty:
        raise ValueError("no silhouette to fit the axis to")
    low, high = float(values.min()), float(values.max())
    padding = 0.08 * (high - low) or 0.05
    return low - padding, high + padding


def curves_subset(results: pd.DataFrame, metric: str) -> pd.DataFrame:
    """The rows of one `metric` for the linkages other than `single`, the only ones the curves figures draw."""
    return results[(results["metric"] == metric) & (results["linkage"] != SINGLE_LINKAGE)]


def k_curves_targets(results: pd.DataFrame) -> list[str]:
    """The metrics that get a curves figure in an agglomerative run, in METRIC_ORDER: those with a linkage other than `single`."""
    return [metric for metric in ordered(results["metric"].unique(), METRIC_ORDER) if not curves_subset(results, metric).empty]


def k_curves_file_name(metric: str) -> str:
    return f"k_curves_metric={metric}.png"


def run_axis_limits(results: pd.DataFrame, column: str) -> tuple[float, float]:
    """The y-limits of `column` shared by every curves figure of a run, so the figures compare at a glance: the lowest
    low and the highest high of the limits fitted to each metric (silhouette_zoom_limits), the low rounded down and
    the high rounded up to 0.1. Raises if no figure has a value of `column`."""
    fitted = [
        silhouette_zoom_limits(values)
        for metric in k_curves_targets(results)
        if not (values := curves_subset(results, metric)[column].dropna()).empty
    ]
    if not fitted:
        raise ValueError(f"no {column} in any curves figure of the run to fit the axis to")
    low, high = min(low for low, _ in fitted), max(high for _, high in fitted)
    return math.floor(round(low * 10, 9)) / 10, math.ceil(round(high * 10, 9)) / 10


def _plot_curves(axis, subset: pd.DataFrame, column: str, label: str) -> None:
    for linkage in ordered(subset["linkage"].unique(), LINKAGE_ORDER):
        group = subset[subset["linkage"] == linkage].sort_values("n_clusters")
        axis.plot(group["n_clusters"], group[column], marker="o", markersize=3.5, label=linkage)
    axis.set_xticks(range(2, int(subset["n_clusters"].max()) + 1, 2))
    axis.tick_params(labelsize=8)
    axis.set_xlabel("n_clusters")
    axis.set_ylabel(label)
    axis.grid(alpha=0.3)


def k_curves_figure(results: pd.DataFrame, metric: str) -> Figure:
    """Silhouette and Davies-Bouldin per n_clusters, one line per linkage other than `single`, for one `metric` of an
    agglomerative run. The axes are those of the whole run (run_axis_limits), the same in every metric's figure.
    Davies-Bouldin is NaN for a non-euclidean metric: its panel is left out."""
    subset = curves_subset(results, metric)
    if subset.empty:
        raise ValueError(f"no row of the run has metric={metric!r} and a linkage other than single")
    has_davies_bouldin = subset["davies_bouldin"].notna().any()
    figure = Figure(figsize=(12 if has_davies_bouldin else 6, 4.5))
    axes = figure.subplots(1, 2) if has_davies_bouldin else [figure.subplots()]
    _plot_curves(axes[0], subset, "silhouette", "Silhouette (higher = better)")
    axes[0].set_ylim(*run_axis_limits(results, "silhouette"))
    axes[0].set_title("silhouette", fontsize=10)
    if has_davies_bouldin:
        _plot_curves(axes[1], subset, "davies_bouldin", "Davies-Bouldin (lower = better)")
        axes[1].set_ylim(*run_axis_limits(results, "davies_bouldin"))
        axes[1].set_title("Davies-Bouldin", fontsize=10)
    axes[0].legend(title="linkage", fontsize=8)
    figure.suptitle(f"Agglomerative, metric={metric}")
    figure.tight_layout()
    return figure


def density_metrics(run: ClusteringTuningRun, X: np.ndarray) -> pd.DataFrame:
    """tuning_results.csv of an hdbscan / hdbscan_soft run with `n_clusters_found`, `largest_cluster_share` (over all
    subjects, noise included) and `dbcv` (src/analysis/dbcv.py, on `X`, the matrix the run clustered), all computed
    from the stored labels. `largest_cluster_share` is NaN when every subject is noise and `dbcv` when there are
    fewer than 2 clusters.

    If the run also wrote `n_clusters_found` the two must agree, or this raises (a clusterings.npz that does
    not belong to this tuning_results.csv). Raises ValueError if `X` has not one row per subject.
    """
    if run.method not in DENSITY_METHODS:
        raise ValueError(f"density_metrics needs an hdbscan or hdbscan_soft run, got {run.method!r}")
    columns = SWEPT_COLUMNS[run.method]
    n_clusters, largest_share, dbcv_scores = [], [], []
    for row in run.results.to_dict("records"):
        labels = run.labels[combo_key(row, columns)]
        shape = partition_shape(labels)
        n_clusters.append(shape.n_clusters)
        largest_share.append(shape.largest_cluster_share)
        dbcv_scores.append(run_dbcv(X, labels, row).score)

    metrics = run.results.copy()
    if "n_clusters_found" in metrics.columns and not np.array_equal(metrics["n_clusters_found"].to_numpy(), n_clusters):
        raise ValueError(f"{run.run_dir}: n_clusters_found in tuning_results.csv differs from the clusters in clusterings.npz")
    metrics["n_clusters_found"] = n_clusters
    metrics["largest_cluster_share"] = largest_share
    metrics["dbcv"] = dbcv_scores
    return metrics


DENSITY_METRICS_FILE = "density_metrics.csv"

# The columns of density_metrics.csv drawn in the map and in the curves, in this order (those the run has).
DENSITY_MAP_COLUMNS = ("dbcv", "noise_fraction", "largest_cluster_share", "n_clusters_found", "membership_mean", "persistence_mean")
DENSITY_CURVE_COLUMNS = (
    ("dbcv", "DBCV (higher = better)"),
    ("noise_fraction", "noise_fraction"),
    ("largest_cluster_share", "largest_cluster_share"),
    ("n_clusters_found", "n_clusters_found"),
)
SELECTION_COLUMN = "cluster_selection_method"


def read_density_metrics(run_dir: Path) -> pd.DataFrame:
    """density_metrics.csv of a run folder, the table the density evaluations after `density_metrics` read.
    Raises FileNotFoundError naming the evaluation to run first."""
    path = Path(run_dir) / DENSITY_METRICS_FILE
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found: run the `density_metrics` evaluation before the ones that read it")
    return pd.read_csv(path)


def density_groups(metrics: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """The rows of a density table by `cluster_selection_method` (hdbscan_soft), or a single group keyed "" (hdbscan)."""
    if SELECTION_COLUMN in metrics.columns:
        return {str(name): group for name, group in metrics.groupby(SELECTION_COLUMN)}
    return {"": metrics}


def dbcv_curves_figures(metrics: pd.DataFrame) -> dict[str, Figure]:
    """DBCV, noise_fraction, largest_cluster_share and n_clusters_found against min_cluster_size, one line per
    min_samples, every combination (no filter on the noise: it is one of the panels). A point is missing where the
    combination has fewer than 2 clusters and DBCV is undefined (not 0). One figure per `cluster_selection_method`
    for hdbscan_soft (keyed by it), a single one keyed "" for hdbscan."""
    figures = {}
    sizes = sorted(metrics["min_cluster_size"].unique())
    for name, group in density_groups(metrics).items():
        figure = Figure(figsize=(17, 3.8))
        axes = figure.subplots(1, len(DENSITY_CURVE_COLUMNS), sharex=True)
        for axis, (column, label) in zip(axes, DENSITY_CURVE_COLUMNS):
            for min_samples, line in group.groupby("min_samples"):
                line = line.sort_values("min_cluster_size")
                axis.plot(line["min_cluster_size"], line[column], marker="o", markersize=4, label=f"min_samples={min_samples}")
            axis.set_xscale("log")
            axis.set_xticks(sizes, sizes)
            axis.minorticks_off()
            axis.tick_params(labelsize=8)
            axis.set_xlabel("min_cluster_size")
            axis.set_title(label, fontsize=10)
            axis.grid(alpha=0.3)
        axes[0].axhline(0, color="black", linewidth=0.6)
        axes[0].legend(fontsize=7)
        figure.suptitle(f"{name}: a missing DBCV point means fewer than 2 clusters" if name else "a missing DBCV point means fewer than 2 clusters", fontsize=9)
        figure.tight_layout()
        figures[name] = figure
    return figures


def recomputed_internal_metrics(run: ClusteringTuningRun, X: np.ndarray, distance_cache: dict[str, np.ndarray] | None = None) -> pd.DataFrame:
    """tuning_results.csv of the run with the columns the sweep computes from the labels recomputed from clusterings.npz:
    silhouette, calinski_harabasz and davies_bouldin for agglomerative (scored under the row's own `metric`, the two
    euclidean-only ones NaN under another), noise_fraction for the density methods. The same functions the sweep uses.
    Columns that come from the fit (`membership_mean`, `persistence_mean`) are left as they are."""
    columns = SWEPT_COLUMNS[run.method]
    distance_cache = {} if distance_cache is None else distance_cache
    rows = []
    for row in run.results.to_dict("records"):
        labels = run.labels[combo_key(row, columns)]
        if run.method == AGGLOMERATIVE:
            rows.append(compute_clustering_metrics_metric_aware(X, labels, row["metric"], distance_cache))
        else:
            rows.append({"noise_fraction": partition_shape(labels).noise_fraction})
    recomputed = pd.DataFrame(rows, index=run.results.index)
    metrics = run.results.copy()
    for column in recomputed.columns:
        if column not in metrics.columns:
            raise ValueError(f"{run.run_dir / 'tuning_results.csv'} has no column {column!r}: this run did not write it, nothing to rewrite")
        metrics[column] = recomputed[column]
    return metrics
