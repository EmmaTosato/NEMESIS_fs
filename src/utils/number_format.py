"""Italian number formatting, shared by the app's text and by the figures it draws."""

# Plotly's `layout.separators`: decimal then thousands. Applies to every number Plotly formats itself (ticks, hover,
# colorbars, `%{z:.2f}` templates); text written in Python goes through `format_number`.
PLOTLY_SEPARATORS = ",."


def format_number(value: float, decimals: int) -> str:
    """'.' groups thousands, ',' is the decimal separator: 5265.4 -> '5.265,4' (29-09-26 feedback: "i numeri non sono
    ben scritti, non si capisce molto bene"). The interface is in English but the numbers follow the Italian convention, so
    English-formatted numbers ('5 265.4') would read as a foreign convention exactly where the reader is scanning fastest.

    Done by swapping Python's own grouped format rather than with `locale`: locale is process global, depends on what
    happens to be installed on the machine, and would silently change every other number this process formats."""
    grouped = f"{value:,.{decimals}f}"          # 5,265.4
    return grouped.translate(str.maketrans({",": ".", ".": ","}))


def format_scientific(value: float, decimals: int) -> str:
    """`value` in scientific notation with ',' as decimal separator: 1.5e-05 -> '1,5e-05'."""
    return f"{value:.{decimals}e}".replace(".", ",")
