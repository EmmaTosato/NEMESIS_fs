"""Unit tests for scripts/build_dim_reduction_strategies_csv.py."""

import csv
import json
import logging

import pytest

from scripts.build_dim_reduction_strategies_csv import (
    NO_METRIC,
    build_strategies_table,
    main,
    parse_sessions_md,
)

_SESSIONS_MD = """# Sessions — clinical_connectome

### Session 1.1

- Starting date: 21-07
- Datasets: UNIPD/WashU, UNIPD/PASPORT
- Modality: Lesion in 2D matrix volumetric

### Session 2

- Starting date:
- Datasets: UNIPD/WashU
- Modality: Features
"""


def _write_sessions_md(tmp_path, content=_SESSIONS_MD):
    path = tmp_path / "data_sessions.md"
    path.write_text(content)
    return path


def test_parse_sessions_md_reads_fixed_keys(tmp_path):
    sessions = parse_sessions_md(_write_sessions_md(tmp_path))

    assert set(sessions) == {"1.1", "2"}
    assert sessions["1.1"].starting_date == "21-07"
    assert sessions["1.1"].datasets == "UNIPD/WashU, UNIPD/PASPORT"
    assert sessions["1.1"].modality == "Lesion in 2D matrix volumetric"
    assert sessions["2"].starting_date == ""


def test_parse_sessions_md_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        parse_sessions_md(tmp_path / "does_not_exist.md")


def test_parse_sessions_md_missing_field_raises(tmp_path):
    content = "### Session 1.1\n\n- Starting date: 21-07\n- Datasets: UNIPD/WashU\n"  # no Modality
    with pytest.raises(ValueError, match="missing field"):
        parse_sessions_md(_write_sessions_md(tmp_path, content))


def test_parse_sessions_md_duplicate_session_raises(tmp_path):
    content = _SESSIONS_MD + "\n### Session 1.1\n\n- Starting date: 01-01\n- Datasets: x\n- Modality: y\n"
    with pytest.raises(ValueError, match="more than once"):
        parse_sessions_md(_write_sessions_md(tmp_path, content))


def test_parse_sessions_md_field_before_header_raises(tmp_path):
    content = "- Starting date: 21-07\n\n### Session 1.1\n- Datasets: x\n- Modality: y\n"
    with pytest.raises(ValueError, match="before any"):
        parse_sessions_md(_write_sessions_md(tmp_path, content))


def _write_runs_csv(path, rows, fieldnames=("session", "timestamp", "input_path", "params", "output", "notes")):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _existing_output(results_root, relative_path):
    """Creates `relative_path` under results_root and returns the "results/..."-prefixed
    string a real runs.csv row would store in its own `output` column (_output_dir_exists
    resolves it against results_root's parent, exactly like on real data)."""
    (results_root / relative_path).mkdir(parents=True, exist_ok=True)
    return f"results/{relative_path}"


def _production_row(session, params, output):
    return {
        "session": session, "timestamp": "01-01-26 00:00", "input_path": "in",
        "params": json.dumps(params), "output": output, "notes": "",
    }


def _tuning_row(session, base_params, tuning_grid, output):
    return {
        "session": session, "timestamp": "01-01-26 00:00", "input_path": "in",
        "params": json.dumps({"base_params": base_params, "tuning_grid": tuning_grid}), "output": output, "notes": "",
    }


def test_build_strategies_table_dedupes_same_strategy_across_production_and_tuning(tmp_path):
    results_root = tmp_path / "results"
    out_a = _existing_output(results_root, "lesion/dim_reduction/production/umap/a")
    out_b = _existing_output(results_root, "lesion/dim_reduction/production/umap/b")
    out_tuning = _existing_output(results_root, "lesion/dim_reduction/tuning/umap/tuning-run")
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "production" / "umap" / "runs.csv",
        [_production_row("s1.1", {"n_components": 2, "metric": "euclidean"}, out_a),
         _production_row("s1.1", {"n_components": 2, "metric": "euclidean"}, out_b)],
    )
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "tuning" / "umap" / "runs_tuning.csv",
        [_tuning_row("s1.1", {"n_components": 2, "metric": "euclidean"}, {"n_neighbors": [5, 15]}, out_tuning)],
        fieldnames=("session", "timestamp", "input_path", "params", "output", "notes"),
    )

    table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    # 2 production rows + 1 tuning row for the same (session, method, metric, n_components)
    # combination collapse into a single existence row - this index answers "does it exist",
    # not "how many times" (no production_runs/tuning_runs columns, dropped 16-08-26).
    assert len(table) == 1
    row = table.iloc[0]
    assert row["session"] == "s1.1"
    assert row["reduction_method"] == "umap"
    assert row["metric"] == "euclidean"
    assert row["n_components"] == 2
    assert row["modality"] == "Lesion in 2D matrix volumetric"
    assert row["datasets"] == "UNIPD/WashU, UNIPD/PASPORT"
    assert list(table.columns) == ["session", "modality", "datasets", "reduction_method", "metric", "n_components"]


def test_build_strategies_table_expands_tuning_row_over_swept_metric(tmp_path):
    # Regression test (16-08-26): a tuning row whose tuning_grid actually swept "metric" must
    # produce one strategy per swept value, not just base_params' single starting metric - a
    # real tsne tuning run exploring {euclidean, jaccard, dice} was previously collapsed to
    # "euclidean" only.
    results_root = tmp_path / "results"
    out_tuning = _existing_output(results_root, "lesion/dim_reduction/tuning/tsne/04-08_s1.1")
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "tuning" / "tsne" / "runs_tuning.csv",
        [_tuning_row(
            "s1.1", {"n_components": 2, "metric": "euclidean"},
            {"metric": ["euclidean", "jaccard", "dice"], "perplexity": [5, 15, 30]}, out_tuning,
        )],
        fieldnames=("session", "timestamp", "input_path", "params", "output", "notes"),
    )

    table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    assert set(zip(table["metric"], table["n_components"])) == {("euclidean", 2), ("jaccard", 2), ("dice", 2)}


def test_build_strategies_table_expands_tuning_row_over_swept_metric_and_n_components(tmp_path):
    results_root = tmp_path / "results"
    out_tuning = _existing_output(results_root, "lesion/dim_reduction/tuning/umap/03-08_s1.1")
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "tuning" / "umap" / "runs_tuning.csv",
        [_tuning_row(
            "s1.1", {"n_components": 2, "metric": "jaccard", "n_neighbors": 15},
            {"metric": ["jaccard", "dice"], "n_components": [5, 10]}, out_tuning,
        )],
        fieldnames=("session", "timestamp", "input_path", "params", "output", "notes"),
    )

    table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    assert set(zip(table["metric"], table["n_components"])) == {
        ("jaccard", 5), ("jaccard", 10), ("dice", 5), ("dice", 10),
    }


def test_build_strategies_table_distinguishes_different_metrics_and_n_components(tmp_path):
    results_root = tmp_path / "results"
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "production" / "umap" / "runs.csv",
        [
            _production_row("s1.1", {"n_components": 2, "metric": "euclidean"}, _existing_output(results_root, "a")),
            _production_row("s1.1", {"n_components": 3, "metric": "euclidean"}, _existing_output(results_root, "b")),
            _production_row("s1.1", {"n_components": 2, "metric": "dice"}, _existing_output(results_root, "c")),
        ],
    )

    table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    assert len(table) == 3
    assert set(zip(table["metric"], table["n_components"])) == {("euclidean", 2), ("euclidean", 3), ("dice", 2)}


def test_build_strategies_table_no_metric_sentinel_for_pca(tmp_path):
    results_root = tmp_path / "results"
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "production" / "pca" / "runs.csv",
        [_production_row("s1.1", {"n_components": 150}, _existing_output(results_root, "a"))],
    )

    table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    assert table.iloc[0]["metric"] == NO_METRIC


def test_build_strategies_table_undocumented_session_gets_placeholder(tmp_path, caplog):
    results_root = tmp_path / "results"
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "production" / "umap" / "runs.csv",
        [_production_row("s99", {"n_components": 2, "metric": "euclidean"}, _existing_output(results_root, "a"))],
    )

    with caplog.at_level(logging.WARNING):
        table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    assert table.iloc[0]["modality"] == "undocumented"
    assert table.iloc[0]["datasets"] == "undocumented"
    assert "no entry in" in caplog.text


def test_build_strategies_table_skips_row_with_missing_output_dir(tmp_path, caplog):
    # Regression test: a real run against this script initially reported a stale "no metric"
    # umap/2 strategy that traced back to a pre-reorg run whose output directory no longer
    # existed on disk - the row must be skipped, not counted as an existing strategy.
    results_root = tmp_path / "results"
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "production" / "umap" / "runs.csv",
        [_production_row("s1.1", {"n_components": 2}, "results/lesion/dim_reduction/umap/23-07_s1.1_d00")],
    )

    with caplog.at_level(logging.WARNING):
        table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    assert len(table) == 0
    assert "no longer exists on disk" in caplog.text


def test_build_strategies_table_output_not_prefixed_with_results_raises(tmp_path):
    results_root = tmp_path / "results"
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "production" / "umap" / "runs.csv",
        [_production_row("s1.1", {"n_components": 2, "metric": "euclidean"}, "some/other/path")],
    )

    with pytest.raises(ValueError, match="doesn't start with 'results/'"):
        build_strategies_table(results_root, _write_sessions_md(tmp_path))


def test_build_strategies_table_no_reduction_runs_returns_empty_table(tmp_path):
    results_root = tmp_path / "results"
    results_root.mkdir()

    table = build_strategies_table(results_root, _write_sessions_md(tmp_path))

    assert len(table) == 0
    assert list(table.columns) == ["session", "modality", "datasets", "reduction_method", "metric", "n_components"]


def test_main_writes_csv_to_results_root(tmp_path):
    results_root = tmp_path / "results"
    _write_runs_csv(
        results_root / "lesion" / "dim_reduction" / "production" / "umap" / "runs.csv",
        [_production_row("s1.1", {"n_components": 2, "metric": "euclidean"}, _existing_output(results_root, "a"))],
    )
    sessions_md = _write_sessions_md(tmp_path)

    exit_code = main(["--results-root", str(results_root), "--sessions-md", str(sessions_md)])

    assert exit_code == 0
    output_path = results_root / "dim_reduction_strategies.csv"
    assert output_path.is_file()
    with output_path.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["reduction_method"] == "umap"


def test_main_missing_sessions_md_returns_1_not_a_traceback(tmp_path):
    results_root = tmp_path / "results"
    results_root.mkdir()

    exit_code = main(["--results-root", str(results_root), "--sessions-md", str(tmp_path / "missing.md")])

    assert exit_code == 1
