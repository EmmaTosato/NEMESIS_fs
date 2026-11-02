"""The app's wiring must survive a refactor untouched.

embedding_app_contract.py holds what every callback writes, reads and watches, and every
component id the layout has, generated from the app itself. These tests rebuild the app and
compare, so moving a callback or a panel between modules fails loudly if it changes the wiring
by accident - the one thing the rest of the suite cannot see, because Dash is built with
suppress_callback_exceptions=True and a callback wired to an id that no longer exists simply
never fires.

When the wiring is meant to change, regenerate the contract in the same commit:
    PYTHONPATH=. python -m tests.unit.embedding_app_contract
"""

from __future__ import annotations

import json

from tests.unit.embedding_app_contract import CALLBACKS, LAYOUT_IDS, build_fixture_app, observed

_REGENERATE = (
    "if this change is intended, regenerate the contract in the same commit: "
    "PYTHONPATH=. python -m tests.unit.embedding_app_contract"
)


def test_every_callback_writes_reads_and_watches_what_the_contract_says(tmp_path):
    callbacks, _ = observed(build_fixture_app(tmp_path))

    assert len(callbacks) == len(CALLBACKS), f"{len(CALLBACKS)} callback nel contratto, {len(callbacks)} nell'app - {_REGENERATE}"
    for observed_callback, expected in zip(callbacks, CALLBACKS):
        assert observed_callback == expected, _REGENERATE


def test_the_layout_has_exactly_the_component_ids_the_contract_says(tmp_path):
    _, ids = observed(build_fixture_app(tmp_path))

    assert set(ids) - set(LAYOUT_IDS) == set(), f"id nuovi nel layout - {_REGENERATE}"
    assert set(LAYOUT_IDS) - set(ids) == set(), f"id spariti dal layout - {_REGENERATE}"


def _matches_a_layout_id(written: str, ids: set[str]) -> bool:
    """Whether the component a callback writes exists in the layout.

    A plain id has to be there as itself. A pattern-matching id ({"mode": "ALL", "type": ...})
    is not a component at all: it stands for every component whose own id agrees with it on the
    keys that are not a wildcard, so it is satisfied by any one of them."""
    if not written.startswith("{"):
        return written in ids
    pattern = json.loads(written)
    fixed = {key: value for key, value in pattern.items() if value not in ("ALL", "ALLSMALLER", "MATCH")}
    for candidate in ids:
        if not candidate.startswith("{"):
            continue
        concrete = json.loads(candidate)
        if concrete.keys() == pattern.keys() and all(concrete[key] == value for key, value in fixed.items()):
            return True
    return False


def test_every_component_a_callback_writes_is_in_the_layout(tmp_path):
    """Not pinned data but a real invariant, and the one Dash is silent about: a callback whose
    output does not exist can never do anything, and with suppress_callback_exceptions=True
    nothing says so. An id a callback only *reads* may legitimately be absent (a picker is put
    there by another callback), so only the outputs are checked."""
    callbacks, ids = observed(build_fixture_app(tmp_path))

    written = {name.rsplit(".", 1)[0] for callback in callbacks for name in callback["outputs"]}
    missing = sorted(name for name in written if not _matches_a_layout_id(name, set(ids)))
    assert missing == [], f"questi callback scrivono su componenti che il layout non ha: {missing}"
