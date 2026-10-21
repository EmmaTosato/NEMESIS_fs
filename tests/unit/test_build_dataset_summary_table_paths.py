"""`scripts/build_dataset_summary_table.py`: conteggi, LaTeX e rami di errore.

`pdflatex`/`pdftoppm` sono I/O esterno e lenti: si simula solo `subprocess.run`/`shutil.which`, mai il codice
sotto test (conteggi, template, argomenti passati ai due programmi).
"""

from __future__ import annotations

import subprocess
import sys

import pandas as pd
import pytest

import scripts.build_dataset_summary_table as table
from src.utils import participants as participants_registry
from tests.factories.ids import subject_id


def _registry(rows):
    return pd.DataFrame(rows, columns=["dataset", "has_lesion", "has_sdc"])


def test_count_per_dataset_sums_flags_keeping_first_appearance_order():
    registry = _registry([
        ("B", True, False), ("A", True, True), ("B", True, False), ("A", False, True), ("B", False, False),
    ])
    counts = table.count_per_dataset(registry)
    assert list(counts.index) == ["B", "A"]
    assert counts.loc["B"].to_dict() == {"has_lesion": 2, "has_sdc": 0}
    assert counts.loc["A"].to_dict() == {"has_lesion": 1, "has_sdc": 2}
    assert counts.dtypes.eq(int).all()


def test_render_latex_sorts_by_lesion_count_prints_dash_for_zero_sdc_and_totals():
    counts = pd.DataFrame(
        {"has_lesion": [3, 10], "has_sdc": [0, 7]}, index=pd.Index(["UNI_PD/X", "WashU"], name="dataset")
    )
    tex = table.render_latex(counts)
    assert tex.index("WashU") < tex.index("UNI")  # decrescente per lesioni
    assert r"UNI\_PD / X & 3 & -- \\" in tex  # escape di `_` e `/`, trattino al posto di 0
    assert r"WashU & 10 & 7 \\" in tex
    assert r"\textbf{13} & \textbf{7}" in tex


def test_count_groups_counts_st_and_hc_from_sub_folders_only(tmp_path):
    for sid in (subject_id(1), subject_id(2), subject_id(1, group="HC")):
        (tmp_path / sid).mkdir()
    (tmp_path / "notes.txt").write_text("x")  # un file non è un soggetto
    (tmp_path / "other_dir").mkdir()  # una cartella senza prefisso sub- nemmeno
    assert table.count_groups(tmp_path) == {"ST": 2, "HC": 1}


def test_count_groups_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="features directory not found"):
        table.count_groups(tmp_path / "absent")


def test_count_groups_with_no_subject_folder_raises_instead_of_a_table_of_zeros(tmp_path):
    (tmp_path / "other").mkdir()
    with pytest.raises(ValueError, match="no sub-"):
        table.count_groups(tmp_path)


def test_count_groups_rejects_a_group_outside_st_hc(tmp_path, monkeypatch):
    (tmp_path / subject_id(1)).mkdir()
    monkeypatch.setattr(table, "group_of", lambda subject: "PD")
    with pytest.raises(ValueError, match="group 'PD' not in"):
        table.count_groups(tmp_path)


def test_render_group_latex_rows_and_total():
    tex = table.render_group_latex({"ST": 4, "HC": 2})
    assert r"Stroke (ST) & 4 \\" in tex
    assert r"Healthy Controls (HC) & 2 \\" in tex
    assert r"\textbf{6}" in tex


@pytest.mark.parametrize("missing", ["pdflatex", "pdftoppm"])
def test_compile_to_png_names_the_missing_tool_and_writes_nothing(tmp_path, monkeypatch, missing):
    monkeypatch.setattr(table.shutil, "which", lambda tool: None if tool == missing else f"/bin/{tool}")
    with pytest.raises(RuntimeError, match=missing):
        table.compile_to_png("t", "tex", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_compile_to_png_writes_tex_copies_pdf_and_calls_pdftoppm_with_the_right_args(tmp_path, monkeypatch):
    calls = []

    def fake_run(cmd, cwd=None, check=None, capture_output=None):
        calls.append(cmd)
        if cmd[0] == "pdflatex":
            (table.Path(cwd) / "t.pdf").write_bytes(b"%PDF")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(table.shutil, "which", lambda tool: f"/bin/{tool}")
    monkeypatch.setattr(table.subprocess, "run", fake_run)

    out = tmp_path / "nested" / "out"
    table.compile_to_png("t", "TEXSOURCE", out)

    assert (out / "t.tex").read_text() == "TEXSOURCE"
    assert (out / "t.pdf").read_bytes() == b"%PDF"
    assert [c[0] for c in calls] == ["pdflatex", "pdftoppm"]
    assert "-halt-on-error" in calls[0]
    assert str(table.PNG_DPI) in calls[1] and calls[1][-1] == str(out / "t")


def test_compile_to_png_propagates_a_latex_failure_and_leaves_no_pdf(tmp_path, monkeypatch):
    def failing_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(table.shutil, "which", lambda tool: f"/bin/{tool}")
    monkeypatch.setattr(table.subprocess, "run", failing_run)
    with pytest.raises(subprocess.CalledProcessError):
        table.compile_to_png("t", "bad", tmp_path / "out")
    assert not (tmp_path / "out" / "t.pdf").exists()


@pytest.fixture
def registry_root(tmp_path, monkeypatch):
    root = tmp_path / "metadata"
    root.mkdir()
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", root)
    (root / "participants.csv").write_text(
        "subject_id,original_id,dataset,disease_id,has_lesion,has_sdc,has_features\n"
        "sub-STUNIPD0001,a,UNIPD,ST,True,True,False\n"
        "sub-STUNIPD0002,b,UNIPD,ST,True,False,False\n"
        "sub-STUCLUK0001,c,UCL,ST,True,False,False\n"
    )
    return root


def _run_main(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["build_dataset_summary_table.py", *args])
    return table.main()


def test_main_writes_dataset_table_only_without_features_dir(registry_root, tmp_path, monkeypatch, capsys):
    compiled = []
    monkeypatch.setattr(table, "compile_to_png", lambda name, tex, out: compiled.append((name, tex, out)))

    assert _run_main(monkeypatch, "--output-dir", str(tmp_path / "tables")) == 0

    assert [c[0] for c in compiled] == [table.DATASET_TABLE_NAME]
    assert compiled[0][2] == tmp_path / "tables"
    assert r"UNIPD & 2 & 1 \\" in compiled[0][1]
    assert "tables written to" in capsys.readouterr().out


def test_main_with_features_dir_also_writes_group_table(registry_root, tmp_path, monkeypatch, capsys):
    features = tmp_path / "features"
    for sid in (subject_id(1), subject_id(1, group="HC")):
        (features / sid).mkdir(parents=True)
    compiled = []
    monkeypatch.setattr(table, "compile_to_png", lambda name, tex, out: compiled.append((name, tex)))

    assert _run_main(monkeypatch, "--output-dir", str(tmp_path / "t"), "--features-dir", str(features)) == 0

    assert [c[0] for c in compiled] == [table.DATASET_TABLE_NAME, table.GROUP_TABLE_NAME]
    assert r"Stroke (ST) & 1 \\" in compiled[1][1]
    assert "{'ST': 1, 'HC': 1}" in capsys.readouterr().out


def test_main_without_registry_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(participants_registry, "METADATA_ROOT", tmp_path / "empty")
    monkeypatch.setattr(table, "compile_to_png", lambda *a: pytest.fail("non deve compilare senza registro"))
    with pytest.raises(FileNotFoundError, match="subject registry not found"):
        _run_main(monkeypatch, "--output-dir", str(tmp_path / "t"))
