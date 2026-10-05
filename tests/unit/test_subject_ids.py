"""Unit tests for src.utils.subject_ids.group_of."""

import pytest

from src.utils.subject_ids import KNOWN_GROUPS, KNOWN_SITES, group_of


def test_group_of_stroke_subject():
    assert group_of("sub-STUNIPD0001") == "ST"


def test_group_of_healthy_control():
    assert group_of("sub-STUNIPDHC0002") == "HC"


def test_group_of_malformed_subject_id_raises():
    with pytest.raises(ValueError, match="subject_id"):
        group_of("not-a-subject-id")


@pytest.mark.parametrize("subject_id", ["sub-STUKLFR0001", "sub-STUCLUK0001", "sub-STUKE0058"])
def test_group_of_recognizes_every_known_site(subject_id):
    assert group_of(subject_id) == "ST"


def test_known_sites_all_parse():
    for site in KNOWN_SITES:
        assert group_of(f"sub-ST{site}0001") == "ST"


def test_group_of_only_returns_known_groups():
    assert {group_of("sub-STUNIPD0001"), group_of("sub-STUNIPDHC0001")} <= set(KNOWN_GROUPS)


def test_group_of_unregistered_site_ending_in_hc_raises_instead_of_misclassifying():
    """Regression: the old [A-Z]+? lazy regex accepted ANY site code,
    always preferring to split a trailing "HC" into the healthy-control
    marker whenever the tail allowed it - a genuine stroke patient from a
    hypothetical unregistered site "MONTREALHC" would have been silently
    misclassified as a healthy control, no error. KNOWN_SITES makes an
    unregistered site raise instead of being guessed."""
    with pytest.raises(ValueError, match="subject_id"):
        group_of("sub-STMONTREALHC0001")
