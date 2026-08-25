"""Standalone CLI to retrieve `sdc` files only - a thin, argparse-driven
wrapper around the same retrieval engine `src.pipeline.retrieve_data.main()`
uses (src.retrieval.config/dataset/output_layout, retrieve_data.run()), not a
separate implementation. Deliberately has no `config/pipelines/*.json` of its
own: unlike retrieve_data.py, every run-specific option here (which
datasets, which file categories, overwrite, output root) is a CLI flag, so
running a partial/exploratory SDC pull needs no new file under `config/`
alongside the pipeline configs already there - see `docs/guides/datasets.md`
for what each category actually is (voxel-wise disconnectome map, per-atlas
parcellated CSVs, ...) and their relative size. Still reuses (does not
duplicate) `config/registry/file_patterns_{local,server}.json` for the
`sdc` leaf templates themselves, since those are a naming *registry*, not a
per-run option - `--input-root` overrides only the `sdc` project_root read
from it, for a one-off different mount without editing the registry file.

Usage:
    PYTHONPATH=. conda activate nemesis && python scripts/download_sdc.py \\
        --datasets UNIPD/WashU UKLFR/stroke_UKLFR \\
        --categories disconnectome-LF lesion-LF \\
        --output-root data/

Defaults to every registered sdc dataset and every category (equivalent to
the full 3 GB pull already documented in docs/guides/datasets.md).
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from src.pipeline.retrieve_data import run
from src.retrieval.config import FilePatterns, RetrievalConfig, RetrieveItem, load_file_patterns

# The 5 datasets registered for the `sdc` object today (see
# file_patterns_server.json / docs/dev/retrieval.md "sdc - a concrete
# instance of this extension") - kept here, not re-derived from the
# registry, since the registry has no per-object "which datasets support
# this" listing (Dataset.has_object() only answers per dataset, at runtime).
SDC_DATASETS = ("UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR", "UKE/WAKEUP_acute")

# The 6 suffixes registered under sdc.dwi.* - see file_patterns_server.json.
# Sizes/purpose documented in docs/guides/datasets.md ("Structural
# Disconnectome calcolato esternamente"): disconnectome-map/lesion-map are
# the two voxel-wise .nii.gz volumes (~73% of the total size combined);
# disconnectome-LF/lesion-LF are the already-parcellated per-atlas CSVs.
SDC_CATEGORIES = (
    "disconnectome-map",
    "disconnectome-mapstats",
    "disconnectome-LF",
    "lesion-map",
    "lesion-mapstats",
    "lesion-LF",
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retrieve `sdc` (structural disconnectome) files only.")
    parser.add_argument(
        "--datasets", nargs="+", choices=SDC_DATASETS, default=list(SDC_DATASETS),
        help="Which dataset(s) to retrieve (default: all 5 registered for sdc).",
    )
    parser.add_argument(
        "--categories", nargs="+", choices=SDC_CATEGORIES, default=list(SDC_CATEGORIES),
        help="Which sdc.dwi.* suffix(es) to retrieve (default: all 6 - see docs/guides/datasets.md for sizes).",
    )
    parser.add_argument("--overwrite", action="store_true", help="Re-copy files that already exist locally.")
    parser.add_argument(
        "--file-patterns", default="config/registry/file_patterns_server.json",
        help="Registry file to read the sdc leaf templates from (default: server; pass the _local.json variant "
        "for a local-mount run).",
    )
    parser.add_argument(
        "--input-root", default=None,
        help="Override the sdc project_root read from --file-patterns (default: use the registry's own value).",
    )
    parser.add_argument("--output-root", default="data/", help="Local root to copy into (default: data/).")
    return parser.parse_args(argv)


def _build_config(args: argparse.Namespace) -> RetrievalConfig:
    file_patterns = load_file_patterns(args.file_patterns)
    if args.input_root is not None:
        file_patterns = replace(
            file_patterns, project_roots={**file_patterns.project_roots, "sdc": Path(args.input_root)}
        )
    retrieve = [
        RetrieveItem(object="sdc", pipeline=None, datatype="dwi", suffix=category) for category in args.categories
    ]
    return RetrievalConfig(
        output_root=Path(args.output_root),
        project="clinical_connectome",
        file_patterns_path=Path(args.file_patterns),
        file_patterns=file_patterns,
        datasets=args.datasets,
        group_filter=["ST"],  # every sdc subject is ST - see docs/guides/datasets.md
        subjects=None,
        retrieve=retrieve,
        include_tabular_data=False,  # participants_tsv_path() resolves via the `lesion` object's root, which
        # UKE/WAKEUP_acute (sdc-only) doesn't have - see docs/dev/retrieval.md
        overwrite=args.overwrite,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)

    try:
        config = _build_config(args)
    except (FileNotFoundError, ValueError) as exc:
        logging.error(str(exc))
        return 1

    return run(config, datetime.now())


if __name__ == "__main__":
    raise SystemExit(main())
