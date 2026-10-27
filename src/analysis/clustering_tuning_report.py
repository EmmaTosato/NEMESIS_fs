"""The report of a stored clustering tuning run (report.md): its tables and figures as markdown.

Computes nothing. It reads what the evaluations of src/analysis/clustering_tuning_evaluations.py wrote in the run
folder (cophenetic_correlation.csv, linkage_agreement.csv, the figures) and tuning_results.csv (which also holds the
columns of the per-combination evaluations), and lays them out with the explanation of each index: what it measures,
how to read it, what it does not say. Called by the sweep (src/pipeline/clustering.py) and by src/pipeline/evaluate_clustering_tuning.py, so the
report is the same either way.

Nothing here classifies a combination as good, usable or stable, with a threshold of ours or of the literature: the
outputs are measurements. The silhouette bands of Kaufman & Rousseeuw are only mentioned (note `silhouette_convention`).

The explanations of the indices are not written here: they are read from utils/report_texts/clustering_tuning.md (REPORT_TEXTS_PATH).
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
    dendrogram_file_name,
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
from src.utils.text_registry import load_text_registry

REPORT_METHODS = (AGGLOMERATIVE, *DENSITY_METHODS, ADP)

# The report of a run, for adp (agglomerative and the density methods have their own layout): one table per value of the
# grouping column (a silhouette is not comparable across metrics or across selection methods), the swept columns first.
REPORT_GROUP_COLUMN: dict[str, str | None] = {ADP: "metric"}
REPORT_KEY_COLUMNS: dict[str, tuple[str, ...]] = {ADP: ("Z",)}
REPORT_COUNT_COLUMNS = ("n_clusters", "min_cluster_size", "min_samples", "n_clusters_found", "n_small_clusters")
# The explanations of the indices (what each measures, how to read it, what it does not say) are not in this module: they are
# in `utils/report_texts/clustering_tuning.md`, a markdown file anyone can read and edit. The keys below are every text the
# report looks up in it; the file must define exactly these (src/utils/text_registry.py raises otherwise).
REPORT_TEXTS_PATH = Path(__file__).resolve().parents[2] / "utils" / "report_texts" / "clustering_tuning.md"

# The columns a report of adp (or a density method) explains, in this order of preference.
REPORT_COLUMN_TERMS = (
    "silhouette", "davies_bouldin", "calinski_harabasz", "dunn", "noise_fraction", "n_clusters_found", "largest_cluster_share",
    "n_small_clusters", "id_2nn", "ari_vs_prev_z", "membership_mean", "persistence_mean", "dbcv",
)
REPORT_TEXT_KEYS = (
    *(f"term:{name}" for name in (*REPORT_COLUMN_TERMS, "cophenetic_correlation", "ari", "jump")),
    "note:silhouette_convention", "note:density_indices", "note:non_euclidean",
    "fragment:curves_panels_both", "fragment:curves_panels_silhouette_only", "fragment:curves_axes_both", "fragment:curves_axes_silhouette_only",
    *(f"hint:{name}" for name in ("curves", "cophenetic", "agreement", "jump", "dendrogram", "heatmap", "dbcv_curves")),
)


def load_report_texts(path: Path = REPORT_TEXTS_PATH) -> dict[str, str | tuple[str, ...]]:
    """The texts of the report by `kind:name` (src/utils/text_registry.py): a string, or a tuple of bullets for a `hint`."""
    return load_text_registry(path, REPORT_TEXT_KEYS, bullet_kinds=("hint",))


def _hint_lines(hint: tuple[str, ...]) -> list[str]:
    """A hint as a markdown quote: a title line, one bullet per sentence, a blank line."""
    return ["> **Come leggerlo**", *(f"> - {sentence}" for sentence in hint), ""]


DENSITY_REPORT_COLUMNS = ("min_cluster_size", "min_samples", "noise_fraction", "n_clusters_found", "largest_cluster_share", "dbcv")
DENSITY_SOFT_COLUMNS = ("cluster_selection_method", "membership_mean", "persistence_mean")
DENSITY_TABLE_COLUMNS = ("min_cluster_size", "n_clusters_found", "noise_fraction", "largest_cluster_share", "dbcv")

AGGLOMERATIVE_REPORT_COLUMNS = ("n_clusters", "linkage", "metric", "silhouette", "davies_bouldin", "calinski_harabasz", "dunn", "largest_cluster_share", "jump")

def curves_hint(
    texts: Mapping[str, str | tuple[str, ...]], silhouette_limits: tuple[float, float], davies_bouldin_limits: tuple[float, float] | None
) -> tuple[str, ...]:
    """The hint under the curves figure of one metric. The axes are those of the whole run, so the text carries their
    values; `davies_bouldin_limits` is None for a metric whose figure has no Davies-Bouldin panel (it needs `euclidean`)."""
    values = {"silhouette_min": f"{silhouette_limits[0]:.1f}", "silhouette_max": f"{silhouette_limits[1]:.1f}"}
    if davies_bouldin_limits:
        values |= {"davies_bouldin_min": f"{davies_bouldin_limits[0]:.1f}", "davies_bouldin_max": f"{davies_bouldin_limits[1]:.1f}"}
        panels, axes = texts["fragment:curves_panels_both"], texts["fragment:curves_axes_both"].format(**values)
    else:
        panels, axes = texts["fragment:curves_panels_silhouette_only"], texts["fragment:curves_axes_silhouette_only"].format(**values)
    return tuple(item.format(panels=panels, axes=axes) for item in texts["hint:curves"])


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


def _curves_section(texts: Mapping[str, str | tuple[str, ...]], results: pd.DataFrame, metric: str) -> list[str]:
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
        *_hint_lines(curves_hint(texts, silhouette_limits, davies_bouldin_limits)),
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


def _agreement_block(texts: Mapping[str, str | tuple[str, ...]], agreement: pd.DataFrame, metric: str) -> list[str]:
    """The agreement table with its hint, or a line saying there is none: a metric with a single linkage has no pair."""
    if agreement[agreement["metric"] == metric].empty:
        return ["Non calcolabile: la run ha un solo linkage per questa `metric`.", ""]
    return [_agreement_table(agreement, metric), "", *_hint_lines(texts["hint:agreement"])]


def _jump_table(results: pd.DataFrame, metric: str) -> str:
    wide = results[results["metric"] == metric].pivot(index="n_clusters", columns="linkage", values="jump")
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
    texts: Mapping[str, str | tuple[str, ...]], run_dir: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, agreement: pd.DataFrame, metric: str
) -> list[str]:
    """Cophenetic correlation, agreement between linkages, dendrogram jump and the tree image of one metric of an
    agglomerative report."""
    images: list[tuple[str, str, tuple[str, ...] | None]] = [("Dendrogramma", dendrogram_file_name(metric), texts["hint:dendrogram"])]
    return [
        "### Cophenetic correlation", "", _cophenetic_table(cophenetic, metric), "", *_hint_lines(texts["hint:cophenetic"]),
        "### Accordo tra linkage (ARI)", "", *_agreement_block(texts, agreement, metric),
        "### Salto del dendrogramma", "", _jump_table(results, metric), "", *_hint_lines(texts["hint:jump"]),
        *_images_section(run_dir, images),
    ]


def _check_agglomerative_inputs(run_dir: Path, results: pd.DataFrame, cophenetic: pd.DataFrame, agreement: pd.DataFrame) -> None:
    for name, frame, columns in (
        ("tuning_results", results, AGGLOMERATIVE_REPORT_COLUMNS),
        ("cophenetic", cophenetic, ("metric", "linkage", "cophenetic_correlation")),
        ("agreement", agreement, ("metric", "n_clusters", "linkage_a", "linkage_b", "ari")),
    ):
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ValueError(
                f"{run_dir}: {name} has no column(s) {missing} - needed for the agglomerative report "
                f"(written by the evaluations {DUNN_INDEX}, {LARGEST_CLUSTER_SHARE}, {DENDROGRAM_JUMP}, cophenetic_correlation and linkage_agreement: list them in tuning_evaluations and run again)"
            )
    for metric in results["metric"].unique():
        if cophenetic[cophenetic["metric"] == metric].empty:
            raise ValueError(f"{run_dir}: no cophenetic row for metric={metric!r} (an analysis of another run?)")


def _agglomerative_report_markdown(
    texts: Mapping[str, str | tuple[str, ...]], run_dir: Path, input_path: Path, results: pd.DataFrame, cophenetic: pd.DataFrame,
    agreement: pd.DataFrame,
) -> str:
    _check_agglomerative_inputs(run_dir, results, cophenetic, agreement)
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
        "- Dati completi: `tuning_results.csv` (anche `dunn`, `largest_cluster_share` e `jump`), `cophenetic_correlation.csv`, "
        "`linkage_agreement.csv`.",
        "- Una cella vuota (–) è un indice non calcolabile per quella combinazione.",
        "",
    ]
    for metric in ordered(results["metric"].unique(), METRIC_ORDER):
        subset = results[results["metric"] == metric]
        lines += [f"## metric = {metric}", ""]
        if metric != "euclidean":
            lines += [texts["note:non_euclidean"].format(metric=metric), ""]
        lines += _curves_section(texts, results, metric)
        for linkage in ordered(subset["linkage"].unique(), LINKAGE_ORDER):
            group = subset[subset["linkage"] == linkage]
            table = group.sort_values("n_clusters")[
                ["n_clusters", "silhouette", "davies_bouldin", "calinski_harabasz", "dunn", "largest_cluster_share"]
            ]
            lines += [f"### linkage = {linkage}", "", _markdown_table(table, ("n_clusters",)), "", *_silhouette_comment(group), ""]
        lines += _dendrogram_section(texts, run_dir, results, cophenetic, agreement, metric)
    terms = [
        f"- **`{column}`**: {texts[f'term:{column}']}"
        for column in ("silhouette", "davies_bouldin", "calinski_harabasz", "dunn", "largest_cluster_share")
    ]
    terms += [
        f"- **`cophenetic_correlation`**: {texts['term:cophenetic_correlation']}",
        f"- **`ari`**: {texts['term:ari']}",
        f"- **`jump`**: {texts['term:jump']}",
        f"- {texts['note:silhouette_convention']}",
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


def _density_report_markdown(
    texts: Mapping[str, str | tuple[str, ...]], run_dir: Path, method: str, input_path: Path, results: pd.DataFrame
) -> str:
    is_soft = method == "hdbscan_soft"
    required = [*DENSITY_REPORT_COLUMNS, *(DENSITY_SOFT_COLUMNS if is_soft else ())]
    missing = [column for column in required if column not in results.columns]
    if missing:
        raise ValueError(
            f"{run_dir}: tuning_results has no column(s) {missing} - needed for the {method} report "
            f"(the {DENSITY_METRICS} evaluation writes them: list it in tuning_evaluations and run again)"
        )
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
        "- Dati completi: `tuning_results.csv`.",
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
        lines += _images_section(run_dir, [("Heatmap delle metriche", heatmap, texts["hint:heatmap"]), ("Curve contro min_cluster_size", curves, texts["hint:dbcv_curves"])])
        for min_samples in sorted(subset["min_samples"].unique()):
            group = subset[subset["min_samples"] == min_samples].sort_values("min_cluster_size")
            lines += [f"{heading} min_samples = {int(min_samples)}", "", _markdown_table(group[columns], ("min_cluster_size",)), "", *_density_comment(group), ""]
    terms = [f"- **`{column}`**: {texts[f'term:{column}']}" for column in (*DENSITY_TABLE_COLUMNS[1:], *(DENSITY_SOFT_COLUMNS[1:] if is_soft else ()))]
    return "\n".join([*lines, "## Termini", "", *terms, f"- {texts['note:density_indices']}", ""])


def tuning_report_markdown(
    run_dir: Path, method: str, input_path: Path, results: pd.DataFrame,
    cophenetic: pd.DataFrame | None = None, agreement: pd.DataFrame | None = None,
) -> str:
    """The report of one clustering tuning run: its `tuning_results.csv` as markdown tables.

    Agglomerative (`results` has the `dunn`, `largest_cluster_share` and `jump` columns of the evaluations): one section per
    `metric` with the curves figures and, per `linkage`, a table with the indices per n_clusters and bullets with the negative
    silhouettes and the first and last value; then the cophenetic correlation, the agreement between linkages and the
    dendrogram jump (`cophenetic` and `agreement`, the frames of `cophenetic_table` and `linkage_agreement`: required
    here and refused for any other method) and links to the tree images the `dendrograms` evaluation wrote in the run folder, when it did.

    hdbscan / hdbscan_soft (`results` needs the `largest_cluster_share` and `dbcv` columns of `density_metrics`): links to the
    heatmap and the DBCV curves the evaluations wrote, and one table per `min_samples` (one section per
    `cluster_selection_method` for hdbscan_soft) with a row per `min_cluster_size` and bullets with the range of the DBCV,
    of the noise and of the number of clusters.

    adp: one table per `metric`, the swept columns first and every other column after them, ordered by silhouette,
    highest first (an empty silhouette last). Nothing is classified by a threshold. Raises ValueError for a
    method without a report or a `results` that lacks a column of the layout.
    """
    if method not in REPORT_METHODS:
        raise ValueError(f"no report for clustering_method {method!r} - supported: {list(REPORT_METHODS)}")
    texts = load_report_texts()
    if method == AGGLOMERATIVE:
        if cophenetic is None or agreement is None:
            raise ValueError(f"{run_dir}: the agglomerative report needs the cophenetic and agreement frames")
        return _agglomerative_report_markdown(texts, run_dir, input_path, results, cophenetic, agreement)
    if cophenetic is not None or agreement is not None:
        raise ValueError(f"{run_dir}: cophenetic and agreement belong to the agglomerative report, not to {method!r}")
    if method in DENSITY_METHODS:
        return _density_report_markdown(texts, run_dir, method, input_path, results)
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
    terms = [f"- **`{column}`**: {texts[f'term:{column}']}" for column in REPORT_COLUMN_TERMS if column in results.columns]
    return "\n".join([*lines, "", "## Termini", "", *terms, ""])


REPORT_FILENAME = "report.md"

# The evaluations whose output (a file of the run folder, or columns of tuning_results.csv) a report reads, by method
# (adp: none, only tuning_results.csv).
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


def write_report(run_dir: Path, overwrite: bool) -> Path:
    """Writes <run_dir>/report.md from the files in the folder and returns its path. Needs config.md and
    tuning_results.csv (with the columns of the run's per-combination evaluations), and, for agglomerative,
    cophenetic_correlation.csv and linkage_agreement.csv. Raises FileExistsError if the
    report exists and `overwrite` is false, FileNotFoundError naming a missing file, ValueError for a method
    with no report."""
    path = run_dir / REPORT_FILENAME
    refuse_existing([path], overwrite)
    run_config = read_run_config(run_dir)
    method, input_path = run_config["clustering_method"], Path(run_config["input_path"])
    results = _read_run_csv(run_dir, "tuning_results.csv", method)
    if method == AGGLOMERATIVE:
        text = tuning_report_markdown(
            run_dir, method, input_path, results,
            _read_run_csv(run_dir, f"{COPHENETIC_CORRELATION}.csv", method), _read_run_csv(run_dir, f"{LINKAGE_AGREEMENT}.csv", method),
        )
    elif method in DENSITY_METHODS:
        text = tuning_report_markdown(run_dir, method, input_path, results)
    else:
        text = tuning_report_markdown(run_dir, method, input_path, results)
    path.write_text(text)
    return path
