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

import itertools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from sklearn.metrics import adjusted_rand_score

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

# The report of a run, for adp (agglomerative and the density methods have their own layout): one table per value of the
# grouping column (a silhouette is not comparable across metrics or across selection methods), the swept columns first.
REPORT_GROUP_COLUMN: dict[str, str | None] = {ADP: "metric"}
REPORT_KEY_COLUMNS: dict[str, tuple[str, ...]] = {ADP: ("Z",)}
REPORT_COUNT_COLUMNS = ("n_clusters", "min_cluster_size", "min_samples", "n_clusters_found", "n_small_clusters")
REPORT_TERMS: dict[str, str] = {
    "silhouette": (
        "per ogni soggetto confronta la distanza media dai compagni del suo cluster con quella dal cluster più vicino; qui è la "
        "media su tutti i soggetti. Va da -1 a 1: più alta è meglio; sotto 0 i soggetti sono in media più vicini a un altro "
        "cluster che al proprio."
    ),
    "davies_bouldin": "media, sui cluster, del rapporto tra quanto il cluster è disperso e quanto è vicino al cluster più simile. Più bassa è meglio.",
    "calinski_harabasz": "rapporto tra la separazione dei cluster e la compattezza di ciascuno. Più alto è meglio; tende a crescere con il numero di cluster.",
    "noise_fraction": "quota dei soggetti non assegnati a nessun cluster (rumore); sono esclusi dal calcolo degli indici.",
    "n_clusters_found": "numero di cluster, rumore escluso.",
    "largest_cluster_share": "quota dei soggetti, rumore compreso, nel cluster più grande.",
    "n_small_clusters": "cluster con meno di 10 soggetti.",
    "id_2nn": "dimensione intrinseca stimata dei dati; costante per `metric`.",
    "ari_vs_prev_z": "ARI (accordo tra due partizioni, 1 = identiche) con la partizione al valore di `Z` immediatamente più basso, sui soli soggetti clusterizzati.",
    "membership_mean": "media, sui soggetti non rumore, della probabilità di appartenere al proprio cluster.",
    "membership_share_below_half": "quota dei soggetti non rumore con probabilità di appartenenza sotto 0.5.",
    "persistence_mean": "stabilità media dei cluster (0 effimeri, 1 stabili).",
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
    "**Fasce della silhouette**: convenzione di Kaufman & Rousseeuw (1990), *Finding Groups in Data*. 0.71-1.00 struttura "
    "forte; 0.51-0.70 ragionevole; 0.26-0.50 debole, forse artificiale; fino a 0.25 nessuna struttura sostanziale. Gli estremi "
    "cambiano da una fonte all'altra: qui la silhouette è arrotondata a 2 decimali. Le fasce descrivono la combinazione: non "
    "scelgono `n_clusters` e non si confrontano tra `metric` diverse. Per Davies-Bouldin e Calinski-Harabasz non esiste una "
    "convenzione con fonte: si leggono solo i valori."
)
SILHOUETTE_DENSITY_NOTE = (
    " Per HDBSCAN la silhouette (come Davies-Bouldin e Calinski-Harabasz) è calcolata sui soli soggetti non rumore: va letta "
    "accanto a `noise_fraction`. Le fasce sono pensate per cluster convessi."
)
COPHENETIC_TERM = (
    "correlazione tra le distanze vere tra i soggetti e le distanze che l'albero implica. Va da -1 a 1: vicino a 1 l'albero "
    "rispetta bene le distanze. Un valore per `metric` e `linkage`, non si confronta tra `metric` diverse. Nessuna fascia con "
    "fonte in letteratura."
)
ARI_TERM = (
    "adjusted Rand index: accordo tra due partizioni degli stessi soggetti, 1 = identiche, 0 = quanto il caso. Qui tra i "
    "linkage della stessa `metric`, allo stesso k; non dipende dai nomi dei cluster."
)
JUMP_TERM = (
    "per ogni k, altezza della fusione che porta da k a k-1 cluster divisa per quella della fusione che porta da k+1 a k. "
    "Vicino a 1: nessun taglio netto a k; più è alto, più il taglio a k è netto. Le altezze sono in unità diverse per ogni "
    "linkage, quindi i linkage non si confrontano. Nessuna fascia con fonte in letteratura."
)

# One block under each figure/table of a report, written as a quote: what it shows, how to read it, what it does not say.
# Descriptions only, no verdict. Each hint is a tuple of bullets.
HINT_CURVES = (
    "Cosa mostra: come cambiano silhouette e Davies-Bouldin al crescere di `n_clusters`, con una linea per ogni linkage.",
    "I pannelli: silhouette con asse da -1 a 1 (a sinistra); la stessa silhouette con asse adattato ai dati (al centro, le "
    "differenze sembrano più grandi); Davies-Bouldin (a destra).",
    "Come si legge: conta la forma della linea su tutti i k, non un punto solo. Silhouette: più alta è meglio. Davies-Bouldin: "
    "più bassa è meglio.",
)
HINT_CURVES_SINGLE = ("Come sopra, ma solo per il linkage `single`: ha spesso valori molto diversi dagli altri, quindi sta in un grafico a parte.",)
HINT_COPHENETIC = (
    "Cosa mostra: quanto l'albero di ogni linkage rispetta le distanze vere tra i soggetti. Serve a confrontare i linkage tra loro (stessa `metric`): più è alto, più l'albero è fedele.",
    "Cosa non dice: niente su quanti cluster scegliere.",
)
HINT_AGREEMENT = (
    "Cosa mostra: per ogni k, quanto due linkage producono la stessa partizione dei soggetti (ARI: 1 = identiche, 0 = quanto il caso).",
    "Come si legge: dove l'ARI è vicino a 1 per tutte le coppie, scegliere il linkage cambia poco; dove è basso, la partizione dipende dal linkage.",
    "Cosa non dice: quale dei due linkage sia quello giusto.",
)
HINT_JUMP = (
    "Cosa mostra: per ogni k, quanto è netto il taglio dell'albero in k cluster. Vicino a 1 non c'è un taglio netto; più è "
    "alto, più è netto.",
    "Cosa non dice: i linkage non si confrontano tra loro (altezze in unità diverse); e non dice se i cluster hanno senso clinico.",
)
HINT_DENDROGRAM = (
    "Cosa mostra: l'albero delle fusioni; l'asse verticale è l'altezza a cui due gruppi si uniscono.",
    "Come si legge: una fusione molto più alta della precedente separa gruppi distinti; tagliare l'albero a una certa altezza "
    "dà quel numero di cluster.",
    "Limiti: sono mostrate solo le ultime 30 fusioni, quindi i k piccoli; le altezze non si confrontano tra linkage.",
)
HINT_LABELS_2D = (
    "Cosa mostra: i soggetti su un piano 2D, colorati per cluster, un riquadro per ogni k mostrato. Il piano è un UMAP "
    "\"gemello\" in 2D, non lo spazio in cui è stato fatto il clustering.",
    "Cosa non dice: indica dove cadono i cluster, non quanto siano separati nello spazio vero.",
    "Vale per tutte le immagini di questa serie.",
)
HINT_HEATMAP = (
    "Cosa mostra: gli stessi numeri delle tabelle su tutta la griglia `min_cluster_size` × `min_samples`, un riquadro per metrica.",
    "Attenzione: ogni riquadro ha una sua scala di colore adattata ai dati, quindi le differenze piccole sembrano grandi.",
)
HINT_FILTERED_CURVES = (
    "Cosa mostra: silhouette e Davies-Bouldin contro `min_cluster_size`, una linea per `min_samples`, solo per le combinazioni "
    "con poco rumore.",
    "Attenzione: il limite di rumore è scritto nel titolo del grafico (`curves_max_noise_fraction` del config, una scelta "
    "nostra). Le combinazioni con più rumore non compaiono; per `leaf` può non esserci nessun grafico.",
)


def _hint_lines(hint: tuple[str, ...]) -> list[str]:
    """A hint as a markdown quote: a title line, one bullet per sentence, a blank line."""
    return ["> **Come leggerlo**", *(f"> - {sentence}" for sentence in hint), ""]


DENSITY_REPORT_COLUMNS = ("min_cluster_size", "min_samples", "silhouette", "davies_bouldin", "calinski_harabasz", "noise_fraction", "n_clusters_found", "largest_cluster_share")
DENSITY_SOFT_COLUMNS = ("cluster_selection_method", "membership_mean", "membership_share_below_half", "persistence_mean")
DENSITY_TABLE_COLUMNS = ("min_cluster_size", "n_clusters_found", "noise_fraction", "largest_cluster_share", "silhouette", "davies_bouldin", "calinski_harabasz")
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


def agglomerative_analysis(run: ClusteringTuningRun, X: np.ndarray, k_values: range) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(cophenetic_table, jump_table) of an agglomerative run, sharing one distance cache."""
    if run.method != AGGLOMERATIVE:
        raise ValueError(f"agglomerative_analysis needs an agglomerative run, got {run.method!r}")
    distance_cache: dict[str, np.ndarray] = {}
    return cophenetic_table(run, X, distance_cache), jump_table(run, X, k_values, distance_cache)


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
        for linkage_a, linkage_b in itertools.combinations(_ordered(labels, LINKAGE_ORDER), 2):
            ari = adjusted_rand_score(labels[linkage_a], labels[linkage_b])
            rows.append({"metric": metric, "n_clusters": int(k), "linkage_a": linkage_a, "linkage_b": linkage_b, "ari": float(ari)})
    return pd.DataFrame(rows, columns=["metric", "n_clusters", "linkage_a", "linkage_b", "ari"])


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
    """The sentence that says which dashed lines of CONVENTION_LINES each silhouette panel of a figure of `subset` shows."""
    low, high = silhouette_zoom_limits(subset["silhouette"])
    visible = [line for line in CONVENTION_LINES if low <= line <= high]
    hidden = [line for line in CONVENTION_LINES if line not in visible]
    as_text = lambda lines: ", ".join(f"{line:.2f}" for line in lines)
    if not hidden:
        center = "si vedono tutti"
    elif not visible:
        center = "non se ne vede nessuno (cadono tutti fuori dal grafico)"
    else:
        shown = f"si vede solo {as_text(visible)}" if len(visible) == 1 else f"si vedono {as_text(visible)}"
        center = f"{shown}; gli altri ({as_text(hidden)}) cadono fuori dal grafico"
    return (
        f"Linee grigie tratteggiate sulla silhouette: i limiti delle fasce di Kaufman & Rousseeuw ({as_text(CONVENTION_LINES)}). "
        f"Pannello a sinistra: si vedono tutti. Pannello centrale: {center}."
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


def _count_phrase(count: int, total: int, label: str) -> str:
    """"29 k su 29", or "1 su 2" when there is no label for the rows."""
    return f"{count}{' ' + label if label else ''} su {total}"


def _silhouette_comment(group: pd.DataFrame, key_column: str = "n_clusters", key_name: str = "k", count_label: str = "k") -> list[str]:
    """The bullets under the table of one (metric, linkage) or one min_samples: the rows per silhouette band
    (SILHOUETTE_BANDS), the negative ones, and the silhouette at the first and last value of `key_column`.
    Measurements and a published convention. `count_label` names the rows being counted ("k"; "" for none)."""
    group = group.sort_values(key_column)
    total = len(group)
    in_band: dict[str | None, list[int]] = {}
    uncomputable = []
    for key, silhouette in zip(group[key_column], group["silhouette"]):
        if np.isnan(silhouette):
            uncomputable.append(int(key))
        else:
            in_band.setdefault(silhouette_band(silhouette), []).append(int(key))
    lines = ["- **Silhouette per fascia** (convenzione di Kaufman & Rousseeuw 1990, arrotondata a 2 decimali):"]
    for name, description, _ in SILHOUETTE_BANDS:
        if name in in_band:
            lines.append(f"  - {name} ({description}): {_count_phrase(len(in_band[name]), total, count_label)} ({key_name} {_k_ranges(in_band[name])})")
    negative = in_band.get(None, [])
    lines.append(
        f"  - negativa (sotto 0): {_count_phrase(len(negative), total, count_label)} ({key_name} {_k_ranges(negative)}); non accettabile "
        "per convenzione, la combinazione resta nel report" if negative else "  - negativa (sotto 0): nessuna"
    )
    if uncomputable:
        lines.append(f"  - non calcolabile: {_count_phrase(len(uncomputable), total, count_label)} ({key_name} {_k_ranges(uncomputable)})")
    first, last = group.iloc[0], group.iloc[-1]
    lines.append(
        f"- **Dal primo all'ultimo valore** ({key_name}): {key_name}={int(first[key_column])}: {_format_report_value('silhouette', first['silhouette'], ())}, "
        f"{key_name}={int(last[key_column])}: {_format_report_value('silhouette', last['silhouette'], ())}"
    )
    return lines


def _curves_section(subset: pd.DataFrame, metric: str) -> list[str]:
    """The figures of one metric of an agglomerative report, with the line that says which dashed lines they show."""
    lines: list[str] = []
    for single, title, hint in ((False, "senza single", HINT_CURVES), (True, "solo single (scala diversa)", HINT_CURVES_SINGLE)):
        figure_subset = _curves_subset(subset, metric, single)
        if not figure_subset.empty:
            lines += [
                f"**Curve per n_clusters, {title}**",
                "",
                f"![{title}]({k_curves_file_name(metric, single)})",
                "",
                *_hint_lines((*hint, convention_lines_caption(figure_subset))),
            ]
    return lines


def _cophenetic_table(cophenetic: pd.DataFrame, metric: str) -> str:
    values = cophenetic[cophenetic["metric"] == metric].set_index("linkage")["cophenetic_correlation"]
    linkages = _ordered(values.index, LINKAGE_ORDER)
    table = pd.DataFrame({"linkage": linkages, "cophenetic_correlation": [values[linkage] for linkage in linkages]})
    return _markdown_table(table, ("linkage",))


def _agreement_table(agreement: pd.DataFrame, metric: str) -> str:
    subset = agreement[agreement["metric"] == metric].assign(pair=lambda frame: frame["linkage_a"] + "-" + frame["linkage_b"])
    wide = subset.pivot(index="n_clusters", columns="pair", values="ari")
    return _markdown_table(wide[list(dict.fromkeys(subset["pair"]))].reset_index(), ("n_clusters",))


def _agreement_block(agreement: pd.DataFrame, metric: str) -> list[str]:
    """The agreement table with its hint, or a line saying there is none: a metric with a single linkage has no pair."""
    if agreement[agreement["metric"] == metric].empty:
        return ["Non calcolabile: la run ha un solo linkage per questa `metric`.", ""]
    return [_agreement_table(agreement, metric), "", *_hint_lines(HINT_AGREEMENT)]


def _jump_table(jump: pd.DataFrame, metric: str) -> str:
    wide = jump[jump["metric"] == metric].pivot(index="n_clusters", columns="linkage", values="jump")
    return _markdown_table(wide[_ordered(wide.columns, LINKAGE_ORDER)].reset_index(), ("n_clusters",))


def _images_section(run_dir: Path, names: list[tuple[str, str, tuple[str, ...] | None]]) -> list[str]:
    """Markdown images for the files of `names` ((caption, file name, hint)) that clustering.py wrote in the run folder:
    a run without one of them simply has no link to it. A hint is written once, under the first image of the series
    that has it (a series shares its hint: pass it on the first entry only, None on the others)."""
    lines: list[str] = []
    pending_hint: tuple[str, ...] | None = None
    for caption, name, hint in names:
        pending_hint = hint or pending_hint
        if (run_dir / name).is_file():
            lines += [f"**{caption}**", "", f"![{caption}]({name})", ""]
            if pending_hint:
                lines += _hint_lines(pending_hint)
                pending_hint = None
    return lines


def _dendrogram_section(
    run_dir: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, agreement: pd.DataFrame, jump: pd.DataFrame, metric: str
) -> list[str]:
    """Cophenetic correlation, agreement between linkages, dendrogram jump and the tree/label images of one metric of an
    agglomerative report."""
    linkages = _ordered(results[results["metric"] == metric]["linkage"].unique(), LINKAGE_ORDER)
    images: list[tuple[str, str, tuple[str, ...] | None]] = [("Dendrogramma (ultime 30 fusioni)", f"dendrogram_metric={metric}.png", HINT_DENDROGRAM)]
    images += [
        (f"Etichette sul piano 2D, {linkage}", f"labels_2d_{linkage}_{metric}.png", HINT_LABELS_2D if index == 0 else None)
        for index, linkage in enumerate(linkages)
    ]
    return [
        "### Cophenetic correlation", "", _cophenetic_table(cophenetic, metric), "", *_hint_lines(HINT_COPHENETIC),
        "### Accordo tra linkage (ARI)", "", *_agreement_block(agreement, metric),
        "### Salto del dendrogramma", "", _jump_table(jump, metric), "", *_hint_lines(HINT_JUMP),
        *_images_section(run_dir, images),
    ]


def _check_agglomerative_inputs(
    run_dir: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, agreement: pd.DataFrame, jump: pd.DataFrame
) -> None:
    for name, frame, columns in (
        ("tuning_results", results, AGGLOMERATIVE_REPORT_COLUMNS),
        ("cophenetic", cophenetic, ("metric", "linkage", "cophenetic_correlation")),
        ("agreement", agreement, ("metric", "n_clusters", "linkage_a", "linkage_b", "ari")),
        ("jump", jump, ("metric", "linkage", "n_clusters", "jump")),
    ):
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ValueError(f"{run_dir}: {name} has no column(s) {missing} - needed for the agglomerative report")
    for metric in results["metric"].unique():
        if any(frame[frame["metric"] == metric].empty for frame in (cophenetic, jump)):
            raise ValueError(f"{run_dir}: no cophenetic or jump row for metric={metric!r} (an analysis of another run?)")


def _agglomerative_report_markdown(
    run_dir: Path, input_path: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, agreement: pd.DataFrame, jump: pd.DataFrame
) -> str:
    _check_agglomerative_inputs(run_dir, results, cophenetic, agreement, jump)
    lines = [
        f"# {AGGLOMERATIVE}, {run_dir.name}",
        "",
        f"Cartella: `{run_dir}`. Matrice di input: `{input_path}`. {len(results)} combinazioni.",
        "",
        "**Come è fatto**",
        "",
        "- Una sezione per `metric` (la distanza usata): gli indici di `metric` diverse non si confrontano.",
        "- In ogni sezione: curve per `n_clusters`, una tabella per `linkage`, poi gli strumenti per scegliere il **linkage** "
        "(curve, cophenetic, accordo tra linkage) e quelli per scegliere dove tagliare l'albero, cioè **k** (salto, dendrogramma, etichette 2D).",
        "- Dati completi: `tuning_results.csv`, `cophenetic_correlation.csv`, `linkage_agreement.csv`, `dendrogram_jump.csv`.",
        "- Una cella vuota (–) è un indice non calcolabile per quella combinazione.",
        "",
    ]
    for metric in _ordered(results["metric"].unique(), METRIC_ORDER):
        subset = results[results["metric"] == metric]
        lines += [f"## metric = {metric}", "", *_curves_section(subset, metric)]
        for linkage in _ordered(subset["linkage"].unique(), LINKAGE_ORDER):
            group = subset[subset["linkage"] == linkage]
            table = group.sort_values("n_clusters")[["n_clusters", "silhouette", "davies_bouldin", "calinski_harabasz"]]
            lines += [f"### linkage = {linkage}", "", _markdown_table(table, ("n_clusters",)), "", *_silhouette_comment(group), ""]
        lines += _dendrogram_section(run_dir, results, cophenetic, agreement, jump, metric)
    terms = [f"- **`{column}`**: {REPORT_TERMS[column]}" for column in ("silhouette", "davies_bouldin", "calinski_harabasz")]
    terms += [
        f"- **`cophenetic_correlation`**: {COPHENETIC_TERM}",
        f"- **`ari`**: {ARI_TERM}",
        f"- **`jump`**: {JUMP_TERM}",
        f"- {SILHOUETTE_BANDS_TERM}",
    ]
    return "\n".join([*lines, "## Termini", "", *terms, ""])


def _extremes_text(group: pd.DataFrame, column: str, label: str) -> str:
    """"da <min> (min_cluster_size ...) a <max> (min_cluster_size ...)" for `column` of one min_samples table."""
    def at(value: float) -> str:
        sizes = [int(size) for size in group.loc[group[column] == value, "min_cluster_size"]]
        text = f"{value:.3f}" if column == "noise_fraction" else f"{int(value)}"
        return f"{text} (min_cluster_size {_k_ranges(sizes)})"
    return f"- {label}: da {at(group[column].min())} a {at(group[column].max())}"


def _density_comment(group: pd.DataFrame) -> list[str]:
    """The bullets under the table of one min_samples of an hdbscan / hdbscan_soft report."""
    lines = _silhouette_comment(group, "min_cluster_size", "min_cluster_size", "")
    lines += [_extremes_text(group, "noise_fraction", "**Rumore**"), _extremes_text(group, "n_clusters_found", "**Cluster trovati**")]
    empty = [int(size) for size in group.loc[group["n_clusters_found"] == 0, "min_cluster_size"]]
    if empty:
        lines.append(f"- **Nessun cluster** (tutti i soggetti rumore): {_count_phrase(len(empty), len(group), '')} (min_cluster_size {_k_ranges(empty)})")
    return lines


def _density_report_markdown(run_dir: Path, method: str, input_path: Path, results: pd.DataFrame) -> str:
    is_soft = method == "hdbscan_soft"
    required = [*DENSITY_REPORT_COLUMNS, *(DENSITY_SOFT_COLUMNS if is_soft else ())]
    missing = [column for column in required if column not in results.columns]
    if missing:
        raise ValueError(f"{run_dir}: tuning_results has no column(s) {missing} - needed for the {method} report")
    columns = [*DENSITY_TABLE_COLUMNS, *(DENSITY_SOFT_COLUMNS[1:] if is_soft else ())]
    lines = [
        f"# {method}, {run_dir.name}",
        "",
        f"Cartella: `{run_dir}`. Matrice di input: `{input_path}`. {len(results)} combinazioni.",
        "",
        "**Come è fatto**",
        "",
        *(["- Una sezione per `cluster_selection_method`: le silhouette di metodi diversi non si confrontano."] if is_soft else []),
        "- Dentro: una tabella per `min_samples`, con una riga per ogni `min_cluster_size`.",
        "- Dati completi: `tuning_results.csv`, `density_metrics.csv`.",
        "- Una cella vuota (–) è un indice non calcolabile per quella combinazione (con 0 cluster non c'è silhouette).",
        "",
    ]
    for selection in (_ordered(results["cluster_selection_method"].unique(), ("eom", "leaf")) if is_soft else [None]):
        subset = results if selection is None else results[results["cluster_selection_method"] == selection]
        heading = "##"
        if selection is not None:
            lines += [f"## cluster_selection_method = {selection}", ""]
            heading = "###"
        suffix = "" if selection is None else f"_{selection}"
        heatmap = "tuning_plot.png" if selection is None else f"tuning_plot_cluster_selection_method={selection}.png"
        lines += _images_section(
            run_dir,
            [("Heatmap delle metriche", heatmap, HINT_HEATMAP), ("Curve con poco rumore", f"noise_filtered_curves{suffix}.png", HINT_FILTERED_CURVES)],
        )
        for min_samples in sorted(subset["min_samples"].unique()):
            group = subset[subset["min_samples"] == min_samples].sort_values("min_cluster_size")
            lines += [f"{heading} min_samples = {int(min_samples)}", "", _markdown_table(group[columns], ("min_cluster_size",)), "", *_density_comment(group), ""]
    terms = [f"- **`{column}`**: {REPORT_TERMS[column]}" for column in (*DENSITY_TABLE_COLUMNS[1:], *(DENSITY_SOFT_COLUMNS[1:] if is_soft else ()))]
    return "\n".join([*lines, "## Termini", "", *terms, f"- {SILHOUETTE_BANDS_TERM}{SILHOUETTE_DENSITY_NOTE}", ""])


def tuning_report_markdown(
    run_dir: Path, method: str, input_path: Path, results: pd.DataFrame,
    cophenetic: pd.DataFrame | None = None, agreement: pd.DataFrame | None = None, jump: pd.DataFrame | None = None,
) -> str:
    """The report of one clustering tuning run: its `tuning_results.csv` as markdown tables.

    Agglomerative: one section per `metric` with the curves figures and, per `linkage`, a table with the three indices
    per n_clusters and bullets that place the silhouette in the bands of a published convention (SILHOUETTE_BANDS);
    then the cophenetic correlation, the agreement between linkages and the dendrogram jump (`cophenetic` and `jump`,
    the frames of `agglomerative_analysis`, and `agreement`, that of `linkage_agreement`: required here and refused for
    any other method) and links to the tree and label images clustering.py wrote in the run folder, when it did.

    hdbscan / hdbscan_soft (`results` is `density_metrics`: it needs `largest_cluster_share`): a
    link to the heatmap clustering.py wrote, and one table per `min_samples` (one section per `cluster_selection_method`
    for hdbscan_soft) with a row per `min_cluster_size` and bullets with the silhouette bands, the range of the noise
    and of the number of clusters.

    adp: one table per `metric`, the swept columns first and every other column after them, ordered by silhouette,
    highest first (an empty silhouette last). Nothing is classified by a threshold of ours. Raises ValueError for a
    method without a report or a `results` that lacks a column of the layout.
    """
    if method not in REPORT_METHODS:
        raise ValueError(f"no report for clustering_method {method!r} - supported: {list(REPORT_METHODS)}")
    if method == AGGLOMERATIVE:
        if cophenetic is None or agreement is None or jump is None:
            raise ValueError(f"{run_dir}: the agglomerative report needs the cophenetic, agreement and jump frames")
        return _agglomerative_report_markdown(run_dir, input_path, results, cophenetic, agreement, jump)
    if cophenetic is not None or agreement is not None or jump is not None:
        raise ValueError(f"{run_dir}: cophenetic, agreement and jump belong to the agglomerative report, not to {method!r}")
    if method in DENSITY_METHODS:
        return _density_report_markdown(run_dir, method, input_path, results)
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
        "**Come è fatto**",
        "",
        "- Righe ordinate per silhouette decrescente"
        + (f"; una tabella per `{group_column}`, perché le silhouette di gruppi diversi non si confrontano." if group_column else "."),
        "- Una cella vuota (–) è un indice non calcolabile per quella combinazione.",
    ]
    for name, group in groups:
        group = group.drop(columns=[group_column]) if group_column else group
        group = group.sort_values("silhouette", ascending=False, na_position="last", kind="stable")
        lines += ["", f"## {group_column} = {name}" if group_column else "## Tabella", "", _markdown_table(group, key_columns)]
    terms = [f"- **`{column}`**: {definition}" for column, definition in REPORT_TERMS.items() if column in results.columns]
    return "\n".join([*lines, "", "## Termini", "", *terms, ""])
