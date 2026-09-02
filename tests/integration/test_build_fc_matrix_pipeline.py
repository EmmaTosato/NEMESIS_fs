"""Integration test: full build_fc_matrix.py CLI run (main()) on synthetic data.

No EBRAIN mount needed - build_fc_matrix operates only on already-masked
local CSVs (mask_fc.py's own output), so this is a pure tmp_path E2E, always
runs (no skipif).
"""

import json
import logging

import numpy as np
import pandas as pd

from src.pipeline import build_fc_matrix
from src.utils.artifacts import load_matrix


def _write_masked_fc(masked_fc_root, combo, subject, fc, dataset="siteA"):
    """Writes the masked FC csv plus this subject's row in the combo's own mask_summary.csv
    (2026-09-02: build_fc_matrix_from_masked now reads dataset back from there, mirroring
    mask_fc.py's real output shape - see src.features.functional.MASK_SUMMARY_FILENAME)."""
    combo_dir = masked_fc_root / combo
    combo_dir.mkdir(parents=True, exist_ok=True)
    fc.to_csv(combo_dir / f"{subject}_masked_fc.csv")
    summary_path = combo_dir / "mask_summary.csv"
    rows = pd.read_csv(summary_path).to_dict("records") if summary_path.is_file() else []
    rows.append({"subject_id": subject, "dataset": dataset, "n_compromised_nodes": 0})
    pd.DataFrame(rows).to_csv(summary_path, index=False)


def _write_config(tmp_path, masked_fc_root, output_root, overrides=None):
    cfg = {
        "project": "testproj",
        "masked_fc_root": str(masked_fc_root),
        "atlas_combos": ["ComboX"],
        "output_root": str(output_root),
        "session_name": "s1",
        "overwrite": False,
    }
    cfg.update(overrides or {})
    path = tmp_path / "build_fc_matrix.json"
    path.write_text(json.dumps(cfg))
    return path


def test_build_fc_matrix_end_to_end(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(build_fc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_fc_matrix, "LOGS_ROOT", tmp_path / "logs")

    masked_fc_root = tmp_path / "masked_fc"
    output_root = tmp_path / "out"
    node_names = ["A", "B", "C"]

    fc1 = pd.DataFrame([[1.0, 0.1, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]], index=node_names, columns=node_names)
    fc2 = pd.DataFrame([[1.0, 0.1, 0.9], [0.1, 1.0, 0.3], [0.9, 0.3, 1.0]], index=node_names, columns=node_names)
    fc2.loc["B", :] = np.nan
    fc2.loc[:, "B"] = np.nan
    _write_masked_fc(masked_fc_root, "ComboX", "sub-01", fc1)
    _write_masked_fc(masked_fc_root, "ComboX", "sub-02", fc2)

    config_path = _write_config(tmp_path, masked_fc_root, output_root)
    with caplog.at_level(logging.INFO):
        exit_code = build_fc_matrix.main(["--config", str(config_path)])
    assert exit_code == 0
    # docs/debugging/debug_25_08_26.md: a run's duration must be logged, success or not.
    assert "run duration:" in caplog.text

    combo_out_dirs = [p for p in (output_root / "ComboX").iterdir() if p.is_dir()]
    assert len(combo_out_dirs) == 1
    out_dir = combo_out_dirs[0]
    # effective_session_name = f"{config.session_name}-{combo}" (02-09-26) - the atlas_combo
    # is appended to the base session so two combos of the same cohort never collide on the
    # same output_dir/runs.csv session id (see test_build_fc_matrix_two_combos_get_distinct_
    # session_names_and_dont_collide below for the regression this actually guards against).
    assert out_dir.name.endswith("_s1-ComboX")

    X, metadata, extra_arrays = load_matrix(out_dir)
    assert list(metadata["subject_id"]) == ["sub-01", "sub-02"]
    assert X.shape == (2, 3)  # A__B, A__C, B__C - none dropped (A__C differs between subjects)
    assert np.isnan(X[1]).sum() == 2  # sub-02: A__B and B__C are NaN
    assert list(extra_arrays["edge_names"]) == ["A__B", "A__C", "B__C"]

    reports = list((tmp_path / "summaries" / "testproj").glob("*.md"))
    logs = list((tmp_path / "logs" / "testproj").glob("*.log"))
    assert len(reports) == 1
    assert len(logs) == 1

    runs_csv = (output_root / "runs.csv").read_text()
    assert "s1" in runs_csv
    assert "ComboX" in runs_csv


def test_build_fc_matrix_drops_constant_edge(tmp_path, monkeypatch):
    monkeypatch.setattr(build_fc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_fc_matrix, "LOGS_ROOT", tmp_path / "logs")

    masked_fc_root = tmp_path / "masked_fc"
    output_root = tmp_path / "out"
    node_names = ["A", "B", "C"]

    # A__C is 0.2 for both subjects (no NaN at all) - identical, must be dropped.
    fc1 = pd.DataFrame([[1.0, 0.1, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]], index=node_names, columns=node_names)
    fc2 = pd.DataFrame([[1.0, 0.5, 0.2], [0.5, 1.0, 0.6], [0.2, 0.6, 1.0]], index=node_names, columns=node_names)
    _write_masked_fc(masked_fc_root, "ComboX", "sub-01", fc1)
    _write_masked_fc(masked_fc_root, "ComboX", "sub-02", fc2)

    config_path = _write_config(tmp_path, masked_fc_root, output_root)
    exit_code = build_fc_matrix.main(["--config", str(config_path)])
    assert exit_code == 0

    out_dir = next((output_root / "ComboX").iterdir())
    X, _metadata, extra_arrays = load_matrix(out_dir)
    assert list(extra_arrays["edge_names"]) == ["A__B", "B__C"]  # A__C dropped
    assert X.shape == (2, 2)


def test_build_fc_matrix_missing_input_raises(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(build_fc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_fc_matrix, "LOGS_ROOT", tmp_path / "logs")

    config_path = _write_config(tmp_path, tmp_path / "does_not_exist", tmp_path / "out")
    with caplog.at_level(logging.INFO):
        exit_code = build_fc_matrix.main(["--config", str(config_path)])
    assert exit_code == 1
    # Duration must be logged on the error path too, not just on success.
    assert "run duration:" in caplog.text


def test_build_fc_matrix_one_combo_not_ready_does_not_abort_the_others(tmp_path, monkeypatch):
    """AUDIT_FINDINGS.md #29 regression: atlas_combos are independent - a combo whose
    masked_fc/<combo>/ input isn't ready yet (e.g. mask_fc.py not rerun for it) must not
    abort combos that ARE ready in the same run. Pre-fix, the first combo in config order
    (alphabetically "ComboMissing" < "ComboReady") aborted main() via return 1 before
    "ComboReady" - genuinely complete - was ever processed.
    """
    monkeypatch.setattr(build_fc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_fc_matrix, "LOGS_ROOT", tmp_path / "logs")

    masked_fc_root = tmp_path / "masked_fc"
    output_root = tmp_path / "out"
    node_names = ["A", "B", "C"]
    fc1 = pd.DataFrame([[1.0, 0.1, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]], index=node_names, columns=node_names)
    fc2 = pd.DataFrame([[1.0, 0.5, 0.2], [0.5, 1.0, 0.6], [0.2, 0.6, 1.0]], index=node_names, columns=node_names)
    _write_masked_fc(masked_fc_root, "ComboReady", "sub-01", fc1)
    _write_masked_fc(masked_fc_root, "ComboReady", "sub-02", fc2)
    # "ComboMissing" never got a masked_fc/ folder at all (mask_fc.py hasn't been run for it).

    config_path = _write_config(
        tmp_path, masked_fc_root, output_root, overrides={"atlas_combos": ["ComboMissing", "ComboReady"]}
    )
    exit_code = build_fc_matrix.main(["--config", str(config_path)])
    assert exit_code == 0

    combo_out_dirs = [p for p in (output_root / "ComboReady").iterdir() if p.is_dir()]
    assert len(combo_out_dirs) == 1
    assert not (output_root / "ComboMissing").exists()

    report_path = next((tmp_path / "summaries" / "testproj").glob("*.md"))
    report_text = report_path.read_text()
    assert "ComboReady" in report_text
    assert "Skipped" in report_text
    assert "ComboMissing" in report_text


def test_build_fc_matrix_two_combos_get_distinct_session_names_and_dont_collide(tmp_path, monkeypatch):
    """02-09-26 session-naming migration regression: config.session_name is only the base
    cohort ("s1" here) - build_fc_matrix.py must append each combo to it
    (effective_session_name) before using it in output_dir/runs.csv, or two atlas_combos
    processed the same day would produce dim_reduction.py-incompatible output (that pipeline's
    own output path is only .../<method>/<date>_<session_name>/, no atlas-dedicated subfolder
    like this one has - a bare shared "s1" would collide there even though it doesn't here)."""
    monkeypatch.setattr(build_fc_matrix, "REPORTS_ROOT", tmp_path / "summaries")
    monkeypatch.setattr(build_fc_matrix, "LOGS_ROOT", tmp_path / "logs")

    masked_fc_root = tmp_path / "masked_fc"
    output_root = tmp_path / "out"
    node_names = ["A", "B", "C"]
    fc = pd.DataFrame([[1.0, 0.1, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]], index=node_names, columns=node_names)
    _write_masked_fc(masked_fc_root, "ComboA", "sub-01", fc)
    _write_masked_fc(masked_fc_root, "ComboB", "sub-01", fc)

    config_path = _write_config(tmp_path, masked_fc_root, output_root, overrides={"atlas_combos": ["ComboA", "ComboB"]})
    exit_code = build_fc_matrix.main(["--config", str(config_path)])
    assert exit_code == 0

    out_dir_a = next((output_root / "ComboA").iterdir())
    out_dir_b = next((output_root / "ComboB").iterdir())
    assert out_dir_a.name.endswith("_s1-ComboA")
    assert out_dir_b.name.endswith("_s1-ComboB")
    assert out_dir_a != out_dir_b

    runs_csv = (output_root / "runs.csv").read_text()
    assert "s1-ComboA" in runs_csv
    assert "s1-ComboB" in runs_csv
