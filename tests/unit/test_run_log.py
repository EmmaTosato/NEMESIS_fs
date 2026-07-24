"""Unit tests for src/utils/run_log.py."""

import csv
from datetime import datetime
from pathlib import Path

from src.utils.run_log import append_run_log_entry


def _read_rows(runs_csv: Path) -> list[dict]:
    with runs_csv.open(newline="") as f:
        return list(csv.DictReader(f))


def test_creates_file_with_header_on_first_entry(tmp_path):
    runs_csv = tmp_path / "umap" / "runs.csv"
    append_run_log_entry(
        runs_csv, "run1", datetime(2026, 7, 20, 16, 30), "production", {"n_neighbors": 15}, Path("out/run1"), None
    )

    rows = _read_rows(runs_csv)
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run1"
    assert rows[0]["timestamp"] == "20-07-26 16:30"
    assert rows[0]["run_type"] == "production"
    assert rows[0]["params"] == '{"n_neighbors": 15}'
    assert rows[0]["output"] == "out/run1"
    assert rows[0]["notes"] == ""  # run_notes=None -> empty field, not "None"


def test_appends_without_overwriting_previous_entries(tmp_path):
    runs_csv = tmp_path / "runs.csv"
    append_run_log_entry(runs_csv, "run1", datetime(2026, 7, 20, 16, 30), "production", {}, Path("out/run1"), None)
    append_run_log_entry(runs_csv, "run2", datetime(2026, 7, 21, 9, 0), "tuning", {}, Path("out/run2"), "picked from sweep")

    rows = _read_rows(runs_csv)
    assert [row["run_id"] for row in rows] == ["run1", "run2"]
    assert rows[1]["run_type"] == "tuning"
    assert rows[1]["notes"] == "picked from sweep"
    # header only written once, even after 2 appends
    assert runs_csv.read_text().count("run_id,timestamp,run_type,params,output,notes") == 1


def test_run_notes_included_when_provided(tmp_path):
    runs_csv = tmp_path / "runs.csv"
    append_run_log_entry(
        runs_csv, "run1", datetime(2026, 7, 20, 16, 30), "production", {}, Path("out/run1"), "cambiati i parametri"
    )
    assert _read_rows(runs_csv)[0]["notes"] == "cambiati i parametri"


def test_extra_columns_prepended_to_header_and_row(tmp_path):
    runs_csv = tmp_path / "runs.csv"
    append_run_log_entry(
        runs_csv,
        "run1",
        datetime(2026, 7, 24, 10, 0),
        "production",
        {},
        Path("out/run1"),
        None,
        extra_columns={"reduction_method": "pca", "clustering_method": "kmeans"},
    )

    assert runs_csv.read_text().splitlines()[0] == "reduction_method,clustering_method,run_id,timestamp,run_type,params,output,notes"
    row = _read_rows(runs_csv)[0]
    assert row["reduction_method"] == "pca"
    assert row["clustering_method"] == "kmeans"
    assert row["run_id"] == "run1"


def test_extra_columns_shared_across_appends_to_same_file(tmp_path):
    runs_csv = tmp_path / "runs.csv"
    append_run_log_entry(
        runs_csv,
        "run1",
        datetime(2026, 7, 24, 10, 0),
        "production",
        {},
        Path("out/run1"),
        None,
        extra_columns={"reduction_method": "pca", "clustering_method": "kmeans"},
    )
    append_run_log_entry(
        runs_csv,
        "run1",
        datetime(2026, 7, 24, 10, 5),
        "production",
        {},
        Path("out/run1"),
        None,
        extra_columns={"reduction_method": "pca", "clustering_method": "agglomerative"},
    )

    rows = _read_rows(runs_csv)
    assert [row["clustering_method"] for row in rows] == ["kmeans", "agglomerative"]
    # header only written once, even after 2 appends
    assert runs_csv.read_text().count("reduction_method,clustering_method,run_id") == 1
