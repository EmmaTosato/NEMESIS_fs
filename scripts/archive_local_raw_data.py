"""One-off/repeatable script: shrinks large locally-cached raw-data directories under `data/`
by keeping a small, fixed sample of subjects in place (for notebooks/exploration) and packing
everything else into one verified `.tar.gz` archive per target - the originals are only deleted
after the archive has been read back and shown to contain exactly the files that were tarred.

Why this is safe: `data/` is documented (`.claude/CLAUDE.md`, `docs/guides/retrieval.md`,
`docs/guides/datasets.md`) as a disposable local cache of EBRAIN, never the source of truth -
`retrieve_data.py` can always re-pull anything archived here. The one exception is
`data/derived/features/masked_fc`, which is `mask_fc.py`'s own computed output, not an EBRAIN
copy - for that target, "restore" means either decompressing the archive back (lossless) or
re-running `mask_fc.py` from the raw WashU features + manual masks.

Two directory shapes are handled:
- "subject_dirs": one `sub-<ID>/...` subdirectory per subject directly under `root` (the 5
  `manual_masks` roots, and `WashU/features`). The kept sample is the first `n_sample` subject
  IDs in sorted order - arbitrary but deterministic, fine for exploration purposes.
- "atlas_combo_groups": `root` has one subdirectory per atlas combo (`Yan<n>TianS<n>Buckner7N`),
  each holding flat `sub-<ID>_masked_fc.csv` files directly - the kept sample is the first
  `n_sample` subject IDs common to *every* combo (sorted), so the sample looks the same across
  every atlas combo. Non-subject files (`mask_summary.csv`, `runs.csv`) and the pre-existing
  `demo/` directory are out of scope and never touched.

Every target's archive is written atomically (temp file + rename) and only replaces the
original directory entries it was built from - other subject dirs/files are left alone, whether
or not they were already pruned by a previous run of this script.

Usage (run from the repo root):
    # Report what would happen, touch nothing:
    PYTHONPATH=. conda run -n nemesis python scripts/archive_local_raw_data.py

    # Actually archive + delete:
    PYTHONPATH=. conda run -n nemesis python scripts/archive_local_raw_data.py --execute
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

_SUBJECT_DIR_RE = re.compile(r"^sub-[A-Za-z0-9]+$")
_ATLAS_COMBO_DIR_RE = re.compile(r"^Yan\d+TianS\d+Buckner7N$")
_MASKED_FC_SUBJECT_FILE_RE = re.compile(r"^(sub-[A-Za-z0-9]+)_masked_fc\.csv$")

_EBRAIN_RESTORE_HINT = (
    "The full data also still lives on EBRAIN - re-pull it with `retrieve_data.py` "
    "(see docs/guides/retrieval.md) instead of decompressing this archive, if you'd rather "
    "always work from the current server copy."
)
_MASKED_FC_RESTORE_HINT = (
    "This is derived output (mask_fc.py), not an EBRAIN copy - decompress this archive to get "
    "it back losslessly, or re-run mask_fc.py from the raw WashU features + manual masks "
    "(see docs/guides/fc_matrix_building.md) to regenerate it from scratch."
)


@dataclass(frozen=True)
class SubjectDirsTarget:
    root: Path
    restore_hint: str = _EBRAIN_RESTORE_HINT
    # Subject IDs that must always stay in the kept sample, regardless of sort order - e.g. a
    # subject hardcoded elsewhere in the repo as a fixed path (config, docs). Never rely on
    # "happens to sort first" for this: pin it explicitly here instead.
    must_keep: frozenset[str] = frozenset()


@dataclass(frozen=True)
class AtlasComboGroupsTarget:
    root: Path
    restore_hint: str = _MASKED_FC_RESTORE_HINT


TARGETS: list[SubjectDirsTarget | AtlasComboGroupsTarget] = [
    SubjectDirsTarget(
        Path("data/clinical_connectome/derivatives/UNIPD/WashU/manual_masks"),
        # config/pipelines/build_lesion_matrix.json's reference_template_path hardcodes this
        # subject's mask as the resampling reference - must never be archived away.
        must_keep=frozenset({"sub-STUNIPD0001"}),
    ),
    SubjectDirsTarget(Path("data/clinical_connectome/derivatives/UNIPD/PSP/manual_masks")),
    SubjectDirsTarget(Path("data/clinical_connectome/derivatives/UNIPD/PASPORT/manual_masks")),
    SubjectDirsTarget(Path("data/clinical_connectome/derivatives/UKLFR/stroke_UKLFR/manual_masks")),
    SubjectDirsTarget(Path("data/clinical_connectome/derivatives/UCL-UK/UCLStrokeData/manual_masks")),
    SubjectDirsTarget(Path("data/clinical_connectome/derivatives/UNIPD/WashU/features")),
    AtlasComboGroupsTarget(Path("data/derived/features/masked_fc")),
]


# --- subject listing / sampling -------------------------------------------------------------


def list_subject_dir_ids(root: Path) -> list[str]:
    """Sorted `sub-<ID>` subdirectory names directly under `root`. Raises if a top-level entry
    doesn't match that shape - an unrecognized entry needs a human look, not a silent skip or an
    accidental sweep into the archive."""
    ids = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or not _SUBJECT_DIR_RE.match(entry.name):
            raise ValueError(f"{root}: unexpected top-level entry {entry.name!r} (expected a sub-<ID> directory)")
        ids.append(entry.name)
    return ids


def select_sample_ids(
    subject_ids: Sequence[str], n_sample: int, must_keep: frozenset[str] = frozenset()
) -> tuple[list[str], list[str]]:
    """Splits `subject_ids` (deduplicated, sorted ascending) into (sample, to_archive).

    Every ID in `must_keep` is always in the sample - explicit, not incidental to sort order.
    The remaining sample slots are filled with the next IDs in sorted order (excluding
    `must_keep`). Raises if any `must_keep` ID isn't actually present, or if there are more of
    them than `n_sample` allows."""
    if n_sample <= 0:
        raise ValueError(f"n_sample must be positive, got {n_sample}")
    unique_sorted = sorted(set(subject_ids))
    if len(unique_sorted) != len(subject_ids):
        raise ValueError("subject_ids contains duplicates - fix the upstream listing before archiving")
    if n_sample >= len(unique_sorted):
        raise ValueError(f"n_sample={n_sample} >= total subjects ({len(unique_sorted)}) - nothing would be archived")
    unrecognized = must_keep - set(unique_sorted)
    if unrecognized:
        raise ValueError(f"must_keep subject(s) not found among the {len(unique_sorted)} discovered: {sorted(unrecognized)}")
    if len(must_keep) > n_sample:
        raise ValueError(f"must_keep has {len(must_keep)} subject(s), more than n_sample={n_sample} can hold")

    remaining_pool = [sid for sid in unique_sorted if sid not in must_keep]
    n_fill = n_sample - len(must_keep)
    sample = sorted(must_keep | set(remaining_pool[:n_fill]))
    to_archive = remaining_pool[n_fill:]
    return sample, to_archive


# --- "subject_dirs" shape: archive + delete + readme ------------------------------------------


def files_under_subject_dirs(root: Path, subject_ids: Sequence[str]) -> set[str]:
    """Relative (posix) paths of every file under the given subject dirs, relative to `root`."""
    paths: set[str] = set()
    for sid in subject_ids:
        subject_dir = root / sid
        if not subject_dir.is_dir():
            raise FileNotFoundError(f"{subject_dir} does not exist - re-list subject ids before archiving")
        paths.update(f.relative_to(root).as_posix() for f in subject_dir.rglob("*") if f.is_file())
    return paths


def archive_subject_dirs(root: Path, subject_ids: Sequence[str], archive_path: Path, *, overwrite: bool) -> None:
    """Tars `subject_ids`' directories (relative paths preserved) into `archive_path`, verifying
    the written archive contains exactly the files gathered from disk before it replaces any
    prior archive - atomic (temp file + rename), never silently overwrites."""
    if archive_path.exists() and not overwrite:
        raise FileExistsError(f"{archive_path} already exists - pass overwrite=True to replace it")
    expected = files_under_subject_dirs(root, subject_ids)
    if not expected:
        raise ValueError(f"{root}: no files found under the {len(subject_ids)} subject dir(s) to archive - nothing to do")

    tmp_path = archive_path.with_name(archive_path.name + ".tmp")
    with tarfile.open(tmp_path, "w:gz") as tar:
        for sid in subject_ids:
            tar.add(root / sid, arcname=sid)

    with tarfile.open(tmp_path, "r:gz") as tar:
        actual = {m.name for m in tar.getmembers() if m.isfile()}
    if actual != expected:
        tmp_path.unlink()
        missing, extra = sorted(expected - actual)[:5], sorted(actual - expected)[:5]
        raise RuntimeError(
            f"archive verification failed for {archive_path}: {len(expected - actual)} file(s) missing "
            f"(e.g. {missing}), {len(actual - expected)} unexpected extra file(s) (e.g. {extra}) - nothing was deleted"
        )
    tmp_path.rename(archive_path)
    logging.info("%s: archived %d subject dir(s), %d file(s) -> %s", root, len(subject_ids), len(expected), archive_path)


def delete_subject_dirs(root: Path, subject_ids: Sequence[str]) -> None:
    for sid in subject_ids:
        shutil.rmtree(root / sid)
    logging.info("%s: deleted %d archived subject dir(s), kept the rest as the local sample", root, len(subject_ids))


# --- "atlas_combo_groups" shape (masked_fc): archive + delete ---------------------------------


def list_atlas_combo_group_dirs(root: Path) -> list[Path]:
    groups = sorted(p for p in root.iterdir() if p.is_dir() and _ATLAS_COMBO_DIR_RE.match(p.name))
    if not groups:
        raise ValueError(f"{root}: no atlas-combo group directories found (expected e.g. Yan300TianS2Buckner7N)")
    return groups


def list_subject_ids_in_group(group_dir: Path) -> list[str]:
    ids = []
    for f in sorted(group_dir.iterdir()):
        if f.is_file():
            match = _MASKED_FC_SUBJECT_FILE_RE.match(f.name)
            if match:
                ids.append(match.group(1))
    return ids


def common_subject_ids(group_dirs: Sequence[Path]) -> list[str]:
    """Subject IDs present in *every* group dir, so the kept sample looks identical across
    atlas combos."""
    if not group_dirs:
        raise ValueError("no group directories given - nothing to sample from")
    id_sets = [set(list_subject_ids_in_group(g)) for g in group_dirs]
    return sorted(set.intersection(*id_sets))


def files_to_archive_in_groups(group_dirs: Sequence[Path], sample_ids: Sequence[str]) -> dict[Path, list[str]]:
    """Per group dir, the sorted subject-file basenames whose subject ID is *not* in
    `sample_ids` - these are archived+deleted; everything else (sample IDs, plus any
    non-subject file like mask_summary.csv) is left untouched."""
    sample_set = set(sample_ids)
    to_archive: dict[Path, list[str]] = {}
    for group_dir in group_dirs:
        filenames = []
        for f in sorted(group_dir.iterdir()):
            if f.is_file():
                match = _MASKED_FC_SUBJECT_FILE_RE.match(f.name)
                if match and match.group(1) not in sample_set:
                    filenames.append(f.name)
        to_archive[group_dir] = filenames
    return to_archive


def archive_atlas_combo_groups(root: Path, to_archive: dict[Path, list[str]], archive_path: Path, *, overwrite: bool) -> None:
    if archive_path.exists() and not overwrite:
        raise FileExistsError(f"{archive_path} already exists - pass overwrite=True to replace it")
    expected = {
        f"{group_dir.relative_to(root).as_posix()}/{name}" for group_dir, names in to_archive.items() for name in names
    }
    if not expected:
        raise ValueError(f"{root}: nothing to archive across {len(to_archive)} group dir(s)")

    tmp_path = archive_path.with_name(archive_path.name + ".tmp")
    with tarfile.open(tmp_path, "w:gz") as tar:
        for group_dir, names in to_archive.items():
            for name in names:
                tar.add(group_dir / name, arcname=f"{group_dir.relative_to(root).as_posix()}/{name}")

    with tarfile.open(tmp_path, "r:gz") as tar:
        actual = {m.name for m in tar.getmembers() if m.isfile()}
    if actual != expected:
        tmp_path.unlink()
        missing, extra = sorted(expected - actual)[:5], sorted(actual - expected)[:5]
        raise RuntimeError(
            f"archive verification failed for {archive_path}: {len(expected - actual)} file(s) missing "
            f"(e.g. {missing}), {len(actual - expected)} unexpected extra file(s) (e.g. {extra}) - nothing was deleted"
        )
    tmp_path.rename(archive_path)
    logging.info("%s: archived %d file(s) across %d group dir(s) -> %s", root, len(expected), len(to_archive), archive_path)


def delete_archived_group_files(to_archive: dict[Path, list[str]]) -> None:
    n = 0
    for group_dir, names in to_archive.items():
        for name in names:
            (group_dir / name).unlink()
            n += 1
    logging.info("deleted %d archived file(s), kept the common sample + non-subject files untouched", n)


# --- readme + orchestration --------------------------------------------------------------------


def write_archive_readme(root: Path, archive_path: Path, sample_ids: Sequence[str], n_archived: int, restore_hint: str) -> None:
    """archive_path is always a *sibling* of root (built via root.with_name(...) - see
    _process_subject_dirs_target/_process_atlas_combo_groups_target), never inside it, while this
    README is written inside root itself - the restore command below must account for that one
    directory level, or running it from root (the natural place to read the README from) fails to
    find the archive."""
    (root / "README_ARCHIVE.md").write_text(
        "# Locally pruned by scripts/archive_local_raw_data.py\n\n"
        f"Kept {len(sample_ids)} sample subject(s) in place for notebooks/exploration: {', '.join(sample_ids)}.\n\n"
        f"{n_archived} file(s) moved into `../{archive_path.name}` (one level up, next to this "
        f"directory - not inside it), verified against disk before deletion. Restore with (run from "
        "this directory):\n\n"
        f"```bash\ntar -xzf ../{archive_path.name} -C .\n```\n\n"
        f"{restore_hint}\n"
    )


def _process_subject_dirs_target(target: SubjectDirsTarget, *, n_sample: int, execute: bool, overwrite: bool) -> None:
    subject_ids = list_subject_dir_ids(target.root)
    sample, to_archive = select_sample_ids(subject_ids, n_sample, must_keep=target.must_keep)
    archive_path = target.root.with_name(target.root.name + "_archive.tar.gz")
    logging.info(
        "%s: %d subject(s) total, keeping %d as sample, archiving %d -> %s",
        target.root, len(subject_ids), len(sample), len(to_archive), archive_path,
    )
    if not execute:
        return
    archive_subject_dirs(target.root, to_archive, archive_path, overwrite=overwrite)
    delete_subject_dirs(target.root, to_archive)
    write_archive_readme(target.root, archive_path, sample, len(to_archive), target.restore_hint)


def _process_atlas_combo_groups_target(target: AtlasComboGroupsTarget, *, n_sample: int, execute: bool, overwrite: bool) -> None:
    group_dirs = list_atlas_combo_group_dirs(target.root)
    common_ids = common_subject_ids(group_dirs)
    sample, _ = select_sample_ids(common_ids, n_sample)
    to_archive = files_to_archive_in_groups(group_dirs, sample)
    n_files = sum(len(v) for v in to_archive.values())
    archive_path = target.root.with_name(target.root.name + "_archive.tar.gz")
    logging.info(
        "%s: %d group dir(s), %d subject(s) common to all groups, keeping %d as sample, archiving %d file(s) -> %s",
        target.root, len(group_dirs), len(common_ids), len(sample), n_files, archive_path,
    )
    if not execute:
        return
    archive_atlas_combo_groups(target.root, to_archive, archive_path, overwrite=overwrite)
    delete_archived_group_files(to_archive)
    write_archive_readme(target.root, archive_path, sample, n_files, target.restore_hint)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n-sample", type=int, default=10, help="Subjects to keep in place per target (default: 10)")
    parser.add_argument("--execute", action="store_true", help="Actually archive+delete. Without this flag, only reports what would happen.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing archive for a target instead of raising")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    for target in TARGETS:
        if not target.root.is_dir():
            logging.error("%s: target root does not exist", target.root)
            return 1

    for target in TARGETS:
        try:
            if isinstance(target, SubjectDirsTarget):
                _process_subject_dirs_target(target, n_sample=args.n_sample, execute=args.execute, overwrite=args.overwrite)
            elif isinstance(target, AtlasComboGroupsTarget):
                _process_atlas_combo_groups_target(target, n_sample=args.n_sample, execute=args.execute, overwrite=args.overwrite)
            else:
                raise TypeError(f"unknown target type: {type(target)!r}")
        except (ValueError, FileExistsError, FileNotFoundError, RuntimeError) as exc:
            logging.error("%s: %s", target.root, exc)
            return 1

    if not args.execute:
        logging.info("dry-run complete - re-run with --execute to actually archive and delete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
