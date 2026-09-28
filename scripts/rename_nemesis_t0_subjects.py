"""One-off script: canonicalize UNIPD/NEMESIS_T0 patient subject ids.

NEMESIS_T0's raw ids (`sub-p001`, `sub-c002`, ...) don't match the project's naming
convention (`sub-<ST|PD|GM><SITE>[HC]<NUM>`, see src/retrieval/dataset.py::group_of) -
every downstream module that discovers subjects by globbing `sub-*` directly
(src/features/lesion.py, sdc.py, subject_discovery.py) calls group_of() unconditionally
and would raise ValueError on these ids. This is not fixable in code alone: the join
between a tsv-derived id and a disk folder is by literal folder name, so the folders
themselves must be renamed, not just reinterpreted at read time.

Scope: only the `sub-p*` (patient) ids. The `sub-c*` (control) ids are left untouched -
they have no imaging data on disk (verified: 0 `sub-c*` folders under manual_masks/sdc)
and are out of scope regardless, since every populate_metadata.json run in this project
uses group_filter: ["ST"] (healthy controls excluded project-wide, see docs/dev/metadata.md).

Numbering: UNIPD is a single site-wide counter shared across WashU/PSP/PASPORT (verified
on disk: 0001-0251 / 0252-0487 / 0489-0585, no gaps reused). New ids continue from 0586.
The mapping covers the *union* of raw ids seen in the tsv and on disk (82 total) - not
their intersection (72) - because a tsv-only id (clinical row, no imaging) and a disk-only
id (imaging, no clinical row) are both legitimate, already-handled outcomes of
populate_metadata.py's inner join (reported as only_in_tsv/only_on_disk), but a disk
folder left with its raw `sub-p*` name would still break group_of() for any pipeline
that globs manual_masks/sdc directly, regardless of tsv membership.

Assigns numbers by ascending original numeric suffix (p001 -> 0586, p002 -> 0587, ...),
deterministic and reproducible from the raw ids alone.

Renames, per surviving `sub-p*` id:
- the subject directory itself, under both manual_masks/ and sdc/
- every file inside it (recursively) whose name starts with the old id
- the tsv's `participant_id` cell to the new canonical id, preserving the raw id in a
  new `participant_id_dmp` column (same pattern already used by UKE_SFB's raw tsv)

Usage (run from the repo root):
    # Report the mapping, touch nothing:
    PYTHONPATH=. conda run -n nemesis python scripts/rename_nemesis_t0_subjects.py

    # Actually rename on disk + rewrite the tsv:
    PYTHONPATH=. conda run -n nemesis python scripts/rename_nemesis_t0_subjects.py --execute
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

TSV_PATH = Path("data/clinical_connectome/metadata_tsv/participants_NEMESIS_T0.tsv")
DATASET_ROOT = Path("data/clinical_connectome/derivatives/UNIPD/NEMESIS_T0")
DATA_TREES = ("manual_masks", "sdc")

NEW_SITE = "UNIPD"
NEW_DISEASE = "ST"
START_NUM = 586  # first free UNIPD/ST number: WashU/PSP/PASPORT occupy 0001-0585, verified on disk

_RAW_PATIENT_ID_RE = re.compile(r"^sub-p(?P<num>\d+)$")
_NEW_ID_DIGITS = 4


@dataclass(frozen=True)
class RenamePlanEntry:
    old_id: str
    new_id: str
    in_tsv: bool
    on_disk: bool


def _raw_num(raw_id: str) -> int:
    match = _RAW_PATIENT_ID_RE.match(raw_id)
    if match is None:
        raise ValueError(f"{raw_id!r} does not match the expected raw NEMESIS_T0 patient id shape 'sub-p<num>'")
    return int(match["num"])


def load_tsv_patient_ids(tsv_path: Path) -> set[str]:
    with tsv_path.open(newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if not rows or "participant_id" not in rows[0]:
        raise ValueError(f"{tsv_path}: expected a 'participant_id' column")
    return {row["participant_id"] for row in rows if row["participant_id"].startswith("sub-p")}


def load_disk_patient_ids(dataset_root: Path) -> set[str]:
    ids: set[str] = set()
    for tree in DATA_TREES:
        tree_dir = dataset_root / tree
        if not tree_dir.is_dir():
            raise FileNotFoundError(f"{tree_dir}: expected data tree not found")
        ids |= {p.name for p in tree_dir.iterdir() if p.is_dir() and p.name.startswith("sub-p")}
    return ids


def build_plan(tsv_path: Path, dataset_root: Path) -> list[RenamePlanEntry]:
    """Deterministic old->new id mapping for every raw patient id seen in the tsv,
    on disk, or both - ordered by ascending original numeric suffix."""
    tsv_ids = load_tsv_patient_ids(tsv_path)
    disk_ids = load_disk_patient_ids(dataset_root)
    union = sorted(tsv_ids | disk_ids, key=_raw_num)

    duplicated_targets_guard: set[str] = set()
    plan = []
    for offset, raw_id in enumerate(union):
        new_id = f"sub-{NEW_DISEASE}{NEW_SITE}{START_NUM + offset:0{_NEW_ID_DIGITS}d}"
        if new_id in duplicated_targets_guard:
            raise ValueError(f"internal error: new id {new_id!r} assigned twice")
        duplicated_targets_guard.add(new_id)
        plan.append(RenamePlanEntry(old_id=raw_id, new_id=new_id, in_tsv=raw_id in tsv_ids, on_disk=raw_id in disk_ids))
    return plan


# --- disk rename -----------------------------------------------------------------------------


def rename_subject_on_disk(dataset_root: Path, entry: RenamePlanEntry, execute: bool) -> list[str]:
    """Renames entry.old_id -> entry.new_id under every data tree that has it (directory
    plus every file inside whose name starts with the old id). Returns the list of actions
    taken (or that would be taken, in dry-run)."""
    actions = []
    for tree in DATA_TREES:
        old_dir = dataset_root / tree / entry.old_id
        if not old_dir.is_dir():
            continue
        new_dir = dataset_root / tree / entry.new_id
        if new_dir.exists():
            raise FileExistsError(f"{new_dir}: already exists, refusing to overwrite")
        actions.append(f"{old_dir} -> {new_dir}")
        if execute:
            old_dir.rename(new_dir)
            for path in sorted(new_dir.rglob(f"{entry.old_id}*")):
                renamed = path.with_name(entry.new_id + path.name[len(entry.old_id) :])
                path.rename(renamed)
    return actions


# --- tsv rewrite -----------------------------------------------------------------------------


def rewrite_tsv(tsv_path: Path, plan: list[RenamePlanEntry], execute: bool) -> None:
    mapping = {entry.old_id: entry.new_id for entry in plan if entry.in_tsv}
    with tsv_path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = [*reader.fieldnames, "participant_id_dmp"]
        rows = list(reader)

    for row in rows:
        old_id = row["participant_id"]
        if old_id in mapping:
            row["participant_id_dmp"] = old_id
            row["participant_id"] = mapping[old_id]
        else:
            row["participant_id_dmp"] = ""

    if not execute:
        return
    fd, tmp_name = tempfile.mkstemp(prefix=f".{tsv_path.name}_tmp_", dir=tsv_path.parent)
    os.close(fd)
    try:
        with open(tmp_name, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_name, tsv_path)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise


# --- report ------------------------------------------------------------------------------------


def print_report(plan: list[RenamePlanEntry], execute: bool) -> None:
    both = [e for e in plan if e.in_tsv and e.on_disk]
    tsv_only = [e for e in plan if e.in_tsv and not e.on_disk]
    disk_only = [e for e in plan if e.on_disk and not e.in_tsv]

    mode = "EXECUTED" if execute else "DRY-RUN (nothing written)"
    print(f"--- rename_nemesis_t0_subjects: {mode} ---")
    print(f"total: {len(plan)} | both tsv+disk: {len(both)} | tsv-only: {len(tsv_only)} | disk-only: {len(disk_only)}")
    print(f"new id range: {plan[0].new_id} .. {plan[-1].new_id}")
    print()
    print(f"{'old_id':<12} {'new_id':<18} in_tsv  on_disk")
    for entry in plan:
        print(f"{entry.old_id:<12} {entry.new_id:<18} {str(entry.in_tsv):<7} {entry.on_disk}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--execute", action="store_true", help="Actually rename on disk and rewrite the tsv (default: dry-run report only)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    plan = build_plan(TSV_PATH, DATASET_ROOT)

    for entry in plan:
        actions = rename_subject_on_disk(DATASET_ROOT, entry, execute=args.execute)
        for action in actions:
            logging.info("%s: %s", "renamed" if args.execute else "would rename", action)

    rewrite_tsv(TSV_PATH, plan, execute=args.execute)
    logging.info("%s: %s", "rewrote" if args.execute else "would rewrite", TSV_PATH)

    print_report(plan, execute=args.execute)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
