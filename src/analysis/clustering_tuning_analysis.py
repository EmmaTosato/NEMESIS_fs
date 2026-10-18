"""Analyses of a stored clustering tuning run, computed after the sweep.

`clustering.py --fine_tuning true` writes `tuning_results.csv` (the indices of every combination),
`clusterings.npz` (every combination's labels) and the plots the sweep itself draws. What it does
not write is read from those files here, without refitting anything:

- agglomerative: cophenetic correlation and dendrogram jump per (metric, linkage), silhouette and
  Davies-Bouldin curves per n_clusters;
- hdbscan / hdbscan_soft: the share of the largest cluster, the `usable` flag, and the
  silhouette/Davies-Bouldin curves restricted to combinations with little noise.

adp is not handled: it has its own diagnostics (docs/guides/clustering.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from src.analysis.clustering_tuning import compute_dendrogram_linkage, cophenetic_correlation, is_invalid_ward_metric_combo

AGGLOMERATIVE = "agglomerative"
DENSITY_METHODS = ("hdbscan", "hdbscan_soft")
SUPPORTED_METHODS = (AGGLOMERATIVE, *DENSITY_METHODS)

# The columns each method sweeps, in the order clustering.py writes them into the keys of clusterings.npz.
SWEPT_COLUMNS: dict[str, tuple[str, ...]] = {
    AGGLOMERATIVE: ("n_clusters", "linkage", "metric"),
    "hdbscan": ("min_cluster_size", "min_samples"),
    "hdbscan_soft": ("min_cluster_size", "min_samples", "cluster_selection_method"),
}

NOISE_LABEL = -1


@dataclass(frozen=True)
class UsableCriteria:
    """A combination is `usable` if it has between `min_clusters` and `max_clusters` clusters, at most
    `max_noise_fraction` of the subjects in the noise and at most `max_largest_cluster_share` of them in
    the largest cluster. A practical filter, not a validity index."""

    min_clusters: int
    max_clusters: int
    max_noise_fraction: float
    max_largest_cluster_share: float


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


def agglomerative_analysis(run: ClusteringTuningRun, X: np.ndarray, k_values: range) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cophenetic correlation and dendrogram jump of every valid (metric, linkage) of an agglomerative run.

    Returns (cophenetic, jump): `cophenetic` has one row per (metric, linkage) and the column
    `cophenetic_correlation`; `jump` one row per (metric, linkage, n_clusters) and the column `jump`.
    A ward row with a non-euclidean metric is invalid in sklearn and absent from the run, so it is skipped.
    """
    if run.method != AGGLOMERATIVE:
        raise ValueError(f"agglomerative_analysis needs an agglomerative run, got {run.method!r}")
    cophenetic_rows, jump_rows = [], []
    distance_cache: dict[str, np.ndarray] = {}
    pairs = run.results[["metric", "linkage"]].drop_duplicates().itertuples(index=False)
    for metric, linkage in pairs:
        params = {"linkage": linkage, "metric": metric}
        if is_invalid_ward_metric_combo(params):
            continue
        cophenetic_rows.append(
            {"metric": metric, "linkage": linkage, "cophenetic_correlation": cophenetic_correlation(X, params, distance_cache)}
        )
        jumps = dendrogram_jump(compute_dendrogram_linkage(X, params, distance_cache), k_values)
        jump_rows += [{"metric": metric, "linkage": linkage, "n_clusters": k, "jump": jump} for k, jump in jumps.items()]
    return pd.DataFrame(cophenetic_rows), pd.DataFrame(jump_rows)


def k_curves_figure(results: pd.DataFrame, metric: str, excluded_linkages: tuple[str, ...] = ("single",)) -> Figure:
    """Silhouette and Davies-Bouldin per n_clusters, one line per linkage, for one `metric` of an agglomerative run.
    Davies-Bouldin is NaN for a non-euclidean metric: its panel is then empty."""
    subset = results[(results["metric"] == metric) & ~results["linkage"].isin(excluded_linkages)]
    if subset.empty:
        raise ValueError(f"no row of the run has metric={metric!r} (after excluding {list(excluded_linkages)})")
    figure = Figure(figsize=(13, 4.5))
    axes = figure.subplots(1, 2, sharex=True)
    for axis, column, label in zip(axes, ("silhouette", "davies_bouldin"), ("Silhouette (higher = better)", "Davies-Bouldin (lower = better)")):
        for linkage, group in subset.groupby("linkage"):
            group = group.sort_values("n_clusters")
            axis.plot(group["n_clusters"], group[column], marker="o", markersize=4, label=linkage)
        axis.set_xlabel("n_clusters")
        axis.set_ylabel(label)
        axis.grid(alpha=0.3)
    axes[0].legend(title="linkage")
    figure.suptitle(f"Agglomerative, metric={metric}")
    figure.tight_layout()
    return figure


def density_candidates(run: ClusteringTuningRun, criteria: UsableCriteria) -> pd.DataFrame:
    """tuning_results.csv of an hdbscan / hdbscan_soft run with `largest_cluster_share` (over all subjects,
    noise included) and the boolean `usable`, both computed from the stored labels.

    The number of clusters is counted from the labels; if the run also wrote `n_clusters_found` the two must
    agree, or this raises (a clusterings.npz that does not belong to this tuning_results.csv).
    """
    if run.method not in DENSITY_METHODS:
        raise ValueError(f"density_candidates needs an hdbscan or hdbscan_soft run, got {run.method!r}")
    columns = SWEPT_COLUMNS[run.method]
    n_clusters, largest_share = [], []
    for row in run.results.to_dict("records"):
        labels = run.labels[combo_key(row, columns)]
        found = labels[labels != NOISE_LABEL]
        n_clusters.append(len(np.unique(found)))
        largest_share.append(float(np.bincount(found).max() / len(labels)) if len(found) else float("nan"))

    candidates = run.results.copy()
    if "n_clusters_found" in candidates.columns and not np.array_equal(candidates["n_clusters_found"].to_numpy(), n_clusters):
        raise ValueError(f"{run.run_dir}: n_clusters_found in tuning_results.csv differs from the clusters in clusterings.npz")
    candidates["n_clusters_found"] = n_clusters
    candidates["largest_cluster_share"] = largest_share
    candidates["usable"] = (
        candidates["n_clusters_found"].between(criteria.min_clusters, criteria.max_clusters)
        & (candidates["noise_fraction"] <= criteria.max_noise_fraction)
        & (candidates["largest_cluster_share"] <= criteria.max_largest_cluster_share)
    )
    return candidates


def noise_filtered_curves_figures(candidates: pd.DataFrame, max_noise_fraction: float) -> tuple[dict[str, Figure], list[str]]:
    """Silhouette and Davies-Bouldin against min_cluster_size, one line per min_samples, keeping only the
    combinations with `noise_fraction` at most `max_noise_fraction`: a silhouette that is high only because the
    hardest subjects were thrown into the noise does not appear.

    One figure per `cluster_selection_method` for hdbscan_soft (keyed by it), a single one keyed "" for hdbscan.
    Returns (figures, without_figure): a group where no combination is under the limit (the `leaf` selection
    never goes below 15% noise; a run without structure may have none at all) has no figure and is listed in
    `without_figure`. That is a finding about the run, not an error: `figures` may then be empty.
    """
    groups = dict(tuple(candidates.groupby("cluster_selection_method"))) if "cluster_selection_method" in candidates.columns else {"": candidates}
    figures, without_figure = {}, []
    for name, group in groups.items():
        kept = group[group["noise_fraction"] <= max_noise_fraction]
        if kept.empty:
            without_figure.append(name)
            continue
        figure = Figure(figsize=(11, 4))
        axes = figure.subplots(1, 2, sharex=True)
        for axis, column, label in zip(axes, ("silhouette", "davies_bouldin"), ("Silhouette (higher = better)", "Davies-Bouldin (lower = better)")):
            for min_samples, line in kept.groupby("min_samples"):
                line = line.sort_values("min_cluster_size")
                axis.plot(line["min_cluster_size"], line[column], marker="o", markersize=4, label=min_samples)
            axis.set_xscale("log")
            sizes = sorted(candidates["min_cluster_size"].unique())
            axis.set_xticks(sizes, sizes)
            axis.minorticks_off()
            axis.set_xlabel("min_cluster_size")
            axis.set_ylabel(label)
            axis.grid(alpha=0.3)
        axes[0].legend(title="min_samples")
        title = f"noise_fraction <= {max_noise_fraction}: {len(kept)} of {len(group)} combinations"
        figure.suptitle(f"{name}, {title}" if name else title)
        figure.tight_layout()
        figures[name] = figure
    return figures, without_figure
