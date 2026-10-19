"""Analyses of a stored clustering tuning run, computed after the sweep.

`clustering.py --fine_tuning true` writes `tuning_results.csv` (the indices of every combination),
`clusterings.npz` (every combination's labels) and the plots the sweep itself draws. What it does
not write is read from those files here, without refitting anything:

- every method (adp included): `tuning_report_markdown`, the tables of `tuning_results.csv` as they are
  (agglomerative: one table per metric and linkage, with the silhouette bands of a published convention);
- agglomerative: cophenetic correlation and dendrogram jump per (metric, linkage), silhouette and
  Davies-Bouldin curves per n_clusters (`single` in a figure of its own);
- hdbscan / hdbscan_soft: the number of clusters and the share of the largest cluster of every
  combination, and the silhouette/Davies-Bouldin curves restricted to combinations with little noise.

Nothing here classifies a combination as good, usable or stable with a threshold of ours: the outputs are measurements,
and the only bands are the silhouette ones of a published convention (SILHOUETTE_BANDS), labelled as such.

adp has its own diagnostics (docs/guides/clustering.md) and only gets the report.
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

ADP = "adp"
REPORT_METHODS = (AGGLOMERATIVE, *DENSITY_METHODS, ADP)

# The report of a run, for the methods other than agglomerative (which has its own layout): one table per value of the
# grouping column (a silhouette is not comparable across metrics or across selection methods), the swept columns first.
REPORT_GROUP_COLUMN: dict[str, str | None] = {"hdbscan": None, "hdbscan_soft": "cluster_selection_method", ADP: "metric"}
REPORT_KEY_COLUMNS: dict[str, tuple[str, ...]] = {
    "hdbscan": ("min_cluster_size", "min_samples"),
    "hdbscan_soft": ("min_cluster_size", "min_samples"),
    ADP: ("Z",),
}
REPORT_COUNT_COLUMNS = ("n_clusters", "min_cluster_size", "min_samples", "n_clusters_found", "n_small_clusters")
REPORT_TERMS: dict[str, str] = {
    "silhouette": "-1..1, più alto meglio.",
    "davies_bouldin": "più basso meglio.",
    "calinski_harabasz": "più alto meglio, cresce con il numero di cluster.",
    "noise_fraction": "quota dei soggetti fuori da ogni zona densa; è esclusa dagli indici.",
    "n_clusters_found": "numero di cluster, rumore escluso.",
    "largest_cluster_share": "quota dei soggetti, rumore compreso, nel cluster più grande.",
    "n_small_clusters": "cluster con meno di 10 soggetti.",
    "id_2nn": "dimensione intrinseca stimata, costante per `metric`.",
    "ari_vs_prev_z": "ARI, sui soli soggetti clusterizzati, contro il `Z` immediatamente più basso.",
    "membership_mean": "media, sui soggetti non rumore, della probabilità di stare nel proprio cluster.",
    "membership_share_below_half": "quota dei soggetti non rumore con probabilità sotto 0.5.",
    "persistence_mean": "media della stabilità dei cluster (0 effimeri, 1 stabili).",
}

# Silhouette bands: the convention of Kaufman & Rousseeuw (1990, "Finding Groups in Data"), not a result of ours. The
# sources that quote it differ on the edges (0.25/0.26, 0.50/0.51): a silhouette is rounded to 2 decimals and falls in
# the first band, from the top, whose lower edge it reaches. A negative silhouette is outside every band.
SILHOUETTE_BANDS: tuple[tuple[str, str, float], ...] = (
    ("0.71-1.00", "struttura forte", 0.71),
    ("0.51-0.70", "ragionevole", 0.51),
    ("0.26-0.50", "debole, forse artificiale", 0.26),
    ("0.00-0.25", "nessuna struttura sostanziale", 0.0),
)
CONVENTION_LINES = tuple(sorted(lower_edge for _, _, lower_edge in SILHOUETTE_BANDS))
SILHOUETTE_BANDS_TERM = (
    "**Fasce della silhouette**: convenzione di Kaufman & Rousseeuw (1990), *Finding Groups in Data*: 0.71-1.00 struttura "
    "forte, 0.51-0.70 ragionevole, 0.26-0.50 debole (forse artificiale), fino a 0.25 nessuna struttura sostanziale. Gli "
    "estremi variano tra le fonti; qui la silhouette è arrotondata a 2 decimali. Le fasce descrivono la combinazione, non "
    "scelgono `n_clusters`, e non si confrontano tra `metric` diverse. Per Davies-Bouldin e Calinski-Harabasz non esiste "
    "una convenzione con fonte: solo i valori."
)

COPHENETIC_TERM = (
    "correlazione tra le distanze vere e quelle dell'albero (da -1 a 1, vicino a 1 l'albero è fedele). Una per `metric` e "
    "`linkage`: non si confronta tra `metric` diverse. Nessuna fascia con fonte in letteratura."
)
JUMP_TERM = (
    "altezza della fusione da k a k-1 divisa per quella da k+1 a k. Vicino a 1 non c'è un taglio naturale a k; più è alto, "
    "più il taglio è netto. Le altezze sono in unità diverse per ogni linkage, quindi i linkage non si confrontano. "
    "Nessuna fascia con fonte in letteratura."
)
SINGLE_LINKAGE = "single"
LINKAGE_ORDER = ("ward", "average", "complete", SINGLE_LINKAGE)
METRIC_ORDER = ("euclidean", "cosine", "manhattan")
AGGLOMERATIVE_REPORT_COLUMNS = ("n_clusters", "linkage", "metric", "silhouette", "davies_bouldin", "calinski_harabasz")


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


def _ordered(values, preferred: tuple[str, ...]) -> list[str]:
    """`values` without repeats: those in `preferred` first, in its order, then any other, sorted - none is dropped."""
    present = set(values)
    return [*(value for value in preferred if value in present), *sorted(present - set(preferred))]


def silhouette_band(value: float) -> str | None:
    """The band of SILHOUETTE_BANDS a silhouette falls in, or None for a negative one. Raises for NaN."""
    if np.isnan(value):
        raise ValueError("a NaN silhouette has no band")
    if value < 0:
        return None
    rounded = round(float(value), 2)
    return next(name for name, _, lower_edge in SILHOUETTE_BANDS if rounded >= lower_edge)


def silhouette_zoom_limits(silhouette: pd.Series) -> tuple[float, float]:
    """The y-limits of the silhouette panel fitted to the data: its range plus 8% on each side (0.05 if it is flat)."""
    values = silhouette.dropna()
    if values.empty:
        raise ValueError("no silhouette to fit the axis to")
    low, high = float(values.min()), float(values.max())
    padding = 0.08 * (high - low) or 0.05
    return low - padding, high + padding


def convention_lines_caption(subset: pd.DataFrame) -> str:
    """Says which dashed lines of CONVENTION_LINES a silhouette panel fitted to `subset` shows and which fall outside."""
    low, high = silhouette_zoom_limits(subset["silhouette"])
    visible = [line for line in CONVENTION_LINES if low <= line <= high]
    hidden = [line for line in CONVENTION_LINES if line not in visible]
    as_text = lambda lines: ", ".join(f"{line:.2f}" for line in lines) or "nessuna"
    return (
        "Linee tratteggiate sulla silhouette: soglie della convenzione di Kaufman & Rousseeuw (1990). Asse fisso: tutte "
        f"visibili. Asse adattato ai dati: visibili {as_text(visible)}, fuori asse {as_text(hidden)}."
    )


def _curves_subset(results: pd.DataFrame, metric: str, single: bool) -> pd.DataFrame:
    is_single = results["linkage"] == SINGLE_LINKAGE
    return results[(results["metric"] == metric) & (is_single if single else ~is_single)]


def k_curves_targets(results: pd.DataFrame) -> list[tuple[str, bool]]:
    """The `(metric, single)` of every curves figure of an agglomerative run: per metric one figure for the linkages
    other than `single` and, if the run has it, one for `single` alone (its silhouette goes far below the others)."""
    return [
        (metric, single)
        for metric in _ordered(results["metric"].unique(), METRIC_ORDER)
        for single in (False, True)
        if not _curves_subset(results, metric, single).empty
    ]


def k_curves_file_name(metric: str, single: bool) -> str:
    return f"k_curves_{'single_' if single else ''}metric={metric}.png"


def _plot_curves(axis, subset: pd.DataFrame, column: str, label: str) -> None:
    for linkage in _ordered(subset["linkage"].unique(), LINKAGE_ORDER):
        group = subset[subset["linkage"] == linkage].sort_values("n_clusters")
        axis.plot(group["n_clusters"], group[column], marker="o", markersize=3.5, label=linkage)
    axis.set_xticks(range(2, int(subset["n_clusters"].max()) + 1, 2))
    axis.tick_params(labelsize=8)
    axis.set_xlabel("n_clusters")
    axis.set_ylabel(label)
    axis.grid(alpha=0.3)


def _draw_convention_lines(axis) -> None:
    low, high = axis.get_ylim()
    for line in (line for line in CONVENTION_LINES if low <= line <= high):
        axis.axhline(line, color="grey", linestyle="--", linewidth=0.9)
        axis.text(axis.get_xlim()[1], line, f" {line:.2f}", va="center", fontsize=7, color="grey")


def k_curves_figure(results: pd.DataFrame, metric: str, single: bool) -> Figure:
    """Silhouette and Davies-Bouldin per n_clusters, one line per linkage, for one `metric` of an agglomerative run:
    the silhouette on a fixed axis (-1..1), on an axis fitted to the data, and Davies-Bouldin. The linkages other than
    `single` (`single=False`) or `single` alone (`single=True`). The silhouette panels carry the dashed lines of
    CONVENTION_LINES that fall inside them. Davies-Bouldin is NaN for a non-euclidean metric: its panel is left out."""
    subset = _curves_subset(results, metric, single)
    if subset.empty:
        raise ValueError(f"no row of the run has metric={metric!r} and {'the single linkage' if single else 'a linkage other than single'}")
    has_davies_bouldin = subset["davies_bouldin"].notna().any()
    figure = Figure(figsize=(18 if has_davies_bouldin else 12, 4.5))
    axes = figure.subplots(1, 3 if has_davies_bouldin else 2)
    silhouette_label = "Silhouette (higher = better)"
    _plot_curves(axes[0], subset, "silhouette", silhouette_label)
    axes[0].set_ylim(-1, 1)
    axes[0].set_title("silhouette, fixed axis (-1 to 1)", fontsize=10)
    _plot_curves(axes[1], subset, "silhouette", silhouette_label)
    axes[1].set_ylim(*silhouette_zoom_limits(subset["silhouette"]))
    axes[1].set_title("silhouette, axis fitted to the data", fontsize=10)
    for axis in axes[:2]:
        _draw_convention_lines(axis)
    if has_davies_bouldin:
        _plot_curves(axes[2], subset, "davies_bouldin", "Davies-Bouldin (lower = better)")
        axes[2].set_ylim(bottom=0)
        axes[2].set_title("Davies-Bouldin", fontsize=10)
    axes[0].legend(title="linkage", fontsize=8)
    figure.suptitle(f"Agglomerative, metric={metric}" + (", single linkage" if single else ""))
    figure.tight_layout()
    return figure


def density_metrics(run: ClusteringTuningRun) -> pd.DataFrame:
    """tuning_results.csv of an hdbscan / hdbscan_soft run with `n_clusters_found` and `largest_cluster_share`
    (over all subjects, noise included), both computed from the stored labels. `largest_cluster_share` is NaN
    when every subject is noise.

    If the run also wrote `n_clusters_found` the two must agree, or this raises (a clusterings.npz that does
    not belong to this tuning_results.csv).
    """
    if run.method not in DENSITY_METHODS:
        raise ValueError(f"density_metrics needs an hdbscan or hdbscan_soft run, got {run.method!r}")
    columns = SWEPT_COLUMNS[run.method]
    n_clusters, largest_share = [], []
    for row in run.results.to_dict("records"):
        labels = run.labels[combo_key(row, columns)]
        found = labels[labels != NOISE_LABEL]
        n_clusters.append(len(np.unique(found)))
        largest_share.append(float(np.bincount(found).max() / len(labels)) if len(found) else float("nan"))

    metrics = run.results.copy()
    if "n_clusters_found" in metrics.columns and not np.array_equal(metrics["n_clusters_found"].to_numpy(), n_clusters):
        raise ValueError(f"{run.run_dir}: n_clusters_found in tuning_results.csv differs from the clusters in clusterings.npz")
    metrics["n_clusters_found"] = n_clusters
    metrics["largest_cluster_share"] = largest_share
    return metrics


def noise_filtered_curves_figures(metrics: pd.DataFrame, max_noise_fraction: float) -> tuple[dict[str, Figure], list[str]]:
    """Silhouette and Davies-Bouldin against min_cluster_size, one line per min_samples, keeping only the
    combinations with `noise_fraction` at most `max_noise_fraction`: a silhouette that is high only because the
    hardest subjects were thrown into the noise does not appear.

    One figure per `cluster_selection_method` for hdbscan_soft (keyed by it), a single one keyed "" for hdbscan.
    Returns (figures, without_figure): a group where no combination is under the limit (the `leaf` selection
    never goes below 15% noise; a run without structure may have none at all) has no figure and is listed in
    `without_figure`. That is a finding about the run, not an error: `figures` may then be empty.
    """
    groups = dict(tuple(metrics.groupby("cluster_selection_method"))) if "cluster_selection_method" in metrics.columns else {"": metrics}
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
            sizes = sorted(metrics["min_cluster_size"].unique())
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


def _format_report_value(column: str, value: float, key_columns: tuple[str, ...]) -> str:
    if pd.isna(value):
        return "–"
    if column in REPORT_COUNT_COLUMNS:
        return str(int(value))
    if column == "calinski_harabasz":
        return f"{value:,.0f}"
    if column in key_columns:
        return f"{value:g}" if isinstance(value, (int, float, np.integer, np.floating)) else str(value)
    if isinstance(value, str):
        return value
    return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.3f}"


def _markdown_table(table: pd.DataFrame, key_columns: tuple[str, ...]) -> str:
    lines = ["| " + " | ".join(table.columns) + " |", "|" + "|".join(["---"] * len(table.columns)) + "|"]
    for row in table.itertuples(index=False):
        lines.append("| " + " | ".join(_format_report_value(column, value, key_columns) for column, value in zip(table.columns, row)) + " |")
    return "\n".join(lines)


def _k_ranges(values: list[int]) -> str:
    """Sorted integers as runs: [2, 3, 4, 9] -> "2-4, 9"."""
    runs: list[list[int]] = []
    for value in sorted(values):
        if runs and value == runs[-1][1] + 1:
            runs[-1][1] = value
        else:
            runs.append([value, value])
    return ", ".join(str(start) if start == end else f"{start}-{end}" for start, end in runs)


def _silhouette_comment(group: pd.DataFrame) -> list[str]:
    """The bullets under the table of one (metric, linkage): the n_clusters per silhouette band (SILHOUETTE_BANDS),
    the negative ones, and the silhouette at the first and last n_clusters. Measurements and a published convention."""
    group = group.sort_values("n_clusters")
    total = len(group)
    in_band: dict[str | None, list[int]] = {}
    uncomputable = []
    for k, silhouette in zip(group["n_clusters"], group["silhouette"]):
        if np.isnan(silhouette):
            uncomputable.append(int(k))
        else:
            in_band.setdefault(silhouette_band(silhouette), []).append(int(k))
    lines = ["- Silhouette per fascia (convenzione di Kaufman & Rousseeuw 1990, arrotondata a 2 decimali):"]
    for name, description, _ in SILHOUETTE_BANDS:
        if name in in_band:
            lines.append(f"  - {name} ({description}): {len(in_band[name])} k su {total} (k {_k_ranges(in_band[name])})")
    negative = in_band.get(None, [])
    lines.append(
        f"  - negativa: {len(negative)} k su {total} (k {_k_ranges(negative)}); non accettabile per convenzione, la combinazione "
        "resta nel report" if negative else "  - negativa: nessun k"
    )
    if uncomputable:
        lines.append(f"  - non calcolabile: {len(uncomputable)} k su {total} (k {_k_ranges(uncomputable)})")
    first, last = group.iloc[0], group.iloc[-1]
    lines.append(
        f"- Curva della silhouette: k={int(first['n_clusters'])}: {_format_report_value('silhouette', first['silhouette'], ())}, "
        f"k={int(last['n_clusters'])}: {_format_report_value('silhouette', last['silhouette'], ())}"
    )
    return lines


def _curves_section(subset: pd.DataFrame, metric: str) -> list[str]:
    """The figures of one metric of an agglomerative report, with the line that says which dashed lines they show."""
    lines: list[str] = []
    for single, title in ((False, "senza single"), (True, "solo single (scala diversa)")):
        figure_subset = _curves_subset(subset, metric, single)
        if not figure_subset.empty:
            lines += [
                f"**Curve per n_clusters, {title}**",
                "",
                f"![{title}]({k_curves_file_name(metric, single)})",
                "",
                convention_lines_caption(figure_subset),
                "",
            ]
    return lines


def _cophenetic_table(cophenetic: pd.DataFrame, metric: str) -> str:
    values = cophenetic[cophenetic["metric"] == metric].set_index("linkage")["cophenetic_correlation"]
    linkages = _ordered(values.index, LINKAGE_ORDER)
    table = pd.DataFrame({"linkage": linkages, "cophenetic_correlation": [values[linkage] for linkage in linkages]})
    return _markdown_table(table, ("linkage",))


def _jump_table(jump: pd.DataFrame, metric: str) -> str:
    wide = jump[jump["metric"] == metric].pivot(index="n_clusters", columns="linkage", values="jump")
    return _markdown_table(wide[_ordered(wide.columns, LINKAGE_ORDER)].reset_index(), ("n_clusters",))


def _images_section(run_dir: Path, names: list[tuple[str, str]]) -> list[str]:
    """Markdown images for the files of `names` ((caption, file name)) that clustering.py wrote in the run folder:
    a run without one of them simply has no link to it."""
    lines: list[str] = []
    for caption, name in names:
        if (run_dir / name).is_file():
            lines += [f"**{caption}**", "", f"![{caption}]({name})", ""]
    return lines


def _dendrogram_section(run_dir: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, jump: pd.DataFrame, metric: str) -> list[str]:
    """Cophenetic correlation, dendrogram jump and the tree/label images of one metric of an agglomerative report."""
    linkages = _ordered(results[results["metric"] == metric]["linkage"].unique(), LINKAGE_ORDER)
    images = [("Dendrogramma (ultime 30 fusioni)", f"dendrogram_metric={metric}.png")]
    images += [(f"Etichette sul piano 2D, {linkage}", f"labels_2d_{linkage}_{metric}.png") for linkage in linkages]
    return [
        "### Cophenetic correlation", "", _cophenetic_table(cophenetic, metric), "",
        "### Salto del dendrogramma", "", _jump_table(jump, metric), "",
        *_images_section(run_dir, images),
    ]


def _check_agglomerative_inputs(run_dir: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, jump: pd.DataFrame) -> None:
    for name, frame, columns in (
        ("tuning_results", results, AGGLOMERATIVE_REPORT_COLUMNS),
        ("cophenetic", cophenetic, ("metric", "linkage", "cophenetic_correlation")),
        ("jump", jump, ("metric", "linkage", "n_clusters", "jump")),
    ):
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ValueError(f"{run_dir}: {name} has no column(s) {missing} - needed for the agglomerative report")
    for metric in results["metric"].unique():
        if cophenetic[cophenetic["metric"] == metric].empty or jump[jump["metric"] == metric].empty:
            raise ValueError(f"{run_dir}: no cophenetic or jump row for metric={metric!r} (an analysis of another run?)")


def _agglomerative_report_markdown(run_dir: Path, input_path: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, jump: pd.DataFrame) -> str:
    _check_agglomerative_inputs(run_dir, results, cophenetic, jump)
    lines = [
        f"# {AGGLOMERATIVE}, {run_dir.name}",
        "",
        f"Cartella: `{run_dir}`. Matrice di input: `{input_path}`. {len(results)} combinazioni.",
        "",
        "Una sezione per `metric` (gli indici di `metric` diverse non si confrontano), dentro una tabella per `linkage`, "
        "ordinate per `n_clusters`.",
        "Una cella vuota (–) è un indice non calcolabile per quella combinazione. Tutti i dati: `tuning_results.csv`, "
        "`cophenetic_correlation.csv`, `dendrogram_jump.csv`.",
        "",
    ]
    for metric in _ordered(results["metric"].unique(), METRIC_ORDER):
        subset = results[results["metric"] == metric]
        lines += [f"## metric = {metric}", "", *_curves_section(subset, metric)]
        for linkage in _ordered(subset["linkage"].unique(), LINKAGE_ORDER):
            group = subset[subset["linkage"] == linkage]
            table = group.sort_values("n_clusters")[["n_clusters", "silhouette", "davies_bouldin", "calinski_harabasz"]]
            lines += [f"### linkage = {linkage}", "", _markdown_table(table, ("n_clusters",)), "", *_silhouette_comment(group), ""]
        lines += _dendrogram_section(run_dir, results, cophenetic, jump, metric)
    lines += _images_section(
        run_dir, [("Distanza media tra dataset (non tra cluster: dice dell'effetto sito, niente su k)", "interclass_distance_matrix.png")]
    )
    terms = [f"- **`{column}`**: {REPORT_TERMS[column]}" for column in ("silhouette", "davies_bouldin", "calinski_harabasz")]
    terms += [f"- **`cophenetic_correlation`**: {COPHENETIC_TERM}", f"- **`jump`**: {JUMP_TERM}", f"- {SILHOUETTE_BANDS_TERM}"]
    return "\n".join([*lines, "## Termini", "", *terms, ""])


def tuning_report_markdown(
    run_dir: Path, method: str, input_path: Path, results: pd.DataFrame,
    cophenetic: pd.DataFrame | None = None, jump: pd.DataFrame | None = None,
) -> str:
    """The report of one clustering tuning run: its `tuning_results.csv` as markdown tables.

    Agglomerative: one section per `metric` with the curves figures and, per `linkage`, a table with the three indices
    per n_clusters and bullets that place the silhouette in the bands of a published convention (SILHOUETTE_BANDS);
    then the cophenetic correlation and the dendrogram jump (`cophenetic` and `jump`, the two frames of
    `agglomerative_analysis`, required here and refused for any other method) and links to the tree and label images
    clustering.py wrote in the run folder, when it did.

    The other methods: one table per value of the grouping column (`metric` for adp, `cluster_selection_method` for
    hdbscan_soft; hdbscan has a single table), the swept columns first and every other column after them,
    ordered by silhouette, highest first (an empty silhouette last). Nothing is classified: no threshold, no
    verdict. Raises ValueError for a method without a report or a `results` that lacks a column of the layout.
    """
    if method not in REPORT_METHODS:
        raise ValueError(f"no report for clustering_method {method!r} - supported: {list(REPORT_METHODS)}")
    if method == AGGLOMERATIVE:
        if cophenetic is None or jump is None:
            raise ValueError(f"{run_dir}: the agglomerative report needs the cophenetic and jump frames of agglomerative_analysis")
        return _agglomerative_report_markdown(run_dir, input_path, results, cophenetic, jump)
    if cophenetic is not None or jump is not None:
        raise ValueError(f"{run_dir}: cophenetic and jump belong to the agglomerative report, not to {method!r}")
    group_column, key_columns = REPORT_GROUP_COLUMN[method], REPORT_KEY_COLUMNS[method]
    required = [*key_columns, "silhouette", *([group_column] if group_column else [])]
    missing = [column for column in required if column not in results.columns]
    if missing:
        raise ValueError(f"{run_dir}: tuning_results has no column(s) {missing} - needed for the {method} report")

    others = [column for column in results.columns if column not in (*key_columns, group_column)]
    ordered = results[[*([group_column] if group_column else []), *key_columns, *others]]
    groups = ordered.groupby(group_column, sort=False) if group_column else [("", ordered)]

    lines = [
        f"# {method}, {run_dir.name}",
        "",
        f"Cartella: `{run_dir}`. Matrice di input: `{input_path}`. {len(results)} combinazioni.",
        "",
        "Tabelle ordinate per silhouette decrescente"
        + (f"; una per `{group_column}`, perché le silhouette di gruppi diversi non si confrontano." if group_column else "."),
        "Una cella vuota (–) è un indice non calcolabile per quella combinazione.",
    ]
    for name, group in groups:
        group = group.drop(columns=[group_column]) if group_column else group
        group = group.sort_values("silhouette", ascending=False, na_position="last", kind="stable")
        lines += ["", f"## {group_column} = {name}" if group_column else "## Tabella", "", _markdown_table(group, key_columns)]
    terms = [f"- **`{column}`**: {definition}" for column, definition in REPORT_TERMS.items() if column in results.columns]
    return "\n".join([*lines, "", "## Termini", "", *terms, ""])
