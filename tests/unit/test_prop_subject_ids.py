"""Test a proprietà di `src/utils/subject_ids.group_of`: confronto con un oracolo scritto a mano
(senza regex) su stringhe composte da frammenti di ID reali, più i casi limite noti."""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from src.utils.subject_ids import KNOWN_GROUPS, KNOWN_SITES, group_of

_DISEASES = ("ST", "PD", "GM")


def _oracle(subject_id: str) -> str | None:
    """Gruppo atteso, o None se l'ID non è nel formato `sub-<MALATTIA><SITO>[HC]<cifre ASCII>`."""
    if not subject_id.startswith("sub-"):
        return None
    rest = subject_id[4:]
    for disease in _DISEASES:
        if not rest.startswith(disease):
            continue
        after_disease = rest[len(disease) :]
        for site in KNOWN_SITES:
            if not after_disease.startswith(site):
                continue
            tail = after_disease[len(site) :]
            has_hc = tail.startswith("HC")
            digits = tail[2:] if has_hc else tail
            if digits and all(c in "0123456789" for c in digits):
                return "HC" if has_hc else disease
    return None


_FRAGMENTS = st.sampled_from(
    ["sub-", "sub", "-", "ST", "PD", "GM", "HC", "hc", "st", *KNOWN_SITES, "0", "7", "0001", "12345", "X", "_", " ", "UNI", "PD0"]
)


@given(st.lists(_FRAGMENTS, max_size=7).map("".join))
def test_group_of_agrees_with_handwritten_oracle_on_fragment_soup(candidate):
    expected = _oracle(candidate)
    if expected is None:
        with pytest.raises(ValueError, match="subject_id"):
            group_of(candidate)
    else:
        assert group_of(candidate) == expected


@given(
    disease=st.sampled_from(_DISEASES),
    site=st.sampled_from(KNOWN_SITES),
    hc=st.booleans(),
    number=st.from_regex(r"[0-9]{1,9}", fullmatch=True),
)
def test_every_wellformed_id_resolves_to_its_group(disease, site, hc, number):
    subject_id = f"sub-{disease}{site}{'HC' if hc else ''}{number}"
    assert group_of(subject_id) == ("HC" if hc else disease)
    assert group_of(subject_id) in KNOWN_GROUPS


@given(st.text(max_size=30))
def test_arbitrary_text_returns_a_known_group_or_raises_valueerror(text):
    """Nessun altro tipo di eccezione, e nessun valore fuori da KNOWN_GROUPS."""
    try:
        result = group_of(text)
    except ValueError:
        return
    assert result in KNOWN_GROUPS


@given(
    disease=st.sampled_from(_DISEASES),
    site=st.sampled_from(KNOWN_SITES),
    number=st.from_regex(r"[0-9]{1,6}", fullmatch=True),
    suffix=st.sampled_from([" ", "\t", "x", "-", "_1", "HC", "."]),
)
def test_trailing_garbage_is_rejected(disease, site, number, suffix):
    with pytest.raises(ValueError):
        group_of(f"sub-{disease}{site}{number}{suffix}")


@given(
    disease=st.sampled_from(_DISEASES),
    site=st.sampled_from(KNOWN_SITES),
    number=st.from_regex(r"[0-9]{1,6}", fullmatch=True),
    prefix=st.sampled_from([" ", "\t", "x", "sub-", "SUB-"]),
)
def test_leading_garbage_and_case_changes_are_rejected(disease, site, number, prefix):
    with pytest.raises(ValueError):
        group_of(f"{prefix}sub-{disease}{site}{number}")
    with pytest.raises(ValueError):
        group_of(f"sub-{disease}{site}{number}".lower())


@pytest.mark.parametrize(
    "subject_id",
    ["sub-STUNIPD", "sub-STUNIPDHC", "sub-UNIPD0001", "sub-ST0001", "sub-XXUNIPD0001", "sub-STUNIPD-0001", "", "sub-"],
)
def test_missing_pieces_are_rejected(subject_id):
    with pytest.raises(ValueError, match="subject_id"):
        group_of(subject_id)


@given(st.sampled_from(_DISEASES), st.sampled_from(KNOWN_SITES), st.from_regex(r"[0-9]{1,6}", fullmatch=True))
def test_trailing_newline_is_rejected(disease, site, number):
    with pytest.raises(ValueError):
        group_of(f"sub-{disease}{site}{number}\n")


def test_non_ascii_digits_are_rejected():
    with pytest.raises(ValueError):
        group_of("sub-STUNIPD٠٠٠١")
