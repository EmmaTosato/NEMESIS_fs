"""Unit tests for src/utils/run_log.py."""

from datetime import datetime
from pathlib import Path

from src.utils.run_log import append_run_log_entry


def test_creates_file_with_header_on_first_entry(tmp_path):
    runs_md = tmp_path / "umap" / "RUNS.md"
    append_run_log_entry(
        runs_md, "run1", datetime(2026, 7, 20, 16, 30), "production", {"n_neighbors": 15}, Path("out/run1"), None
    )

    content = runs_md.read_text()
    assert content.startswith("# Run history — umap")
    assert "## run1 — 20-07-26 16:30 (production)" in content
    assert '"n_neighbors": 15' in content
    assert "Output: out/run1" in content
    assert "Note:" not in content  # run_notes=None -> no Note line


def test_appends_without_overwriting_previous_entries(tmp_path):
    runs_md = tmp_path / "RUNS.md"
    append_run_log_entry(runs_md, "run1", datetime(2026, 7, 20, 16, 30), "production", {}, Path("out/run1"), None)
    append_run_log_entry(runs_md, "run2", datetime(2026, 7, 21, 9, 0), "tuning", {}, Path("out/run2"), "picked from sweep")

    content = runs_md.read_text()
    assert "## run1" in content
    assert "## run2" in content
    assert content.index("## run1") < content.index("## run2")
    assert "Note: picked from sweep" in content
    # header only written once
    assert content.count("# Run history") == 1


def test_run_notes_included_when_provided(tmp_path):
    runs_md = tmp_path / "RUNS.md"
    append_run_log_entry(
        runs_md, "run1", datetime(2026, 7, 20, 16, 30), "production", {}, Path("out/run1"), "cambiati i parametri"
    )
    assert "Note: cambiati i parametri" in runs_md.read_text()
