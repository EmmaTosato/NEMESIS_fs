"""Render the summary tables of the SDC clustering tunings (LaTeX booktabs -> .tex + PNG).

One table file per (method, reduction, n_components) under `<output-dir>/<method>/`:

- `agglomerative_<red>_nc<n>`: one row per metric / linkage (`single` left out), with the five k of highest
  silhouette (best first), their range, the silhouette of those five and of the 6th, and the silhouette range over
  every k.
- `hdbscan_<red>_nc<n>`: the five combinations of highest silhouette (and the 6th), with noise, clusters found and
  largest cluster share.
- `hdbscan_soft_<red>_nc<n>`: the same for `eom` and `leaf` (two tables in one file), plus the mean soft
  membership and the share of subjects with membership < 0.5.

Silhouette of HDBSCAN is not a column of `tuning_results.csv` (it is not meaningful with noise): it is recomputed
here, euclidean, on the non-noise subjects of the saved labels (`clusterings.npz`) and the run's input matrix.
Combinations with no cluster are left out of the HDBSCAN tables and counted in the title. The soft membership is not
saved either: the six displayed combinations of each table are refitted with `hdbscan_soft_fit`, and the script stops
if a refit does not reproduce the saved labels or the `membership_mean` of `tuning_results.csv`.

Usage:
    conda activate nemesis
    PYTHONPATH=. python scripts/build_tuning_summary_tables.py --output-dir results/tables/tuning_sum_03-11 \\
        [--session s2.4-vol] [--tuning-root results/sdc/clustering/tuning]

Needs `pdflatex` and `pdftoppm` on PATH (see scripts/build_dataset_summary_table.py::compile_to_png).
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.build_dataset_summary_table import compile_to_png
from src.analysis.clustering import hdbscan_soft_fit, own_cluster_membership, soft_membership_matrix
from src.analysis.clustering_tuning import compute_clustering_metrics
from src.analysis.clustering_tuning_analysis import (
    LINKAGE_ORDER,
    METRIC_ORDER,
    SINGLE_LINKAGE,
    SWEPT_COLUMNS,
    ClusteringTuningRun,
    combo_key,
    load_clustering_tuning_run,
)
from src.utils.artifacts import load_matrix

TOP_N = 5
UMAP_NCS = (2, 3, 10)
PCA_NCS = (2, 12, 30, 42)
SELECTION_METHODS = ("eom", "leaf")
# approx_min_span_tree is the one hdbscan_soft base param the grid does not sweep (params_clustering.json).
SOFT_FIXED_PARAMS = {"approx_min_span_tree": False}
MEMBERSHIP_TOLERANCE = 1e-6
SOFT_FOOTNOTE = (
    r"Membership = soft probability of belonging to the assigned cluster; "
    r"mean and share computed on non-noise patients."
)

_PREAMBLE = r"""\documentclass[border=8pt,varwidth=40cm]{standalone}
\usepackage[scaled=.92]{helvet}
\renewcommand{\familydefault}{\sfdefault}
\usepackage[T1]{fontenc}
\usepackage{booktabs}
\usepackage{array}
\begin{document}
\small
"""


@dataclass(frozen=True)
class RunSpec:
    method: str
    reduction: str  # "umap" or "pca"
    n_components: int

    @property
    def name(self) -> str:
        return f"{self.method}_{self.reduction}_nc{self.n_components}"

    @property
    def label(self) -> str:
        return f"nc{self.n_components}" if self.reduction == "umap" else f"PCA, nc{self.n_components}"


def find_run_dir(tuning_root: Path, spec: RunSpec, session: str) -> Path:
    """The one tuning directory of `spec`: `<date>_<session>_m_euclidean_nc<n>` (UMAP) or `<date>_<session>_nc<n>` (PCA).
    Raises FileNotFoundError / ValueError if there is none or more than one."""
    suffix = f"m_euclidean_nc{spec.n_components}" if spec.reduction == "umap" else f"nc{spec.n_components}"
    matches = sorted((tuning_root / spec.method / spec.reduction).glob(f"*_{session}_{suffix}"))
    if not matches:
        raise FileNotFoundError(f"no tuning of {spec.method}/{spec.reduction} matching *_{session}_{suffix} under {tuning_root}")
    if len(matches) > 1:
        raise ValueError(f"{len(matches)} tunings match *_{session}_{suffix}: {[m.name for m in matches]}")
    return matches[0]


# ---------- formatting ----------

def _signed(value: float, decimals: int) -> str:
    """LaTeX number with a real minus sign."""
    text = f"{value:.{decimals}f}"
    return text.replace("-", "$-$")


def _range(low: float, high: float, decimals: int = 3) -> str:
    return f"{_signed(low, decimals)}--{_signed(high, decimals)}"


def _table_start(columns: str, title: str, header: list[str]) -> str:
    width = len(header)
    return (
        f"\\begin{{tabular}}{{{columns}}}\n\\toprule\n\\multicolumn{{{width}}}{{l}}{{{title}}} \\\\\n\\midrule\n"
        + " & ".join(header) + " \\\\\n\\midrule\n"
    )


def _table_end() -> str:
    return "\\bottomrule\n\\end{tabular}\n"


# ---------- agglomerative ----------

def top_k_row(silhouette_by_k: pd.Series) -> dict[str, str]:
    """The cells of one metric / linkage row from its silhouette per k (index = k, 2 or more values, no NaN).
    Ties are broken by the smaller k."""
    if silhouette_by_k.isna().any():
        raise ValueError(f"silhouette has NaN at k={list(silhouette_by_k.index[silhouette_by_k.isna()])}")
    if len(silhouette_by_k) <= TOP_N:
        raise ValueError(f"need more than {TOP_N} values of k for the top-{TOP_N} and the 6th, got {len(silhouette_by_k)}")
    ranked = silhouette_by_k.sort_index().sort_values(ascending=False, kind="stable")
    top, sixth = ranked.iloc[:TOP_N], ranked.iloc[TOP_N]
    return {
        "top_k": ", ".join(str(int(k)) for k in top.index),
        "range_k": f"{int(top.index.min())}--{int(top.index.max())}",
        "top_silhouette": f"{_range(top.min(), top.max())} ({_signed(sixth, 3)})",
        "all_silhouette": _range(silhouette_by_k.min(), silhouette_by_k.max()),
    }


def agglomerative_latex(run: ClusteringTuningRun, label: str) -> str:
    results = run.results[run.results["linkage"] != SINGLE_LINKAGE]
    rows = []
    for metric in METRIC_ORDER:
        for linkage in LINKAGE_ORDER:
            subset = results[(results["metric"] == metric) & (results["linkage"] == linkage)]
            if subset.empty:
                continue
            cells = top_k_row(subset.set_index("n_clusters")["silhouette"])
            rows.append(
                f"{metric} / {linkage} & {cells['top_k']} & \\textbf{{{cells['range_k']}}} & "
                f"{cells['top_silhouette']} & {cells['all_silhouette']} \\\\"
            )
    header = [
        "Metric / linkage",
        r"Top 5 $k$ (highest silhouette first)",
        r"\textbf{Range of top 5 $k$}",
        "Silhouette, top 5 (6th)",
        r"Silhouette range over all $k$",
    ]
    return _table_start("lrrrr", f"\\textbf{{{label}}}", header) + "\n".join(rows) + "\n" + _table_end()


# ---------- HDBSCAN ----------

def density_silhouettes(run: ClusteringTuningRun, X: np.ndarray, rows: pd.DataFrame) -> pd.Series:
    """Silhouette (euclidean, non-noise subjects) of each row of `rows` (a slice of the run's results, with at
    least one cluster). Raises ValueError if a row has exactly one cluster: its silhouette is not defined."""
    columns = SWEPT_COLUMNS[run.method]
    values = {}
    for index, row in zip(rows.index, rows.to_dict("records")):  # records keep the int dtype of the key columns
        key = combo_key(row, columns)
        silhouette = compute_clustering_metrics(X, run.labels[key])["silhouette"]
        if np.isnan(silhouette):
            raise ValueError(f"{run.run_dir}: silhouette undefined for {key} ({row['n_clusters_found']:.0f} cluster(s))")
        values[index] = silhouette
    return pd.Series(values)


def soft_memberships(run: ClusteringTuningRun, X: np.ndarray, row: dict) -> tuple[float, float]:
    """(mean, share below 0.5) of the own-cluster soft membership of the non-noise subjects of one `hdbscan_soft`
    combination, from a refit. Raises ValueError if the refit does not reproduce the saved labels or the
    `membership_mean` of tuning_results.csv."""
    params = {
        "min_cluster_size": int(row["min_cluster_size"]),
        "min_samples": int(row["min_samples"]),
        "cluster_selection_method": row["cluster_selection_method"],
        **SOFT_FIXED_PARAMS,
    }
    key = combo_key(row, SWEPT_COLUMNS[run.method])
    fitted = hdbscan_soft_fit(X, params)
    if not np.array_equal(fitted.labels_, run.labels[key]):
        raise ValueError(f"{run.run_dir}: the refit of {key} does not reproduce the saved labels")
    own = own_cluster_membership(soft_membership_matrix(fitted), fitted.labels_)
    own = own[~np.isnan(own)]
    if abs(own.mean() - row["membership_mean"]) > MEMBERSHIP_TOLERANCE:
        raise ValueError(f"{run.run_dir}: refit membership_mean {own.mean():.6f} != csv {row['membership_mean']:.6f} for {key}")
    return float(own.mean()), float((own < 0.5).mean())


def density_table(
    run: ClusteringTuningRun, X: np.ndarray, selection: str | None, label: str, soft: bool
) -> str:
    """One table of the top-5 (and 6th) combinations by silhouette; `selection` filters a soft run's
    `cluster_selection_method` (None for plain HDBSCAN)."""
    results = run.results
    if selection is not None:
        results = results[results["cluster_selection_method"] == selection]
    total = len(results)
    results = results[results["n_clusters_found"] >= 1]
    if results.empty:
        raise ValueError(f"{run.run_dir}: no combination with a cluster{'' if selection is None else f' for {selection}'}")
    silhouette = density_silhouettes(run, X, results)
    results = results.assign(silhouette=silhouette).sort_values(
        ["silhouette", "min_cluster_size", "min_samples"], ascending=[False, True, True], kind="stable"
    )
    shown = results.iloc[: TOP_N + 1]

    subtitle = ""
    if soft or len(results) < total:
        clause = f"; {len(results)} of {total} combinations with clusters" if len(results) < total else ""
        subtitle = f" (from {_signed(results['silhouette'].min(), 3)} to {_signed(results['silhouette'].max(), 3)}{clause})"
    title = f"\\textbf{{{label}{'' if selection is None else f', {selection}'}}}{subtitle}"

    header = ["Rank", "Min cluster size / min samples", "Silhouette", "Noise", "Clusters found", "Largest cluster share"]
    columns = "rrrrrr"
    if soft:
        header += ["Mean membership", r"Share with membership $<0.5$"]
        columns += "rr"
    body = []
    for position, row in enumerate(shown.to_dict("records"), start=1):
        cells = [
            "6th" if position == TOP_N + 1 else str(position),
            f"{int(row['min_cluster_size'])} / {int(row['min_samples'])}",
            _signed(row["silhouette"], 3),
            f"{100 * row['noise_fraction']:.1f}\\%",
            str(int(row["n_clusters_found"])),
            f"{100 * row['largest_cluster_share']:.1f}\\%",
        ]
        if soft:
            mean, below = soft_memberships(run, X, row)
            cells += [f"{mean:.2f}", f"{100 * below:.0f}\\%"]
        body.append(" & ".join(cells) + " \\\\")
    latex = _table_start(columns, title, header) + "\n".join(body) + "\n" + _table_end()
    if soft:
        latex += f"\\par\\footnotesize {SOFT_FOOTNOTE}\\par\n\\small\n"
    return latex


def density_latex(run: ClusteringTuningRun, X: np.ndarray, label: str) -> str:
    if run.method == "hdbscan":
        return density_table(run, X, None, label, soft=False)
    return "\n\\vspace{1.5em}\n".join(density_table(run, X, selection, label, soft=True) for selection in SELECTION_METHODS)


# ---------- driver ----------

def build_spec(spec: RunSpec, tuning_root: Path, session: str, output_dir: Path) -> Path:
    run = load_clustering_tuning_run(find_run_dir(tuning_root, spec, session))
    if run.method != spec.method:
        raise ValueError(f"{run.run_dir}: config.md says {run.method!r}, expected {spec.method!r}")
    if spec.method == "agglomerative":
        body = agglomerative_latex(run, spec.label)
    else:
        X, _, _ = load_matrix(run.input_path)
        body = density_latex(run, np.asarray(X), spec.label)
    target = output_dir / spec.method
    compile_to_png(spec.name, f"{_PREAMBLE}{body}\\end{{document}}\n", target)
    (target / f"{spec.name}.pdf").unlink()  # compile_to_png always writes it; only .tex and .png are kept here
    return target / f"{spec.name}.png"


def all_specs() -> list[RunSpec]:
    return [
        RunSpec(method, reduction, n)
        for method in ("agglomerative", "hdbscan", "hdbscan_soft")
        for reduction, ncs in (("umap", UMAP_NCS), ("pca", PCA_NCS))
        for n in ncs
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=Path("results/tables/tuning_sum_03-11"))
    parser.add_argument("--session", default="s2.4-vol")
    parser.add_argument("--tuning-root", type=Path, default=Path("results/sdc/clustering/tuning"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)

    for spec in all_specs():
        print(f"{spec.name} -> {build_spec(spec, args.tuning_root, args.session, args.output_dir)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
