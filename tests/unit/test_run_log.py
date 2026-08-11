"""Unit tests for src/utils/run_log.py."""

import csv
from datetime import datetime
from pathlib import Path

import pytest

from src.utils.run_log import append_run_log_entry


def _read_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="") as f:
        return list(csv.DictReader(f))


def test_creates_file_with_header_on_first_entry(tmp_path):
    log_dir = tmp_path / "umap"
    append_run_log_entry(
        log_dir, "s1.1_run1", datetime(2026, 7, 20, 16, 30), "production", {"n_neighbors": 15}, Path("out/run1"), None
    )

    rows = _read_rows(log_dir / "runs.csv")
    assert len(rows) == 1
    assert rows[0]["session"] == "s1.1"
    assert rows[0]["id"] == "run1"
    assert rows[0]["timestamp"] == "20-07-26 16:30"
    assert rows[0]["params"] == '{"n_neighbors": 15}'
    assert rows[0]["output"] == "out/run1"
    assert rows[0]["notes"] == ""  # run_notes=None -> empty field, not "None"


def test_run_id_without_underscore_has_empty_id(tmp_path):
    append_run_log_entry(tmp_path, "run1", datetime(2026, 7, 20, 16, 30), "production", {}, Path("out/run1"), None)
    rows = _read_rows(tmp_path / "runs.csv")
    assert rows[0]["session"] == "run1"
    assert rows[0]["id"] == ""


def test_appends_without_overwriting_previous_entries(tmp_path):
    append_run_log_entry(tmp_path, "s1_run1", datetime(2026, 7, 20, 16, 30), "production", {}, Path("out/run1"), None)
    append_run_log_entry(
        tmp_path, "s1_run2", datetime(2026, 7, 21, 9, 0), "production", {}, Path("out/run2"), "picked from sweep"
    )

    rows = _read_rows(tmp_path / "runs.csv")
    assert [row["id"] for row in rows] == ["run1", "run2"]
    assert rows[1]["notes"] == "picked from sweep"
    # header only written once, even after 2 appends
    assert (tmp_path / "runs.csv").read_text().count("session,id,timestamp,params,output,notes") == 1


def test_run_notes_included_when_provided(tmp_path):
    append_run_log_entry(
        tmp_path, "s1_run1", datetime(2026, 7, 20, 16, 30), "production", {}, Path("out/run1"), "cambiati i parametri"
    )
    assert _read_rows(tmp_path / "runs.csv")[0]["notes"] == "cambiati i parametri"


def test_extra_columns_prepended_to_header_and_row(tmp_path):
    append_run_log_entry(
        tmp_path,
        "s1_run1",
        datetime(2026, 7, 24, 10, 0),
        "production",
        {},
        Path("out/run1"),
        None,
        extra_columns={"reduction_method": "pca", "clustering_method": "kmeans"},
    )

    header = (tmp_path / "runs.csv").read_text().splitlines()[0]
    assert header == "reduction_method,clustering_method,session,id,timestamp,params,output,notes"
    row = _read_rows(tmp_path / "runs.csv")[0]
    assert row["reduction_method"] == "pca"
    assert row["clustering_method"] == "kmeans"
    assert row["id"] == "run1"


def test_extra_columns_shared_across_appends_to_same_file(tmp_path):
    append_run_log_entry(
        tmp_path,
        "s1_run1",
        datetime(2026, 7, 24, 10, 0),
        "production",
        {},
        Path("out/run1"),
        None,
        extra_columns={"reduction_method": "pca", "clustering_method": "kmeans"},
    )
    append_run_log_entry(
        tmp_path,
        "s1_run1",
        datetime(2026, 7, 24, 10, 5),
        "production",
        {},
        Path("out/run1"),
        None,
        extra_columns={"reduction_method": "pca", "clustering_method": "agglomerative"},
    )

    rows = _read_rows(tmp_path / "runs.csv")
    assert [row["clustering_method"] for row in rows] == ["kmeans", "agglomerative"]
    # header only written once, even after 2 appends
    assert (tmp_path / "runs.csv").read_text().count("reduction_method,clustering_method,session") == 1


def test_production_and_tuning_write_separate_files(tmp_path):
    append_run_log_entry(tmp_path, "s1_run1", datetime(2026, 7, 24, 10, 0), "production", {}, Path("out/prod"), None)
    append_run_log_entry(tmp_path, "s1_tune1", datetime(2026, 7, 24, 10, 5), "tuning", {}, Path("out/tune"), None)

    assert (tmp_path / "runs.csv").is_file()
    assert (tmp_path / "runs_tuning.csv").is_file()
    assert _read_rows(tmp_path / "runs.csv")[0]["id"] == "run1"
    assert _read_rows(tmp_path / "runs_tuning.csv")[0]["id"] == "tune1"


def test_unknown_run_type_raises_instead_of_silently_writing_to_tuning_file(tmp_path):
    """Regression: run_type picked its target file via `"runs.csv" if
    run_type == "production" else "runs_tuning.csv"` - a typo like
    "Production" or a future third run_type would have silently landed in
    runs_tuning.csv instead of raising."""
    with pytest.raises(ValueError, match="run_type"):
        append_run_log_entry(tmp_path, "s1_run1", datetime(2026, 7, 24, 10, 0), "Production", {}, Path("out"), None)
    assert not (tmp_path / "runs.csv").exists()
    assert not (tmp_path / "runs_tuning.csv").exists()
