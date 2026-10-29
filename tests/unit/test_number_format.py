"""Unit tests for src/utils/number_format.py."""

import pytest

from src.utils.number_format import PLOTLY_SEPARATORS, format_number, format_scientific


@pytest.mark.parametrize(
    "value, decimals, expected",
    [(5265.4, 1, "5.265,4"), (0.366, 3, "0,366"), (1234567, 0, "1.234.567"), (-0.5, 2, "-0,50")],
)
def test_format_number_groups_thousands_with_a_dot_and_separates_decimals_with_a_comma(value, decimals, expected):
    assert format_number(value, decimals) == expected


def test_format_scientific_uses_the_decimal_comma():
    assert format_scientific(1.5e-05, 1) == "1,5e-05"


def test_plotly_separators_are_decimal_comma_then_thousands_dot():
    assert PLOTLY_SEPARATORS == ",."
