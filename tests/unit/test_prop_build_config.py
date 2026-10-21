"""Test a proprietà / parametrici di src/analysis/build_config.py.

Contratto (docstring dei loader): `FileNotFoundError` se il file non c'e', `ValueError` che identifica il
campo per qualunque problema strutturale (campo mancante, tipo sbagliato, valore fuori dominio) - mai
`TypeError`/`KeyError`/`OverflowError` (lessons_learned #7, #8, #5). Le config vengono generate per
mutazione di una config valida, con un valore JSON arbitrario al posto di un campo.
"""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.analysis import build_config as B
from src.utils.subject_ids import KNOWN_GROUPS

_GRIDS = {
    "2mm": {"reference_template_path": "t2.nii.gz", "brain_mask_path": "m2.nii.gz"},
    "1mm": {"reference_template_path": "t1.nii.gz", "brain_mask_path": "m1.nii.gz"},
}
_ATLAS = {"image_path": "a.nii.gz", "labels_path": "a.csv"}
_COMMON = {"project": "p", "data_root": "d", "output_root": "o", "session_name": "s", "overwrite": False}

# nome -> (loader, config valida, campi opzionali (assenti o None sono validi))
_CASES: dict[str, tuple] = {
    "build_matrix_voxelwise": (
        B.load_build_matrix_config,
        {**_COMMON, "datasets": ["A/x", "A/y"], "group_filter": ["ST"], "representation": "voxelwise",
         "excluded_subjects_path": "e.csv", "reference_template_path": "t.nii.gz", "lesion_glob": "*.nii.gz",
         "binarize_threshold": 0.5, "resample_interpolation": "nearest", "correct_out_of_brain": True,
         "brain_mask_path": "bm.nii.gz", "run_notes": "n"},
        {"group_filter", "run_notes", "correct_out_of_brain", "brain_mask_path"},
    ),
    "build_matrix_parcellated": (
        B.load_build_matrix_config,
        {**_COMMON, "datasets": ["A/x"], "representation": "parcellated", "excluded_subjects_path": "e.csv",
         "atlas": "schaefer", "value_column": "mean_overlap", "reference_labels_path": "l.csv"},
        {"group_filter", "run_notes"},
    ),
    "mask_fc": (
        B.load_mask_fc_config,
        {**_COMMON, "dataset": "A/x", "atlas_root": "r", "atlas_combos": ["c1", "c2"], "lesion_glob": "*.nii.gz",
         "fc_glob_template": "*{combo}.csv", "min_coverage": 0.5, "resample_interpolation": "linear",
         "binarize_threshold": 0.5, "group_filter": ["ST", "HC"], "run_notes": "n"},
        {"group_filter", "run_notes"},
    ),
    "build_fc_matrix": (
        B.load_build_fc_matrix_config,
        {"project": "p", "masked_fc_root": "m", "atlas_combos": ["c1", "c2"], "output_root": "o", "session_name": "s",
         "overwrite": True, "run_notes": "n"},
        {"run_notes"},
    ),
    "sdc_voxelwise": (
        B.load_build_sdc_matrix_config,
        {**_COMMON, "datasets": ["A/x"], "excluded_subjects_path": "e.csv", "object": "disconnectome",
         "representation": "voxelwise", "reference_template_path": "t.nii.gz", "resample_interpolation": "continuous",
         "correct_out_of_brain": True, "brain_mask_path": "bm.nii.gz"},
        {"group_filter", "run_notes", "correct_out_of_brain", "brain_mask_path"},
    ),
    "sdc_parcellated": (
        B.load_build_sdc_matrix_config,
        {**_COMMON, "datasets": ["A/x"], "excluded_subjects_path": "e.csv", "object": "lesion",
         "representation": "parcellated", "atlas": "schaefer", "value_column": "mean_overlap",
         "reference_labels_path": "l.csv"},
        {"group_filter", "run_notes", "correct_out_of_brain", "brain_mask_path"},
    ),
    "sdc_streamline": (
        B.load_build_sdc_matrix_config,
        {**_COMMON, "datasets": ["A/x"], "excluded_subjects_path": "e.csv", "object": "lesion",
         "representation": "streamline", "reference_labels_path": "l.csv"},
        {"group_filter", "run_notes", "correct_out_of_brain", "brain_mask_path"},
    ),
    "lesion_metadata": (
        B.load_compute_lesion_metadata_config,
        {"project": "p", "data_root": "d", "datasets": ["A/x"], "group_filter": ["ST"], "lesion_glob": "*.nii.gz",
         "binarize_threshold": 0.5, "resample_interpolation": "nearest", "grids": _GRIDS, "correct_out_of_brain": True,
         "side_threshold": 0.2, "output_path": "o.csv", "overwrite": False, "run_notes": "n",
         "location": {"grid": "2mm", "atlases": {"cortical": _ATLAS, "subcortical": _ATLAS, "cerebellum": _ATLAS}}},
        {"group_filter", "run_notes"},
    ),
    "sdc_metadata": (
        B.load_compute_sdc_metadata_config,
        {"project": "p", "data_root": "d", "datasets": ["A/x"], "group_filter": ["ST"],
         "disconnectome_glob": "*.nii.gz", "resample_interpolation": "nearest", "grids": _GRIDS,
         "output_path": "o.csv", "overwrite": False, "run_notes": "n"},
        {"group_filter", "run_notes"},
    ),
}
_CASE_NAMES = list(_CASES)

_NESTED_PATHS = {
    "lesion_metadata": [("grids",), ("grids", "2mm"), ("grids", "2mm", "brain_mask_path"), ("grids", "1mm", "reference_template_path"),
                        ("location",), ("location", "grid"), ("location", "atlases"), ("location", "atlases", "cortical"),
                        ("location", "atlases", "cerebellum", "image_path"), ("location", "atlases", "subcortical", "labels_path")],
    "sdc_metadata": [("grids",), ("grids", "2mm"), ("grids", "1mm", "brain_mask_path")],
}


def _paths(case: str) -> list[tuple]:
    config = _CASES[case][1]
    return [(key,) for key in config] + [("unknown_field",)] + _NESTED_PATHS.get(case, [])


_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(-5, 5),
    st.integers(min_value=10**30, max_value=10**40),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(max_size=6),
)
_json = st.recursive(
    _scalars,
    lambda children: st.one_of(st.lists(children, max_size=3), st.dictionaries(st.text(max_size=4), children, max_size=3)),
    max_leaves=6,
)
_DELETE = object()


def _mutated(case: str, path: tuple, value: object) -> dict:
    config = copy.deepcopy(_CASES[case][1])
    *parents, leaf = path
    node = config
    for step in parents:
        node = node[step]
    if value is _DELETE:
        node.pop(leaf, None)
    else:
        node[leaf] = value
    return config


def _load(case: str, obj: object):
    """Scrive `obj` in una cartella fresca (un esempio hypothesis per cartella) e chiama il loader."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "cfg.json"
        path.write_text(json.dumps(obj))
        return _CASES[case][0](path)


def _load_or_valueerror(case: str, obj: object):
    try:
        return _load(case, obj)
    except ValueError:
        return None


# ---- ancora + fuzz --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", _CASE_NAMES)
def test_the_unmutated_config_loads(case):
    """Ancora del fuzz: una config di partenza gia' invalida renderebbe ogni mutazione 'valida per caso'."""
    assert _load(case, _CASES[case][1]) is not None


@settings(max_examples=250)
@given(case=st.sampled_from(_CASE_NAMES), data=st.data())
def test_a_mutated_config_loads_or_raises_valueerror_never_another_exception(case, data):
    path = data.draw(st.sampled_from(_paths(case)))
    value = data.draw(st.one_of(_json, st.just(_DELETE)))
    _load_or_valueerror(case, _mutated(case, path, value))


@settings(max_examples=100)
@given(case=st.sampled_from(_CASE_NAMES), top=_json)
def test_a_top_level_that_is_not_an_object_is_a_valueerror(case, top):
    if isinstance(top, dict):
        return
    with pytest.raises(ValueError, match="top-level"):
        _load(case, top)


@pytest.mark.parametrize("case", _CASE_NAMES)
def test_missing_or_non_file_paths_raise_filenotfounderror(case, tmp_path):
    loader = _CASES[case][0]
    for target in (tmp_path / "absent.json", tmp_path):
        with pytest.raises(FileNotFoundError, match="config file not found"):
            loader(target)


@pytest.mark.parametrize("case", _CASE_NAMES)
@pytest.mark.parametrize("fraction", [0.1, 0.5, 0.99])
def test_a_truncated_config_file_raises_valueerror(case, fraction, tmp_path):
    text = json.dumps(_CASES[case][1])
    file = tmp_path / "cfg.json"
    file.write_text(text[: int(len(text) * fraction)])
    with pytest.raises(ValueError):  # JSONDecodeError e' un ValueError
        _CASES[case][0](file)


# ---- campi obbligatori / tipi, per ogni loader ------------------------------------------------------------------


def _required_fields():
    return [(case, key) for case in _CASE_NAMES for key in _CASES[case][1] if key not in _CASES[case][2]]


@pytest.mark.parametrize("case, field", _required_fields())
def test_deleting_any_required_field_raises_valueerror_naming_it(case, field):
    config = _mutated(case, (field,), _DELETE)
    with pytest.raises(ValueError, match=field):
        _load(case, config)


def _str_fields():
    return [(case, key) for case in _CASE_NAMES for key, value in _CASES[case][1].items() if isinstance(value, str)]


@pytest.mark.parametrize("case, field", _str_fields())
@pytest.mark.parametrize("bad", [0, 1, True, False, 1.5, [], ["a"], {}, {"a": 1}, ""])
def test_a_string_field_rejects_every_non_string_and_the_empty_string(case, field, bad):
    config = _mutated(case, (field,), bad)
    with pytest.raises(ValueError, match=field):
        _load(case, config)


def _bool_fields():
    return [(case, key) for case in _CASE_NAMES for key, value in _CASES[case][1].items() if isinstance(value, bool)]


@pytest.mark.parametrize("case, field", _bool_fields())
@pytest.mark.parametrize("bad", [0, 1, "true", "yes", [], {}, 1.0])
def test_a_boolean_field_rejects_truthy_non_booleans(case, field, bad):
    config = _mutated(case, (field,), bad)
    with pytest.raises(ValueError, match=field):
        _load(case, config)


# ---- liste obbligatorie: datasets / atlas_combos -------------------------------------------------------------------------


_LIST_FIELDS = [("build_matrix_voxelwise", "datasets"), ("sdc_voxelwise", "datasets"), ("sdc_metadata", "datasets"),
                ("lesion_metadata", "datasets"), ("mask_fc", "atlas_combos"), ("build_fc_matrix", "atlas_combos")]


@pytest.mark.parametrize("case, field", _LIST_FIELDS)
@pytest.mark.parametrize(
    "bad, match",
    [([], "non-empty"), ("a/x", "non-empty list"), (None, "non-empty list"), ({"a": 1}, "non-empty list"), ([""], "non-empty"),
     ([1], "non-empty"), (["a", 1], "non-empty"), ([["a"]], "non-empty"), ([None], "non-empty"),
     (["a", "a"], "duplicate"), (["a", "b", "a"], "duplicate"), (["a", "b", "b", "b"], "duplicate")],
)
def test_required_unique_string_lists_reject_empty_wrongly_typed_and_duplicated_entries(case, field, bad, match):
    with pytest.raises(ValueError, match=match):
        _load(case, _mutated(case, (field,), bad))


@settings(max_examples=80)
@given(items=st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=6, unique=True), case=st.sampled_from(_LIST_FIELDS))
def test_a_unique_string_list_is_returned_in_its_original_order(items, case):
    name, field = case
    config = _load(name, _mutated(name, (field,), items))
    assert getattr(config, field) == items


@settings(max_examples=80)
@given(items=st.lists(st.text(min_size=1, max_size=3), min_size=2, max_size=6), case=st.sampled_from(_LIST_FIELDS))
def test_a_list_is_accepted_iff_it_has_no_duplicates(items, case):
    name, field = case
    config = _mutated(name, (field,), items)
    if len(set(items)) != len(items):
        with pytest.raises(ValueError, match="duplicate"):
            _load(name, config)
    else:
        assert getattr(_load(name, config), field) == items


# ---- group_filter -----------------------------------------------------------------------------------------------------------


_GROUP_CASES = [name for name in _CASE_NAMES if "group_filter" in _CASES[name][1]]


@settings(max_examples=60)
@given(case=st.sampled_from(_GROUP_CASES), groups=st.lists(st.sampled_from(KNOWN_GROUPS), min_size=1, max_size=4, unique=True))
def test_a_group_filter_of_distinct_known_groups_is_kept_as_declared(case, groups):
    assert _load(case, _mutated(case, ("group_filter",), groups)).group_filter == groups


@pytest.mark.parametrize("case", _GROUP_CASES)
@pytest.mark.parametrize("bad", [[], "ST", 3, True, {"ST": 1}, [""], ["XX"], ["st"], ["ST", "XX"], [None], [["ST"]], [1]])
def test_a_malformed_or_unknown_group_filter_is_a_valueerror(case, bad):
    with pytest.raises(ValueError, match="group_filter"):
        _load(case, _mutated(case, ("group_filter",), bad))


@pytest.mark.parametrize("case", _GROUP_CASES)
def test_group_filter_absent_or_null_means_no_restriction(case):
    assert _load(case, _mutated(case, ("group_filter",), _DELETE)).group_filter is None
    assert _load(case, _mutated(case, ("group_filter",), None)).group_filter is None


# ---- numeri in [0, 1] -----------------------------------------------------------------------------------------------------------


_FRACTION_FIELDS = [("build_matrix_voxelwise", "binarize_threshold"), ("mask_fc", "min_coverage"), ("mask_fc", "binarize_threshold"),
                    ("lesion_metadata", "binarize_threshold"), ("lesion_metadata", "side_threshold")]


@pytest.mark.parametrize("case, field", _FRACTION_FIELDS)
@pytest.mark.parametrize(
    "value, valid",
    [(0, True), (1, True), (0.0, True), (1.0, True), (0.25, True), (1e-300, True), (-0.0, True), (-1e-12, False), (1.0000001, False), (-1, False),
     (2, False), (10**30, False), (float("nan"), False), (float("inf"), False), (float("-inf"), False), (True, False), (False, False),
     ("0.5", False), (None, False), ([0.5], False), ({}, False)],
)
def test_fractions_accept_exactly_numbers_in_the_closed_unit_interval(case, field, value, valid):
    config = _mutated(case, (field,), value)
    if valid:
        assert getattr(_load(case, config), field) == float(value)
        assert isinstance(getattr(_load(case, config), field), float)  # un int viene normalizzato a float
    else:
        with pytest.raises(ValueError, match=field):
            _load(case, config)


@settings(max_examples=120)
@given(value=st.one_of(st.integers(-3, 3), st.floats(allow_nan=False, allow_infinity=False, min_value=-3, max_value=3)), case=st.sampled_from(_FRACTION_FIELDS))
def test_fraction_acceptance_matches_the_interval_oracle(value, case):
    name, field = case
    config = _mutated(name, (field,), value)
    if 0 <= value <= 1:
        assert getattr(_load(name, config), field) == float(value)
    else:
        with pytest.raises(ValueError):
            _load(name, config)


# ---- domini enumerati -------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["build_matrix_voxelwise", "mask_fc", "lesion_metadata", "sdc_voxelwise", "sdc_metadata"])
@pytest.mark.parametrize("interp", ["linear", "nearest", "continuous"])
def test_every_known_interpolation_is_accepted(case, interp):
    assert _load(case, _mutated(case, ("resample_interpolation",), interp)).resample_interpolation == interp


@settings(max_examples=60)
@given(interp=st.text(max_size=10).filter(lambda s: s not in {"linear", "nearest", "continuous"}),
       case=st.sampled_from(["build_matrix_voxelwise", "mask_fc", "lesion_metadata", "sdc_voxelwise", "sdc_metadata"]))
def test_an_unknown_interpolation_is_rejected(interp, case):
    if interp == "":
        return  # gia' coperto dal controllo "stringa non vuota"
    with pytest.raises(ValueError, match="resample_interpolation"):
        _load(case, _mutated(case, ("resample_interpolation",), interp))


@pytest.mark.parametrize("representation", ["", "Voxelwise", "voxel", "parcellated ", None, 1, ["voxelwise"]])
def test_an_unknown_lesion_representation_is_rejected(representation):
    with pytest.raises(ValueError, match="representation"):
        _load("build_matrix_voxelwise", _mutated("build_matrix_voxelwise", ("representation",), representation))


# ---- esclusività fra rappresentazioni ---------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("key, value", [("atlas", "a"), ("value_column", "mean_overlap"), ("reference_labels_path", "l.csv")])
def test_a_voxelwise_lesion_config_rejects_each_parcellated_field(key, value):
    config = {**_CASES["build_matrix_voxelwise"][1], key: value}
    with pytest.raises(ValueError, match="are not read by representation='voxelwise'"):
        _load("build_matrix_voxelwise", config)


@pytest.mark.parametrize(
    "key, value",
    [("reference_template_path", "t"), ("lesion_glob", "*"), ("binarize_threshold", 0.5), ("resample_interpolation", "nearest"),
     ("correct_out_of_brain", False), ("correct_out_of_brain", None), ("brain_mask_path", "m")],
)
def test_a_parcellated_lesion_config_rejects_each_voxelwise_field_even_when_it_would_do_nothing(key, value):
    config = {**_CASES["build_matrix_parcellated"][1], key: value}
    with pytest.raises(ValueError, match="are not read by representation='parcellated'"):
        _load("build_matrix_parcellated", config)


@pytest.mark.parametrize("case", ["sdc_parcellated", "sdc_streamline"])
@pytest.mark.parametrize("extra", [{"correct_out_of_brain": True}, {"brain_mask_path": "bm.nii.gz"}, {"correct_out_of_brain": True, "brain_mask_path": "bm"}])
def test_sdc_correction_fields_that_would_act_are_rejected_outside_voxelwise(case, extra):
    with pytest.raises(ValueError, match="only read by representation='voxelwise'"):
        _load(case, {**_CASES[case][1], **extra})


@pytest.mark.parametrize("case", ["sdc_parcellated", "sdc_streamline"])
@pytest.mark.parametrize("extra", [{}, {"correct_out_of_brain": False}, {"correct_out_of_brain": None}, {"brain_mask_path": None}])
def test_sdc_correction_fields_that_do_nothing_are_accepted_outside_voxelwise(case, extra):
    config = _load(case, {**_CASES[case][1], **extra})
    assert config.correct_out_of_brain is False and config.brain_mask_path is None


@pytest.mark.parametrize("case", ["build_matrix_voxelwise", "sdc_voxelwise"])
def test_correct_out_of_brain_requires_a_brain_mask_exactly_when_set(case):
    base = copy.deepcopy(_CASES[case][1])
    del base["brain_mask_path"]
    with pytest.raises(ValueError, match="brain_mask_path is missing"):
        _load(case, {**base, "correct_out_of_brain": True})
    config = _load(case, {**base, "correct_out_of_brain": False})
    assert config.brain_mask_path is None and config.correct_out_of_brain is False


@pytest.mark.parametrize(
    "object_, representation, valid",
    [("disconnectome", "voxelwise", True), ("lesion", "voxelwise", False), ("disconnectome", "streamline", False), ("lesion", "streamline", True),
     ("lesion", "parcellated", True), ("disconnectome", "parcellated", True), ("other", "parcellated", False), ("lesion", "other", False)],
)
def test_sdc_object_representation_matrix(object_, representation, valid):
    base = {"voxelwise": "sdc_voxelwise", "streamline": "sdc_streamline"}.get(representation, "sdc_parcellated")
    config = {**_CASES[base][1], "object": object_, "representation": representation}
    if valid:
        assert _load(base, config).representation == representation
    else:
        with pytest.raises(ValueError):
            _load(base, config)


# ---- griglie e location (lesion/sdc metadata) ----------------------------------------------------------------------------------------------


@settings(max_examples=100)
@given(names=st.lists(st.text(max_size=6), min_size=0, max_size=4, unique=True))
def test_grid_names_are_accepted_iff_non_empty_alphanumeric_and_the_object_is_non_empty(names):
    grids = {name: _GRIDS["2mm"] for name in names}
    config = _mutated("sdc_metadata", ("grids",), grids)
    if names and all(name.isalnum() for name in names):
        assert [g.name for g in _load("sdc_metadata", config).grids] == names  # ordine del file
    else:
        with pytest.raises(ValueError):
            _load("sdc_metadata", config)


@settings(max_examples=60)
@given(grid=st.text(alphabet="abcxyz0123456789", max_size=4))
def test_the_location_grid_must_be_one_of_the_declared_grids(grid):
    config = _mutated("lesion_metadata", ("location", "grid"), grid)
    if grid in _GRIDS:
        assert _load("lesion_metadata", config).location.grid == grid
    else:
        with pytest.raises(ValueError):
            _load("lesion_metadata", config)


@pytest.mark.parametrize("extra", ["extra", "Cortical", "thalamus"])
def test_location_atlases_with_an_unknown_or_misspelt_name_are_rejected_not_ignored(extra):
    atlases = {"cortical": _ATLAS, "subcortical": _ATLAS, "cerebellum": _ATLAS, extra: _ATLAS}
    with pytest.raises(ValueError, match="exactly the keys"):
        _load("lesion_metadata", _mutated("lesion_metadata", ("location", "atlases"), atlases))


@pytest.mark.parametrize("missing", ["cortical", "subcortical", "cerebellum"])
def test_location_atlases_missing_one_of_the_three_is_rejected(missing):
    atlases = {k: _ATLAS for k in ("cortical", "subcortical", "cerebellum") if k != missing}
    with pytest.raises(ValueError, match="exactly the keys"):
        _load("lesion_metadata", _mutated("lesion_metadata", ("location", "atlases"), atlases))


@pytest.mark.parametrize("entry", [None, 3, "a.nii", [], {}, {"image_path": "a"}, {"labels_path": "b"}, {"image_path": "", "labels_path": "b"},
                                   {"image_path": 1, "labels_path": "b"}, {"image_path": "a", "labels_path": None},
                                   {"image_path": "a", "labels_path": "b", "extra": 1}])
def test_a_malformed_location_atlas_entry_is_a_valueerror(entry):
    with pytest.raises(ValueError, match="location.atlases.cortical"):
        _load("lesion_metadata", _mutated("lesion_metadata", ("location", "atlases", "cortical"), entry))


@pytest.mark.parametrize("entry", [None, 3, "x", [], {}, {"reference_template_path": "t"}, {"brain_mask_path": "m"},
                                   {"reference_template_path": "", "brain_mask_path": "m"}, {"reference_template_path": "t", "brain_mask_path": 5}])
@pytest.mark.parametrize("case", ["lesion_metadata", "sdc_metadata"])
def test_a_malformed_grid_entry_is_a_valueerror_naming_the_grid(case, entry):
    with pytest.raises(ValueError, match="grids.2mm"):
        _load(case, _mutated(case, ("grids", "2mm"), entry))


# ---- bug sospetti ------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", _GROUP_CASES)
def test_a_group_filter_with_duplicate_groups_is_rejected(case):
    with pytest.raises(ValueError, match="duplicate"):
        _load(case, _mutated(case, ("group_filter",), ["ST", "ST"]))


@pytest.mark.parametrize("case, field", _FRACTION_FIELDS)
def test_an_integer_too_large_for_a_float_is_a_valueerror_not_an_overflowerror(case, field):
    config = _mutated(case, (field,), 10**400)
    with pytest.raises(ValueError, match=field):
        _load(case, config)
