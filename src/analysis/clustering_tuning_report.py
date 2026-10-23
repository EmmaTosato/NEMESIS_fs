"""The report of a stored clustering tuning run (report.md): its tables and figures as markdown.

Computes nothing. It reads what the evaluations of src/analysis/clustering_tuning_evaluations.py wrote in the run
folder (cophenetic_correlation.csv, dendrogram_jump.csv, linkage_agreement.csv, density_metrics.csv, the figures) and
tuning_results.csv, and lays them out with the explanation of each index: what it measures, how to read it, what it
does not say. Called by the sweep (src/pipeline/clustering.py) and by src/pipeline/evaluate_clustering_tuning.py, so the
report is the same either way.

Nothing here classifies a combination as good, usable or stable, with a threshold of ours or of the literature: the
outputs are measurements. The silhouette bands of Kaufman & Rousseeuw are only mentioned (SILHOUETTE_CONVENTION_NOTE).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.clustering_tuning_analysis import (
    ADP,
    AGGLOMERATIVE,
    DENSITY_METHODS,
    LINKAGE_ORDER,
    METRIC_ORDER,
    curves_subset,
    k_curves_file_name,
    ordered,
    read_run_config,
    run_axis_limits,
)
from src.analysis.clustering_tuning_evaluations import (
    COPHENETIC_CORRELATION,
    DENDROGRAM_JUMP,
    DENSITY_METRICS,
    DUNN_INDEX,
    LARGEST_CLUSTER_SHARE,
    LINKAGE_AGREEMENT,
    evaluations_for,
    refuse_existing,
)

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
    "dunn": (
        "rapporto tra la distanza minima tra due cluster e il diametro massimo di un cluster (la distanza più grande tra due "
        "soggetti dello stesso cluster). Più alto è meglio."
    ),
    "noise_fraction": "quota dei soggetti non assegnati a nessun cluster (rumore).",
    "n_clusters_found": "numero di cluster, rumore escluso.",
    "largest_cluster_share": "quota dei soggetti, rumore compreso, nel cluster più grande.",
    "n_small_clusters": "cluster con meno di 10 soggetti.",
    "id_2nn": "dimensione intrinseca stimata dei dati; costante per `metric`.",
    "ari_vs_prev_z": "ARI (accordo tra due partizioni, 1 = identiche) con la partizione al valore di `Z` immediatamente più basso, sui soli soggetti clusterizzati.",
    "membership_mean": "media, sui soggetti non rumore, della probabilità di appartenere al proprio cluster.",
    "persistence_mean": "stabilità media dei cluster (0 effimeri, 1 stabili).",
    "dbcv": (
        "indice di validità basato sulla densità (Moulavi et al. 2014): per ogni cluster confronta quanto è rado al suo "
        "interno con quanto è separato dal cluster più vicino; la media è pesata sulla dimensione dei cluster, con il "
        "rumore nel denominatore, quindi il rumore abbassa il punteggio. Va da -1 a 1: più alto è meglio. Non definito con "
        "meno di 2 cluster."
    ),
}

SILHOUETTE_CONVENTION_NOTE = (
    "**Fasce della silhouette**: esistono fasce di lettura (Kaufman & Rousseeuw 1990, *Finding Groups in Data*); questo "
    "report non le usa. Spiegazione e fonti in `knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md`."
)
DENSITY_INDICES_NOTE = (
    "**Indici non calcolati**: silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn non sono calcolati per HDBSCAN: si "
    "calcolano sui soli soggetti non rumore (se l'algoritmo scarta i soggetti più difficili, salgono) e presuppongono "
    "cluster compatti. Il DBCV pesa il rumore. Spiegazione in "
    "`knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md`."
)
NON_EUCLIDEAN_NOTE = "Calinski-Harabasz, Davies-Bouldin e Dunn non sono definiti per `{metric}`: richiedono la distanza euclidea (cella vuota)."
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
HINT_HEATMAP = (
    "Cosa mostra: gli stessi numeri delle tabelle su tutta la griglia `min_cluster_size` × `min_samples`, un riquadro per metrica.",
    "Attenzione: ogni riquadro ha una sua scala di colore adattata ai dati, quindi le differenze piccole sembrano grandi.",
)
HINT_DBCV_CURVES = (
    "Cosa mostra: DBCV, quota di rumore, quota del cluster più grande e numero di cluster contro `min_cluster_size`, una linea "
    "per `min_samples`. Tutte le combinazioni, nessun filtro sul rumore.",
    "Un punto manca dove i cluster sono meno di 2: il DBCV non è definito, non vale 0.",
    "Cosa non dice: da solo il DBCV non dice quale combinazione scegliere; va letto accanto al rumore.",
)

def _hint_lines(hint: tuple[str, ...]) -> list[str]:
    """A hint as a markdown quote: a title line, one bullet per sentence, a blank line."""
    return ["> **Come leggerlo**", *(f"> - {sentence}" for sentence in hint), ""]


DENSITY_REPORT_COLUMNS = ("min_cluster_size", "min_samples", "noise_fraction", "n_clusters_found", "largest_cluster_share", "dbcv")
DENSITY_SOFT_COLUMNS = ("cluster_selection_method", "membership_mean", "persistence_mean")
DENSITY_TABLE_COLUMNS = ("min_cluster_size", "n_clusters_found", "noise_fraction", "largest_cluster_share", "dbcv")

AGGLOMERATIVE_REPORT_COLUMNS = ("n_clusters", "linkage", "metric", "silhouette", "davies_bouldin", "calinski_harabasz", "dunn", "largest_cluster_share")

def curves_hint(silhouette_limits: tuple[float, float], davies_bouldin_limits: tuple[float, float] | None) -> tuple[str, ...]:
    """The hint under the curves figure of one metric. The axes are those of the whole run, so the text carries their
    values; `davies_bouldin_limits` is None for a metric whose figure has no Davies-Bouldin panel (it needs `euclidean`)."""
    if davies_bouldin_limits:
        panels = "silhouette (a sinistra) e Davies-Bouldin (a destra)"
        axes = (
            f"silhouette da {silhouette_limits[0]:.1f} a {silhouette_limits[1]:.1f}, "
            f"Davies-Bouldin da {davies_bouldin_limits[0]:.1f} a {davies_bouldin_limits[1]:.1f}"
        )
    else:
        panels = "silhouette; Davies-Bouldin non c'è perché per questa `metric` non esiste"
        axes = f"silhouette da {silhouette_limits[0]:.1f} a {silhouette_limits[1]:.1f}"
    return (
        "Cosa mostra: come cambiano silhouette e Davies-Bouldin al crescere di `n_clusters`, con una linea per ogni linkage. "
        "`single` non è disegnato: i suoi valori sono nelle tabelle sotto.",
        f"I pannelli: {panels}.",
        f"Gli assi sono gli stessi in tutti i grafici di questa serie: {axes}. Sono l'intervallo dei dati di tutte le `metric` "
        "della run con un margine dell'8%, arrotondato al decimo. Il confronto è tra le forme delle linee: una silhouette di "
        "`metric` diverse non si confronta nel valore.",
        "Come si legge: conta la forma della linea su tutti i k, non un punto solo. Silhouette: più alta è meglio. Davies-Bouldin: "
        "più bassa è meglio.",
    )


def _format_report_value(column: str, value: float, key_columns: tuple[str, ...]) -> str:
    if pd.isna(value):
        return "–"
    if column in REPORT_COUNT_COLUMNS:
        return str(int(value))
    if not isinstance(value, str) and round(value, 3) == 0:
        value = 0.0  # never "-0.000"
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
    """The bullets under the table of one (metric, linkage) or one min_samples: the rows with a negative silhouette,
    those with none (not computable), and the silhouette at the first and last value of `key_column`. Measurements
    only. `count_label` names the rows being counted ("k"; "" for none)."""
    group = group.sort_values(key_column)
    total = len(group)
    negative = [int(key) for key, silhouette in zip(group[key_column], group["silhouette"]) if silhouette < 0]
    uncomputable = [int(key) for key, silhouette in zip(group[key_column], group["silhouette"]) if np.isnan(silhouette)]
    lines = [
        f"- **Silhouette negativa**: {_count_phrase(len(negative), total, count_label)} ({key_name} {_k_ranges(negative)})"
        if negative
        else "- **Silhouette negativa**: nessuna"
    ]
    if uncomputable:
        lines.append(f"- **Silhouette non calcolabile**: {_count_phrase(len(uncomputable), total, count_label)} ({key_name} {_k_ranges(uncomputable)})")
    first, last = group.iloc[0], group.iloc[-1]
    lines.append(
        f"- **Dal primo all'ultimo valore** ({key_name}): {key_name}={int(first[key_column])}: {_format_report_value('silhouette', first['silhouette'], ())}, "
        f"{key_name}={int(last[key_column])}: {_format_report_value('silhouette', last['silhouette'], ())}"
    )
    return lines


def _curves_section(results: pd.DataFrame, metric: str) -> list[str]:
    """The curves figure of one metric of an agglomerative report, with its hint; empty for a metric with no linkage
    other than `single`. `results` is the whole run: the axes are shared."""
    if curves_subset(results, metric).empty:
        return []
    silhouette_limits = run_axis_limits(results, "silhouette")
    davies_bouldin_limits = run_axis_limits(results, "davies_bouldin") if curves_subset(results, metric)["davies_bouldin"].notna().any() else None
    return [
        "**Curve per n_clusters**",
        "",
        f"![curve per n_clusters]({k_curves_file_name(metric)})",
        "",
        *_hint_lines(curves_hint(silhouette_limits, davies_bouldin_limits)),
    ]


def _cophenetic_table(cophenetic: pd.DataFrame, metric: str) -> str:
    values = cophenetic[cophenetic["metric"] == metric].set_index("linkage")["cophenetic_correlation"]
    linkages = ordered(values.index, LINKAGE_ORDER)
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
    return _markdown_table(wide[ordered(wide.columns, LINKAGE_ORDER)].reset_index(), ("n_clusters",))


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
    """Cophenetic correlation, agreement between linkages, dendrogram jump and the tree image of one metric of an
    agglomerative report."""
    images: list[tuple[str, str, tuple[str, ...] | None]] = [("Dendrogramma (ultime 30 fusioni)", f"dendrogram_metric={metric}.png", HINT_DENDROGRAM)]
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
        "(curve, cophenetic, accordo tra linkage) e quelli per scegliere dove tagliare l'albero, cioè **k** (salto, dendrogramma).",
        "- Dati completi: `tuning_results.csv`, `largest_cluster_share.csv`, `dunn_index.csv`, `cophenetic_correlation.csv`, "
        "`linkage_agreement.csv`, `dendrogram_jump.csv`.",
        "- Una cella vuota (–) è un indice non calcolabile per quella combinazione.",
        "",
    ]
    for metric in ordered(results["metric"].unique(), METRIC_ORDER):
        subset = results[results["metric"] == metric]
        lines += [f"## metric = {metric}", ""]
        if metric != "euclidean":
            lines += [NON_EUCLIDEAN_NOTE.format(metric=metric), ""]
        lines += _curves_section(results, metric)
        for linkage in ordered(subset["linkage"].unique(), LINKAGE_ORDER):
            group = subset[subset["linkage"] == linkage]
            table = group.sort_values("n_clusters")[
                ["n_clusters", "silhouette", "davies_bouldin", "calinski_harabasz", "dunn", "largest_cluster_share"]
            ]
            lines += [f"### linkage = {linkage}", "", _markdown_table(table, ("n_clusters",)), "", *_silhouette_comment(group), ""]
        lines += _dendrogram_section(run_dir, results, cophenetic, agreement, jump, metric)
    terms = [
        f"- **`{column}`**: {REPORT_TERMS[column]}"
        for column in ("silhouette", "davies_bouldin", "calinski_harabasz", "dunn", "largest_cluster_share")
    ]
    terms += [
        f"- **`cophenetic_correlation`**: {COPHENETIC_TERM}",
        f"- **`ari`**: {ARI_TERM}",
        f"- **`jump`**: {JUMP_TERM}",
        f"- {SILHOUETTE_CONVENTION_NOTE}",
    ]
    return "\n".join([*lines, "## Termini", "", *terms, ""])


def _extremes_text(group: pd.DataFrame, column: str, label: str) -> str:
    """"da <min> (min_cluster_size ...) a <max> (min_cluster_size ...)" for `column` of one min_samples table."""
    def at(value: float) -> str:
        sizes = [int(size) for size in group.loc[group[column] == value, "min_cluster_size"]]
        text = f"{value:.3f}" if column in ("noise_fraction", "dbcv") else f"{int(value)}"
        return f"{text} (min_cluster_size {_k_ranges(sizes)})"
    return f"- {label}: da {at(group[column].min())} a {at(group[column].max())}"


def _density_comment(group: pd.DataFrame) -> list[str]:
    """The bullets under the table of one min_samples of an hdbscan / hdbscan_soft report. Measurements only."""
    defined = group[group["dbcv"].notna()]
    lines = [_extremes_text(defined, "dbcv", "**DBCV**") if not defined.empty else "- **DBCV**: mai definito"]
    lines += [_extremes_text(group, "noise_fraction", "**Rumore**"), _extremes_text(group, "n_clusters_found", "**Cluster trovati**")]
    undefined = [int(size) for size in group.loc[group["dbcv"].isna(), "min_cluster_size"]]
    if undefined:
        lines.append(f"- **Meno di 2 cluster** (DBCV non definito): {_count_phrase(len(undefined), len(group), '')} (min_cluster_size {_k_ranges(undefined)})")
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
        *(["- Una sezione per `cluster_selection_method`: i risultati di metodi diversi non si confrontano."] if is_soft else []),
        "- Dentro: una tabella per `min_samples`, con una riga per ogni `min_cluster_size`.",
        "- Dati completi: `tuning_results.csv`, `density_metrics.csv`.",
        "- Una cella vuota (–) è un indice non definito per quella combinazione (con meno di 2 cluster non c'è DBCV).",
        "",
    ]
    for selection in (ordered(results["cluster_selection_method"].unique(), ("eom", "leaf")) if is_soft else [None]):
        subset = results if selection is None else results[results["cluster_selection_method"] == selection]
        heading = "##"
        if selection is not None:
            lines += [f"## cluster_selection_method = {selection}", ""]
            heading = "###"
        heatmap = "tuning_plot.png" if selection is None else f"tuning_plot_cluster_selection_method={selection}.png"
        curves = "dbcv_curves.png" if selection is None else f"dbcv_curves_cluster_selection_method={selection}.png"
        lines += _images_section(run_dir, [("Heatmap delle metriche", heatmap, HINT_HEATMAP), ("Curve contro min_cluster_size", curves, HINT_DBCV_CURVES)])
        for min_samples in sorted(subset["min_samples"].unique()):
            group = subset[subset["min_samples"] == min_samples].sort_values("min_cluster_size")
            lines += [f"{heading} min_samples = {int(min_samples)}", "", _markdown_table(group[columns], ("min_cluster_size",)), "", *_density_comment(group), ""]
    terms = [f"- **`{column}`**: {REPORT_TERMS[column]}" for column in (*DENSITY_TABLE_COLUMNS[1:], *(DENSITY_SOFT_COLUMNS[1:] if is_soft else ()))]
    return "\n".join([*lines, "## Termini", "", *terms, f"- {DENSITY_INDICES_NOTE}", ""])


def tuning_report_markdown(
    run_dir: Path, method: str, input_path: Path, results: pd.DataFrame,
    cophenetic: pd.DataFrame | None = None, agreement: pd.DataFrame | None = None, jump: pd.DataFrame | None = None,
) -> str:
    """The report of one clustering tuning run: its `tuning_results.csv` as markdown tables.

    Agglomerative: one section per `metric` with the curves figures and, per `linkage`, a table with the three indices
    per n_clusters and bullets with the negative silhouettes and the first and last value;
    then the cophenetic correlation, the agreement between linkages and the dendrogram jump (`cophenetic` and `jump`,
    the frames of `cophenetic_table` and `jump_table`, and `agreement`, that of `linkage_agreement`: required here and refused for
    any other method) and links to the tree and label images clustering.py wrote in the run folder, when it did.

    hdbscan / hdbscan_soft (`results` is `density_metrics`: it needs `largest_cluster_share` and `dbcv`): links to the
    heatmap and the DBCV curves the evaluations wrote, and one table per `min_samples` (one section per
    `cluster_selection_method` for hdbscan_soft) with a row per `min_cluster_size` and bullets with the range of the DBCV,
    of the noise and of the number of clusters.

    adp: one table per `metric`, the swept columns first and every other column after them, ordered by silhouette,
    highest first (an empty silhouette last). Nothing is classified by a threshold. Raises ValueError for a
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


REPORT_FILENAME = "report.md"

# The evaluations whose files a report reads from the run folder, by method (adp: none, only tuning_results.csv).
REPORT_EVALUATIONS: dict[str, tuple[str, ...]] = {
    AGGLOMERATIVE: (COPHENETIC_CORRELATION, DENDROGRAM_JUMP, LINKAGE_AGREEMENT, LARGEST_CLUSTER_SHARE, DUNN_INDEX),
    **{method: (DENSITY_METRICS,) for method in DENSITY_METHODS},
    ADP: (),
}


def require_report_evaluations(block: Mapping[str, tuple[str, ...]], methods: tuple[str, ...]) -> None:
    """Every method has a report, and the `tuning_evaluations` block lists the evaluations that report reads, so
    the sweep that writes it has their files. Raises ValueError naming the method and what is missing."""
    for method in methods:
        if method not in REPORT_EVALUATIONS:
            raise ValueError(f"write_report is true but {method!r} has no report - methods with one: {sorted(REPORT_EVALUATIONS)}")
        missing = [name for name in REPORT_EVALUATIONS[method] if name not in evaluations_for(block, method)]
        if missing:
            raise ValueError(f"write_report is true but tuning_evaluations lacks {missing} for {method!r}, which its report reads")


def _read_run_csv(run_dir: Path, name: str, method: str) -> pd.DataFrame:
    path = run_dir / name
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found - the {method} report reads it: list its evaluation in tuning_evaluations and run again")
    return pd.read_csv(path)


def _with_agglomerative_indices(run_dir: Path, results: pd.DataFrame, share: pd.DataFrame, dunn: pd.DataFrame) -> pd.DataFrame:
    """`tuning_results.csv` of an agglomerative run with the `largest_cluster_share` and `dunn` columns of the two evaluation
    files, joined on the swept columns. Raises ValueError if a file does not have exactly one row per combination of
    tuning_results (the analysis of another run)."""
    keys = ["n_clusters", "linkage", "metric"]
    merged = results
    for name, frame, column in (("largest_cluster_share.csv", share, "largest_cluster_share"), ("dunn_index.csv", dunn, "dunn")):
        missing = [key for key in (*keys, column) if key not in frame.columns]
        if missing:
            raise ValueError(f"{run_dir}: {name} has no column(s) {missing} - needed for the agglomerative report")
        if len(frame) != len(results) or len(results.merge(frame[[*keys, column]], on=keys, how="inner")) != len(results):
            raise ValueError(f"{run_dir}: {name} does not have one row per combination of tuning_results.csv (an analysis of another run?)")
        merged = merged.merge(frame[[*keys, column]], on=keys, how="left")
    return merged


def write_report(run_dir: Path, overwrite: bool) -> Path:
    """Writes <run_dir>/report.md from the files in the folder and returns its path. Needs config.md and
    tuning_results.csv, and the CSVs of REPORT_EVALUATIONS for the run's method. Raises FileExistsError if the
    report exists and `overwrite` is false, FileNotFoundError naming a missing file, ValueError for a method
    with no report."""
    path = run_dir / REPORT_FILENAME
    refuse_existing([path], overwrite)
    run_config = read_run_config(run_dir)
    method, input_path = run_config["clustering_method"], Path(run_config["input_path"])
    results = _read_run_csv(run_dir, "tuning_results.csv", method)
    if method == AGGLOMERATIVE:
        frames = {name: _read_run_csv(run_dir, f"{name}.csv", method) for name in REPORT_EVALUATIONS[method]}
        results = _with_agglomerative_indices(run_dir, results, frames[LARGEST_CLUSTER_SHARE], frames[DUNN_INDEX])
        text = tuning_report_markdown(
            run_dir, method, input_path, results,
            frames[COPHENETIC_CORRELATION], frames[LINKAGE_AGREEMENT], frames[DENDROGRAM_JUMP],
        )
    elif method in DENSITY_METHODS:
        text = tuning_report_markdown(run_dir, method, input_path, _read_run_csv(run_dir, f"{DENSITY_METRICS}.csv", method))
    else:
        text = tuning_report_markdown(run_dir, method, input_path, results)
    path.write_text(text)
    return path
