"""Unit tests for scripts/archive_local_raw_data.py."""

import subprocess
import tarfile

import pytest

from scripts.archive_local_raw_data import (
    AtlasComboGroupsTarget,
    SubjectDirsTarget,
    archive_atlas_combo_groups,
    archive_subject_dirs,
    common_subject_ids,
    delete_archived_group_files,
    delete_subject_dirs,
    files_to_archive_in_groups,
    files_under_subject_dirs,
    list_atlas_combo_group_dirs,
    list_subject_dir_ids,
    list_subject_ids_in_group,
    main,
    select_sample_ids,
)


def _make_subject_dirs(root, subject_ids, filename="mask.nii.gz"):
    for sid in subject_ids:
        subdir = root / sid / "anat"
        subdir.mkdir(parents=True)
        (subdir / f"{sid}_{filename}").write_text(f"content-{sid}")


def _make_atlas_combo_groups(root, combo_names, subject_ids_per_combo):
    for combo, subject_ids in zip(combo_names, subject_ids_per_combo):
        combo_dir = root / combo
        combo_dir.mkdir(parents=True)
        for sid in subject_ids:
            (combo_dir / f"{sid}_masked_fc.csv").write_text(f"content-{combo}-{sid}")
        (combo_dir / "mask_summary.csv").write_text("summary")


# --- list_subject_dir_ids ----------------------------------------------------------------------


def test_list_subject_dir_ids_returns_sorted_names(tmp_path):
    _make_subject_dirs(tmp_path, ["sub-B002", "sub-A001", "sub-C003"])

    assert list_subject_dir_ids(tmp_path) == ["sub-A001", "sub-B002", "sub-C003"]


def test_list_subject_dir_ids_ignores_top_level_files(tmp_path):
    """Regression: files alongside the subject dirs used to be fatal - including
    README_ARCHIVE.md, which this very script writes there, so a second run over its own
    output always crashed. A hand-written manifest beside it broke it the same way."""
    _make_subject_dirs(tmp_path, ["sub-A001"])
    (tmp_path / ".DS_Store").write_text("")
    (tmp_path / "README_ARCHIVE.md").write_text("# pruned")
    (tmp_path / "features_archive_subjects.tsv").write_text("subject_id\tsource\n")

    assert list_subject_dir_ids(tmp_path) == ["sub-A001"]


def test_list_subject_dir_ids_still_raises_on_unexpected_directory(tmp_path):
    _make_subject_dirs(tmp_path, ["sub-A001"])
    (tmp_path / "leftovers").mkdir()

    with pytest.raises(ValueError, match="unexpected top-level directory"):
        list_subject_dir_ids(tmp_path)


# --- select_sample_ids ---------------------------------------------------------------------------


def test_select_sample_ids_splits_first_n_sorted_as_sample():
    sample, to_archive = select_sample_ids(["sub-C", "sub-A", "sub-B", "sub-D"], n_sample=2)

    assert sample == ["sub-A", "sub-B"]
    assert to_archive == ["sub-C", "sub-D"]


def test_select_sample_ids_raises_on_non_positive_n_sample():
    with pytest.raises(ValueError, match="must be positive"):
        select_sample_ids(["sub-A", "sub-B"], n_sample=0)


def test_select_sample_ids_raises_when_n_sample_covers_everything():
    with pytest.raises(ValueError, match="nothing would be archived"):
        select_sample_ids(["sub-A", "sub-B"], n_sample=2)


def test_select_sample_ids_raises_on_duplicates():
    with pytest.raises(ValueError, match="duplicates"):
        select_sample_ids(["sub-A", "sub-A", "sub-B"], n_sample=1)


def test_select_sample_ids_always_keeps_must_keep_even_if_it_sorts_last():
    sample, to_archive = select_sample_ids(["sub-A", "sub-B", "sub-C", "sub-Z"], n_sample=2, must_keep=frozenset({"sub-Z"}))

    assert sample == ["sub-A", "sub-Z"]
    assert to_archive == ["sub-B", "sub-C"]


def test_select_sample_ids_raises_if_must_keep_subject_not_found():
    with pytest.raises(ValueError, match="must_keep subject.*not found"):
        select_sample_ids(["sub-A", "sub-B"], n_sample=1, must_keep=frozenset({"sub-GONE"}))


def test_select_sample_ids_raises_if_must_keep_exceeds_n_sample():
    with pytest.raises(ValueError, match="more than n_sample"):
        select_sample_ids(["sub-A", "sub-B", "sub-C"], n_sample=1, must_keep=frozenset({"sub-A", "sub-B"}))


# --- subject_dirs archive/delete regression (the core "no silent data loss" behavior) ----------


def test_archive_subject_dirs_writes_a_verified_archive_containing_every_file(tmp_path):
    _make_subject_dirs(tmp_path, ["sub-A001", "sub-B002"])
    archive_path = tmp_path / "manual_masks_archive.tar.gz"

    archive_subject_dirs(tmp_path, ["sub-A001", "sub-B002"], archive_path, overwrite=False)

    with tarfile.open(archive_path, "r:gz") as tar:
        names = {m.name for m in tar.getmembers() if m.isfile()}
    assert names == {"sub-A001/anat/sub-A001_mask.nii.gz", "sub-B002/anat/sub-B002_mask.nii.gz"}


def test_archive_subject_dirs_raises_on_existing_archive_without_overwrite(tmp_path):
    _make_subject_dirs(tmp_path, ["sub-A001"])
    archive_path = tmp_path / "manual_masks_archive.tar.gz"
    archive_path.write_text("pre-existing")

    with pytest.raises(FileExistsError, match="already exists"):
        archive_subject_dirs(tmp_path, ["sub-A001"], archive_path, overwrite=False)


def test_archive_then_delete_subject_dirs_preserves_data_losslessly(tmp_path):
    """Regression for the core safety property: after archive+delete, every archived file's
    content is still recoverable from the .tar.gz, and the sample subject was never touched."""
    _make_subject_dirs(tmp_path, ["sub-A001", "sub-B002", "sub-C003"])
    archive_path = tmp_path / "manual_masks_archive.tar.gz"

    archive_subject_dirs(tmp_path, ["sub-B002", "sub-C003"], archive_path, overwrite=False)
    delete_subject_dirs(tmp_path, ["sub-B002", "sub-C003"])

    assert not (tmp_path / "sub-B002").exists()
    assert not (tmp_path / "sub-C003").exists()
    assert (tmp_path / "sub-A001/anat/sub-A001_mask.nii.gz").read_text() == "content-sub-A001"
    with tarfile.open(archive_path, "r:gz") as tar:
        extracted = tar.extractfile("sub-B002/anat/sub-B002_mask.nii.gz").read().decode()
    assert extracted == "content-sub-B002"


def test_files_under_subject_dirs_raises_if_a_subject_dir_is_missing(tmp_path):
    _make_subject_dirs(tmp_path, ["sub-A001"])

    with pytest.raises(FileNotFoundError, match="does not exist"):
        files_under_subject_dirs(tmp_path, ["sub-A001", "sub-GONE"])


# --- atlas_combo_groups (masked_fc shape) --------------------------------------------------------


def test_list_atlas_combo_group_dirs_ignores_non_matching_entries(tmp_path):
    _make_atlas_combo_groups(tmp_path, ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"], [["sub-A001"], ["sub-A001"]])
    (tmp_path / "demo").mkdir()
    (tmp_path / "runs.csv").write_text("x")

    groups = list_atlas_combo_group_dirs(tmp_path)

    assert [g.name for g in groups] == ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"]


def test_list_subject_ids_in_group_ignores_non_subject_files(tmp_path):
    _make_atlas_combo_groups(tmp_path, ["Yan100TianS1Buckner7N"], [["sub-A001", "sub-B002"]])

    ids = list_subject_ids_in_group(tmp_path / "Yan100TianS1Buckner7N")

    assert ids == ["sub-A001", "sub-B002"]


def test_common_subject_ids_intersects_across_groups(tmp_path):
    _make_atlas_combo_groups(
        tmp_path,
        ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"],
        [["sub-A001", "sub-B002", "sub-C003"], ["sub-B002", "sub-C003", "sub-D004"]],
    )
    groups = list_atlas_combo_group_dirs(tmp_path)

    assert common_subject_ids(groups) == ["sub-B002", "sub-C003"]


def test_files_to_archive_in_groups_excludes_sample_and_non_subject_files(tmp_path):
    _make_atlas_combo_groups(tmp_path, ["Yan100TianS1Buckner7N"], [["sub-A001", "sub-B002", "sub-C003"]])
    groups = list_atlas_combo_group_dirs(tmp_path)

    to_archive = files_to_archive_in_groups(groups, sample_ids=["sub-A001"])

    combo_dir = tmp_path / "Yan100TianS1Buckner7N"
    assert to_archive[combo_dir] == ["sub-B002_masked_fc.csv", "sub-C003_masked_fc.csv"]


def test_archive_then_delete_atlas_combo_groups_keeps_sample_and_non_subject_files(tmp_path):
    _make_atlas_combo_groups(
        tmp_path,
        ["Yan100TianS1Buckner7N", "Yan200TianS2Buckner7N"],
        [["sub-A001", "sub-B002"], ["sub-A001", "sub-B002"]],
    )
    groups = list_atlas_combo_group_dirs(tmp_path)
    to_archive = files_to_archive_in_groups(groups, sample_ids=["sub-A001"])
    archive_path = tmp_path / "masked_fc_archive.tar.gz"

    archive_atlas_combo_groups(tmp_path, to_archive, archive_path, overwrite=False)
    delete_archived_group_files(to_archive)

    # sample subject and non-subject files survive in place
    assert (tmp_path / "Yan100TianS1Buckner7N/sub-A001_masked_fc.csv").exists()
    assert (tmp_path / "Yan100TianS1Buckner7N/mask_summary.csv").exists()
    # archived subject is gone from disk but recoverable from the archive
    assert not (tmp_path / "Yan100TianS1Buckner7N/sub-B002_masked_fc.csv").exists()
    with tarfile.open(archive_path, "r:gz") as tar:
        names = {m.name for m in tar.getmembers() if m.isfile()}
    assert names == {
        "Yan100TianS1Buckner7N/sub-B002_masked_fc.csv",
        "Yan200TianS2Buckner7N/sub-B002_masked_fc.csv",
    }


# --- main() orchestration (dry-run vs execute) ---------------------------------------------------


def test_main_dry_run_does_not_touch_the_filesystem(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "manual_masks"
    root.mkdir()
    _make_subject_dirs(root, [f"sub-{i:03d}" for i in range(5)])
    import scripts.archive_local_raw_data as module

    monkeypatch.setattr(module, "TARGETS", [SubjectDirsTarget(root)])

    exit_code = main(["--n-sample", "2"])

    assert exit_code == 0
    assert not (root.parent / "manual_masks_archive.tar.gz").exists()
    assert len(list(root.iterdir())) == 5


def test_main_execute_archives_and_prunes_leaving_readme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "manual_masks"
    root.mkdir()
    _make_subject_dirs(root, [f"sub-{i:03d}" for i in range(5)])
    import scripts.archive_local_raw_data as module

    monkeypatch.setattr(module, "TARGETS", [SubjectDirsTarget(root)])

    exit_code = main(["--n-sample", "2", "--execute"])

    assert exit_code == 0
    remaining = sorted(p.name for p in root.iterdir() if p.is_dir())
    assert remaining == ["sub-000", "sub-001"]
    assert (root.parent / "manual_masks_archive.tar.gz").exists()
    assert (root / "README_ARCHIVE.md").exists()


def test_pruning_records_the_true_population_in_a_manifest(tmp_path, monkeypatch):
    """A pruned directory is indistinguishable from a genuinely small one by a filesystem scan
    alone - scripts/populate_metadata.py's has_* flags reported 10 WashU feature subjects instead
    of 225 for exactly this reason. The manifest is the machine-readable record of who really
    exists, readable without decompressing anything."""
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "features"
    root.mkdir()
    _make_subject_dirs(root, [f"sub-{i:03d}" for i in range(5)])
    import scripts.archive_local_raw_data as module

    monkeypatch.setattr(module, "TARGETS", [SubjectDirsTarget(root)])
    assert main(["--n-sample", "2", "--execute"]) == 0

    manifest = root / "features_archive_subjects.tsv"
    rows = [line.split("\t") for line in manifest.read_text().splitlines()[1:]]
    assert {subject_id for subject_id, source in rows if source == "kept_in_place"} == {"sub-000", "sub-001"}
    assert {subject_id for subject_id, source in rows if source == "archive"} == {"sub-002", "sub-003", "sub-004"}
    # the archived subjects are genuinely gone from disk - the manifest is the only local record
    assert not (root / "sub-004").exists()


def test_readme_reports_the_true_total_and_points_at_the_manifest(tmp_path, monkeypatch):
    """The README is the human-facing summary: totals plus a pointer to the manifest,
    deliberately not a second copy of the subject lists (which would be free to drift)."""
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "features"
    root.mkdir()
    _make_subject_dirs(root, [f"sub-{i:03d}" for i in range(5)])
    import scripts.archive_local_raw_data as module

    monkeypatch.setattr(module, "TARGETS", [SubjectDirsTarget(root)])
    assert main(["--n-sample", "2", "--execute"]) == 0

    readme = (root / "README_ARCHIVE.md").read_text()
    assert "5 subject(s) in total" in readme
    assert "2 kept in place, 3 inside the archive" in readme
    assert "features_archive_subjects.tsv" in readme
    assert "sub-004" not in readme  # the archived list lives in the manifest, not here


def test_readme_restore_command_actually_restores_the_archived_subjects(tmp_path, monkeypatch):
    """Regression: write_archive_readme used to instruct `tar -xzf <archive>.tar.gz -C .` run from
    root - but archive_path is a *sibling* of root (one level up), not inside it, so that exact
    command failed to find the archive when run, as documented, from root itself. This test
    literally runs the README's own restore command (not a paraphrase of it) and checks the
    archived subject actually comes back."""
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "manual_masks"
    root.mkdir()
    _make_subject_dirs(root, [f"sub-{i:03d}" for i in range(5)])
    import scripts.archive_local_raw_data as module

    monkeypatch.setattr(module, "TARGETS", [SubjectDirsTarget(root)])
    exit_code = main(["--n-sample", "2", "--execute"])
    assert exit_code == 0
    assert not (root / "sub-004").exists()  # archived away

    readme = (root / "README_ARCHIVE.md").read_text()
    restore_command = readme.split("```bash\n")[1].split("\n```")[0]
    subprocess.run(restore_command, shell=True, cwd=root, check=True)

    assert (root / "sub-004" / "anat" / "sub-004_mask.nii.gz").exists()


def test_main_execute_keeps_must_keep_subject_even_when_it_sorts_last(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "manual_masks"
    root.mkdir()
    _make_subject_dirs(root, [f"sub-{i:03d}" for i in range(5)] + ["sub-ZZZ"])
    import scripts.archive_local_raw_data as module

    monkeypatch.setattr(module, "TARGETS", [SubjectDirsTarget(root, must_keep=frozenset({"sub-ZZZ"}))])

    exit_code = main(["--n-sample", "2", "--execute"])

    assert exit_code == 0
    remaining = sorted(p.name for p in root.iterdir() if p.is_dir())
    assert remaining == ["sub-000", "sub-ZZZ"]


def test_main_returns_1_and_touches_nothing_if_a_target_root_is_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import scripts.archive_local_raw_data as module

    monkeypatch.setattr(module, "TARGETS", [SubjectDirsTarget(tmp_path / "does_not_exist")])

    assert main(["--execute"]) == 1
