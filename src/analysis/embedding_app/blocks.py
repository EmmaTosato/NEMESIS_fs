"""The small page blocks more than one panel is built from: a warning callout, the
sentence for subjects left out of a map, and a table of numbers.

They carry the wording and the CSS classes, so the same situation reads the same way
wherever it comes up. Anything only one panel uses lives with that panel instead.
"""

from __future__ import annotations

from dash import html


def _warning_box(message: str, detail: str | None = None) -> html.Div:
    """The shared boxed callout for every "partial result" warning on the page (29-09-26
    feedback: "warning tipo questo devono essere renderizzati un po' meglio").

    An uppercase vivid label carries the alarm; the message itself stays BLACK body text. That
    split is deliberate: coloring the whole block would make the information read as decoration
    and cost it contrast, while the label alone is enough to say "this is not routine caption
    text" - which is exactly how the previous thin amber line failed.

    detail: the long, non-prose tail (a list of subject ids), set apart from the sentence so the
    sentence stays readable when the tail runs to a dozen ids."""
    children: list = [html.Span("Warning", className="warning-label"), message]
    if detail is not None:
        children.append(html.Span(detail, className="warning-detail"))
    return html.Div(children, className="anatomy-warning")


def _missing_subjects_warning(missing_subjects: list[str]) -> str | None:
    """Shared warning text for overlap_map_content_for/disconnection_map_content_for (29-09-26)
    - None (no warning line at all, see _anatomy_viewer's own `warning` param) when every
    requested subject resolved."""
    if not missing_subjects:
        return None
    return (
        f"{len(missing_subjects)} cluster subjects left out of the map (data not found on disk): "
        f"{', '.join(sorted(missing_subjects))}"
    )


def _table(headers: list[str], rows: list[list], text_columns: tuple[int, ...] = (0,)) -> html.Div:
    """A table of the comparison section. The columns in `text_columns` hold labels (left-aligned),
    the rest numbers; a header may break at "\\n" (see .comparison-table), so a column is as wide as
    its numbers, not as its title."""
    def cells(tag, values):
        return [tag(value, className="text-col" if i in text_columns else None) for i, value in enumerate(values)]

    table = html.Table(
        [html.Thead(html.Tr(cells(html.Th, headers))), html.Tbody([html.Tr(cells(html.Td, row)) for row in rows])],
        className="stats-table comparison-table",
    )
    return html.Div(table, className="stats-table-wrap comparison-table-wrap")
