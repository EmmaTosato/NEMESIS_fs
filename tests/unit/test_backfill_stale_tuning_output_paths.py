"""Unit tests for scripts/backfill_stale_tuning_output_paths.py."""

import csv
import logging

import pytest

from scripts.backfill_stale_tuning_output_paths import backfill_file, corrected_output, main


def test_corrected_output_swaps_method_and_tuning_segments_when_target_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results/lesion/dim_reduction/tuning/tsne/04-08_s1.1").mkdir(parents=True)

    fixed = corrected_output("results/lesion/dim_reduction/tsne/tuning/04-08_s1.1")

    assert fixed == "results/lesion/dim_reduction/tuning/tsne/04-08_s1.1"


def test_corrected_output_returns_none_if_neither_path_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert corrected_output("results/lesion/dim_reduction/tsne/tuning/29-07_s1.1") is None


def test_corrected_output_returns_none_if_output_already_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results/lesion/dim_reduction/tuning/tsne/13-08_s1.1").mkdir(parents=True)

    assert corrected_output("results/lesion/dim_reduction/tuning/tsne/13-08_s1.1") is None


def test_corrected_output_returns_none_for_unrelated_path_shape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert corrected_output("results/lesion/clustering/production/kmeans/10-08_s1") is None


def _write_runs_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["session", "id", "timestamp", "input_path", "params", "output", "notes"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _row(session, output, run_id="a"):
    return {"session": session, "id": run_id, "timestamp": "01-01-26 00:00", "input_path": "", "params": "{}", "output": output, "notes": ""}


def test_backfill_file_corrects_recoverable_rows_and_flags_unrecoverable_ones(tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results/lesion/dim_reduction/tuning/tsne/04-08_s1.1").mkdir(parents=True)
    csv_path = tmp_path / "results/lesion/dim_reduction/tuning/tsne/runs_tuning.csv"
    _write_runs_csv(
        csv_path,
        [
            _row("s1.1", "results/lesion/dim_reduction/tsne/tuning/04-08_s1.1", "a"),  # recoverable
            _row("s1.1", "results/lesion/dim_reduction/tsne/tuning/29-07_s1.1", "b"),  # unrecoverable
        ],
    )

    with caplog.at_level(logging.INFO):
        n_corrected, n_stale = backfill_file(csv_path)

    assert n_corrected == 1
    assert n_stale == 1
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["output"] == "results/lesion/dim_reduction/tuning/tsne/04-08_s1.1"
    assert rows[1]["output"] == "results/lesion/dim_reduction/tsne/tuning/29-07_s1.1"  # untouched
    assert "not found on disk" in caplog.text


def test_backfill_file_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results/lesion/dim_reduction/tuning/tsne/04-08_s1.1").mkdir(parents=True)
    csv_path = tmp_path / "results/lesion/dim_reduction/tuning/tsne/runs_tuning.csv"
    _write_runs_csv(csv_path, [_row("s1.1", "results/lesion/dim_reduction/tsne/tuning/04-08_s1.1", "a")])

    first = backfill_file(csv_path)
    second = backfill_file(csv_path)

    assert first == (1, 0)
    assert second == (0, 0)


def test_backfill_file_no_output_column_raises(tmp_path):
    csv_path = tmp_path / "runs.csv"
    csv_path.write_text("session,id\ns1,a\n")

    with pytest.raises(ValueError, match="no 'output' column"):
        backfill_file(csv_path)


def test_main_missing_results_root_returns_1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["--results-root", "does_not_exist"]) == 1


def test_main_no_runs_csv_files_returns_0(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()

    assert main(["--results-root", "results"]) == 0
