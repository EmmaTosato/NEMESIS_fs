"""Test a proprietà delle funzioni pure di `src/pipeline/compute_lesion_metadata.py` e
`compute_sdc_metadata.py`: scrittura atomica del CSV, payload di config serializzabile, nome del
file di config accanto al CSV, report che non crolla su colonne tutte NaN o coorti vuote.

Il monkeypatch e' usato solo per simulare un guasto di I/O (`os.replace`, `DataFrame.to_csv`) e per
puntare la cartella dei report in una cartella temporanea.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis.build_config import LesionMetadataConfig, SdcMetadataConfig
from src.features.lesion import LesionGrid, _metadata_columns
from src.features.lesion_location import LOCATION_CATEGORIES, LesionAtlas, LesionLocationSpec
from src.pipeline import compute_lesion_metadata as lesion_pipeline
from src.pipeline import compute_sdc_metadata as sdc_pipeline

WRITERS = [pytest.param(lesion_pipeline._write_csv, id="lesion"), pytest.param(sdc_pipeline._write_csv, id="sdc")]

grid_names = st.lists(st.text("abcdXYZ0123", min_size=1, max_size=5), min_size=1, max_size=3, unique=True)


def grids_of(names: list[str]) -> list[LesionGrid]:
    return [LesionGrid(n, Path(f"/ref/{n}.nii.gz"), Path(f"/brain/{n}.nii.gz")) for n in names]


def location_of(grid: str) -> LesionLocationSpec:
    atlas = lambda n: LesionAtlas(Path(f"/atlas/{n}.nii.gz"), Path(f"/atlas/{n}.xml"))  # noqa: E731
    return LesionLocationSpec(grid, atlas("cortical"), atlas("subcortical"), atlas("cerebellum"))


def lesion_config(names: list[str], output: Path = Path("/out/lesion_metadata.csv"), **over) -> LesionMetadataConfig:
    kwargs = dict(
        project="p", data_root=Path("/data"), datasets=["a", "b"], group_filter=["ST"], lesion_glob="*/x.nii.gz",
        binarize_threshold=0.5, resample_interpolation="nearest", grids=grids_of(names), correct_out_of_brain=True,
        side_threshold=0.2, location=location_of(names[0]), output_path=output, overwrite=False, run_notes=None,
    )
    kwargs.update(over)
    return LesionMetadataConfig(**kwargs)


def sdc_config(names: list[str], output: Path = Path("/out/sdc_metadata.csv"), **over) -> SdcMetadataConfig:
    kwargs = dict(
        project="p", data_root=Path("/data"), datasets=["a"], group_filter=None, disconnectome_glob="*/m.nii.gz",
        resample_interpolation="nearest", grids=grids_of(names), output_path=output, overwrite=False, run_notes="n",
    )
    kwargs.update(over)
    return SdcMetadataConfig(**kwargs)


frames = st.lists(
    st.tuples(st.integers(0, 10_000), st.one_of(st.none(), st.floats(0, 1))), min_size=1, max_size=8
).map(lambda rows: pd.DataFrame({"subject_id": [f"sub-STUNIPD{i:04d}" for i in range(len(rows))], "dataset": "a",
                                 "volume": [v for v, _ in rows], "fraction": [np.nan if f is None else f for _, f in rows]}))


# --- _write_csv: scrittura atomica ----------------------------------------------------------------


@pytest.mark.parametrize("write", WRITERS)
@given(frame=frames)
@settings(max_examples=15)
def test_csv_round_trips_nan_as_empty_cell_and_leaves_no_temp_file(write, frame):
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "nested" / "dir" / "metadata.csv"
        write(frame, target)
        loaded = pd.read_csv(target)
        leftovers = sorted(p.name for p in target.parent.iterdir())
    pd.testing.assert_frame_equal(loaded, frame, check_dtype=False)
    assert leftovers == ["metadata.csv"]


@pytest.mark.parametrize("write", WRITERS)
def test_a_failing_replace_keeps_the_previous_csv_and_removes_the_temp_file(write, monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "metadata.csv"
        write(pd.DataFrame({"a": [1]}), target)
        original = target.read_bytes()

        def broken_replace(src, dst):
            raise OSError("disk full")

        monkeypatch.setattr(os, "replace", broken_replace)
        with pytest.raises(OSError, match="disk full"):
            write(pd.DataFrame({"a": [2, 3]}), target)
        assert target.read_bytes() == original
        assert sorted(p.name for p in Path(tmp).iterdir()) == ["metadata.csv"]


@pytest.mark.parametrize("write", WRITERS)
def test_a_failure_while_writing_the_temp_file_never_touches_the_destination(write, monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "metadata.csv"
        write(pd.DataFrame({"a": [1]}), target)
        original = target.read_bytes()

        def broken_to_csv(self, *args, **kwargs):
            raise OSError("read-only filesystem")

        monkeypatch.setattr(pd.DataFrame, "to_csv", broken_to_csv)
        with pytest.raises(OSError, match="read-only"):
            write(pd.DataFrame({"a": [2]}), target)
        assert target.read_bytes() == original
        assert [p.name for p in Path(tmp).iterdir()] == ["metadata.csv"]


# --- _config_payload / _write_run_config -----------------------------------------------------------


@given(names=grid_names, threshold=st.floats(0, 1), side=st.floats(0.01, 0.99), notes=st.one_of(st.none(), st.text(max_size=20)), group_filter=st.one_of(st.none(), st.just(["ST", "HC"])))
def test_lesion_payload_is_json_serializable_and_lists_every_grid_in_order(names, threshold, side, notes, group_filter):
    payload = lesion_pipeline._config_payload(lesion_config(names, binarize_threshold=threshold, side_threshold=side, run_notes=notes, group_filter=group_filter))
    restored = json.loads(json.dumps(payload))
    assert restored == payload
    assert list(restored["grids"]) == names
    assert all(set(g) == {"reference_template_path", "brain_mask_path"} for g in restored["grids"].values())
    assert restored["location"]["grid"] == names[0] and set(restored["location"]["atlases"]) == {"cortical", "subcortical", "cerebellum"}
    assert restored["binarize_threshold"] == threshold and restored["group_filter"] == group_filter and restored["run_notes"] == notes


@given(names=grid_names)
def test_sdc_payload_is_json_serializable_and_lists_every_grid_in_order(names):
    payload = sdc_pipeline._config_payload(sdc_config(names))
    assert json.loads(json.dumps(payload)) == payload and list(payload["grids"]) == names
    assert "output_path" not in payload and "overwrite" not in payload  # sono del run, non di cio' che ha prodotto il CSV


@pytest.mark.parametrize("module, config", [(lesion_pipeline, lesion_config), (sdc_pipeline, sdc_config)], ids=["lesion", "sdc"])
@pytest.mark.parametrize("filename, expected", [("metadata.csv", "metadata.config.json"), ("sdc.v2.csv", "sdc.v2.config.json"), ("noext", "noext.config.json")])
def test_run_config_sits_next_to_the_csv_and_records_the_run_it_belongs_to(module, config, filename, expected):
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / filename
        written = module._write_run_config(config(["g"], output), output, datetime(2026, 10, 21, 9, 5, 7))
        payload = json.loads(written.read_text())
    assert written.name == expected and written.parent == output.parent
    assert payload["written"] == "21-10-26 09:05:07" and payload["grids"]["g"]["brain_mask_path"] == "/brain/g.nii.gz"


# --- report ------------------------------------------------------------------------------------------


def lesion_frame(names: list[str], rows: list[tuple], location_grid: str) -> pd.DataFrame:
    """rows: (dataset, volume, fraction|None, dominant|None). NaN dove il valore e' assente."""
    columns = _metadata_columns(grids_of(names), location_of(location_grid))
    frame = pd.DataFrame(index=range(len(rows)), columns=columns, dtype=object)
    for i, (dataset, volume, fraction, dominant) in enumerate(rows):
        frame.loc[i, ["subject_id", "dataset"]] = [f"sub-STUNIPD{i:04d}", dataset]
        for name in names:
            side = np.nan if volume == 0 else "left"
            frame.loc[i, [f"lesion_volume_voxels_{name}", f"out_of_brain_fraction_{name}", f"laterality_index_{name}", f"lesion_side_{name}"]] = [
                volume, np.nan if fraction is None else fraction, np.nan if volume == 0 else 0.5, side
            ]
        frame.loc[i, f"location_dominant_{location_grid}"] = np.nan if dominant is None else dominant
        for category in LOCATION_CATEGORIES:
            frame.loc[i, f"location_{category}_{location_grid}"] = np.nan if dominant is None else float(category == dominant)
    for column in frame.columns:
        if column not in ("subject_id", "dataset") and not column.startswith(("lesion_side", "location_dominant")):
            frame[column] = pd.to_numeric(frame[column])
    return frame


report_rows = st.lists(
    st.tuples(st.sampled_from(["siteA", "siteB"]), st.integers(0, 5000), st.one_of(st.none(), st.floats(0, 1)), st.one_of(st.none(), st.sampled_from(LOCATION_CATEGORIES))),
    min_size=1, max_size=8,
)


@given(names=grid_names, rows=report_rows, excluded=st.lists(st.sampled_from([f"sub-STUNIPDHC{i:04d}" for i in range(4)]), unique=True, max_size=4))
@settings(max_examples=25)
def test_lesion_report_counts_rows_datasets_and_exclusions_exactly_and_never_crashes(names, rows, excluded):
    frame = lesion_frame(names, [(d, v, f if v else None, c if v else None) for d, v, f, c in rows], names[0])
    lines = lesion_pipeline._report_lines(lesion_config(names), frame, excluded, datetime(2026, 1, 2, 3, 4, 5))
    text = "\n".join(lines)
    assert f"({len(rows)} righe)" in text
    for dataset in {d for d, *_ in rows}:
        assert f"| {dataset} | {sum(1 for d, *_ in rows if d == dataset)} |" in text
    assert text.count("### ") == len(names)
    assert f"senza sede (maschera vuota o tutta fuori dal brain): {sum(1 for _, v, _, c in rows if v == 0 or c is None)}" in text
    assert all(f"| {category} |" in text for category in LOCATION_CATEGORIES)
    assert (f"{len(excluded)} soggetto/i esclusi" in text) if excluded else ("Nessuno." in text)
    assert all(f"- {s}" in text for s in excluded)


def test_lesion_report_of_a_dry_run_has_no_metrics_section():
    text = "\n".join(lesion_pipeline._report_lines(lesion_config(["g"]), None, [], datetime(2026, 1, 2, 3, 4, 5)))
    assert "## Dry run" in text and "righe)" not in text and "## Metriche per griglia" not in text


def test_lesion_report_of_a_cohort_with_every_fraction_missing_is_still_written():
    frame = lesion_frame(["g"], [("siteA", 0, None, None), ("siteA", 0, None, None)], "g")
    text = "\n".join(lesion_pipeline._report_lines(lesion_config(["g"]), frame, [], datetime(2026, 1, 2, 3, 4, 5)))
    assert "maschere vuote (volume = 0): 2" in text and "senza lato (indice indefinito): 2" in text


sdc_rows = st.lists(st.tuples(st.sampled_from(["siteA", "siteB"]), st.floats(0, 5e6)), min_size=1, max_size=8)


@given(names=grid_names, rows=sdc_rows, excluded=st.lists(st.sampled_from([f"sub-STUNIPDHC{i:04d}" for i in range(3)]), unique=True, max_size=3))
@settings(max_examples=25)
def test_sdc_report_has_one_distribution_block_per_grid_and_the_right_counts(names, rows, excluded):
    frame = pd.DataFrame({"subject_id": [f"sub-STUNIPD{i:04d}" for i in range(len(rows))], "dataset": [d for d, _ in rows]})
    for name in names:
        frame[f"disconnection_load_voxels_{name}"] = [load for _, load in rows]
        frame[f"disconnection_mean_{name}"] = [load / 1e7 for _, load in rows]
    text = "\n".join(sdc_pipeline._report_lines(sdc_config(names), frame, excluded, datetime(2026, 1, 2, 3, 4, 5)))
    assert text.count("## Distribuzione (") == len(names) and f"({len(rows)} righe)" in text
    assert text.count("soggetti con carico = 0: ") == len(names)
    assert (f"{len(excluded)} soggetto/i esclusi" in text) if excluded else ("Nessuno." in text)


@pytest.mark.parametrize("module, config, prefix", [(lesion_pipeline, lesion_config, "compute_lesion_metadata_summary"), (sdc_pipeline, sdc_config, "compute_sdc_metadata_summary")], ids=["lesion", "sdc"])
def test_report_filename_carries_the_seconds_so_two_runs_in_one_minute_do_not_collide(module, config, prefix, tmp_path, monkeypatch):
    monkeypatch.setattr(module, "REPORTS_ROOT", tmp_path / "reports")
    first = module._write_report(config(["g"]), None, [], datetime(2026, 10, 21, 9, 5, 7))
    second = module._write_report(config(["g"]), None, [], datetime(2026, 10, 21, 9, 5, 8))
    assert first != second and first.name == f"{prefix}__21-10-26__09-05-07.md"
    assert first.read_text().startswith("# compute_")
