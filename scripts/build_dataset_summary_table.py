"""Render the dataset count tables (LaTeX booktabs -> .tex + PDF + PNG).

- dataset_summary_table: per-dataset "Lesion mask / SDC" counts, straight from the
  subject registry (assets/metadata/participants.csv, `has_lesion`/`has_sdc`). A
  dataset with no SDC at all prints an en dash, not 0.
- group_summary_table (only with --features-dir): stroke (ST) vs healthy-control (HC)
  subjects that have functional-connectivity features, counted from the `sub-*`
  folders of the given features directory, group taken from the subject id
  (src.retrieval.dataset.group_of). Counted from disk, not from the registry: HC
  subjects are only in the registry once populate_metadata has seen them, and a local
  data/ copy is a partial sample (docs/guides/datasets.md) - point --features-dir at the
  full copy (the EBRAIN mount, or a full local retrieval).

Usage:
    conda activate nemesis
    PYTHONPATH=. python scripts/build_dataset_summary_table.py --output-dir results/tables \\
        [--features-dir <.../UNIPD/WashU/features>]

Needs `pdflatex` and `pdftoppm` on PATH; raises if either is missing.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from src.retrieval.dataset import group_of
from src.utils.participants import load_participants_registry

DATASET_TABLE_NAME = "dataset_summary_table"
GROUP_TABLE_NAME = "group_summary_table"
GROUP_LABELS = {"ST": "Stroke (ST)", "HC": "Healthy Controls (HC)"}
PNG_DPI = 300

_LATEX_TEMPLATE = r"""\documentclass[border=8pt]{{standalone}}
\usepackage{{booktabs}}
\usepackage{{array}}
\begin{{document}}
\Large
\begin{{tabular}}{{l >{{\centering\arraybackslash}}p{{3.2cm}} >{{\centering\arraybackslash}}p{{2.2cm}}}}
\toprule
Dataset & Lesion mask & SDC \\
\midrule
{rows}
\midrule
\textbf{{Total}} & \textbf{{{total_lesion}}} & \textbf{{{total_sdc}}} \\
\bottomrule
\end{{tabular}}
\end{{document}}
"""


_GROUP_TEMPLATE = r"""\documentclass[border=8pt]{{standalone}}
\usepackage{{booktabs}}
\usepackage{{array}}
\begin{{document}}
\Large
\begin{{tabular}}{{l >{{\centering\arraybackslash}}p{{2cm}}}}
\toprule
Group & n \\
\midrule
{rows}
\midrule
\textbf{{Total}} & \textbf{{{total}}} \\
\bottomrule
\end{{tabular}}
\end{{document}}
"""


def count_per_dataset(registry: pd.DataFrame) -> pd.DataFrame:
    """Subjects with a lesion mask / SDC per dataset, in first-appearance order."""
    return registry.groupby("dataset", sort=False)[["has_lesion", "has_sdc"]].sum().astype(int)


def _latex_escape(text: str) -> str:
    return text.replace("_", r"\_").replace("/", " / ")


def render_latex(counts: pd.DataFrame) -> str:
    """Fill the booktabs template; datasets sorted by descending lesion count."""
    counts = counts.sort_values("has_lesion", ascending=False, kind="stable")
    rows = "\n".join(
        f"{_latex_escape(name)} & {row.has_lesion} & {row.has_sdc if row.has_sdc else r'--'} \\\\"
        for name, row in counts.iterrows()
    )
    return _LATEX_TEMPLATE.format(
        rows=rows, total_lesion=counts.has_lesion.sum(), total_sdc=counts.has_sdc.sum()
    )


def count_groups(features_dir: Path) -> dict[str, int]:
    """Subjects per group among the `sub-*` folders of features_dir.

    Raises FileNotFoundError if features_dir is missing, ValueError if it holds no
    subject folder (wrong path - not a table of zeros) or a group other than ST/HC.
    """
    if not features_dir.is_dir():
        raise FileNotFoundError(f"features directory not found: {features_dir}")
    subjects = sorted(p.name for p in features_dir.glob("sub-*") if p.is_dir())
    if not subjects:
        raise ValueError(f"no sub-* folder under {features_dir}")
    counts = {group: 0 for group in GROUP_LABELS}
    for subject in subjects:
        group = group_of(subject)
        if group not in counts:
            raise ValueError(f"{subject}: group {group!r} not in {sorted(GROUP_LABELS)}")
        counts[group] += 1
    return counts


def render_group_latex(counts: dict[str, int]) -> str:
    rows = "\n".join(f"{GROUP_LABELS[g]} & {n} \\\\" for g, n in counts.items())
    return _GROUP_TEMPLATE.format(rows=rows, total=sum(counts.values()))


def compile_to_png(name: str, tex: str, output_dir: Path) -> None:
    """Write <name>.tex/.pdf/.png into output_dir (created if missing)."""
    for tool in ("pdflatex", "pdftoppm"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool!r} not found on PATH - required to render the table")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{name}.tex").write_text(tex)
    with tempfile.TemporaryDirectory() as tmp:
        tex_path = Path(tmp) / f"{name}.tex"
        tex_path.write_text(tex)
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=tmp, check=True, capture_output=True,
        )
        pdf_path = Path(tmp) / f"{name}.pdf"
        shutil.copy(pdf_path, output_dir / pdf_path.name)
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(PNG_DPI), "-singlefile", str(pdf_path),
             str(output_dir / name)],
            check=True, capture_output=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output-dir", type=Path, default=Path("results/tables"))
    parser.add_argument("--features-dir", type=Path, default=None,
                        help="WashU features/ directory (full copy); enables the ST/HC table")
    args = parser.parse_args()

    counts = count_per_dataset(load_participants_registry())
    compile_to_png(DATASET_TABLE_NAME, render_latex(counts), args.output_dir)
    print(counts.to_string())
    if args.features_dir is not None:
        groups = count_groups(args.features_dir)
        compile_to_png(GROUP_TABLE_NAME, render_group_latex(groups), args.output_dir)
        print(groups)
    print(f"tables written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
