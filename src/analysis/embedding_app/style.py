"""The visual identity of the Embedding Explorer: design tokens, the page's CSS, the HTML
skeleton Dash renders it into, and the number format every figure on the page is given.

The bottom layer of the embedding_app package - it imports nothing from its siblings, they
read the tokens from here (figures style their fonts and axes with the same values the CSS
uses, so the page and the plots in it cannot drift apart).
"""

from __future__ import annotations

import plotly.graph_objects as go

from src.utils.number_format import PLOTLY_SEPARATORS

# Same measured design tokens as src/analysis/understanding_umap_report.py's own _CSS
# (PAIR-style editorial report, 13/14-08-26 sessions) - not imported directly (that module's
# _CSS is private and tightly coupled to its own grid/slider DOM, none of which this app has),
# but deliberately the same values, so the two Dash tools in this repo read as one visual
# family instead of two unrelated ones. _TEXT_COLOR = PAIR's own measured text color
# (getComputedStyle on the live page = rgb(51,51,51)), font stack = system-ui/-apple-system
# stack PAIR uses, _GRID_BORDER = PAIR's own .demo-data cell border.
_TEXT_COLOR = "#333"
_GRID_BORDER = "rgba(0,0,0,0.1)"
_FONT_STACK = (
    '-apple-system, "system-ui", "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, '
    'Cantarell, "Helvetica Neue", sans-serif'
)

# Injected into the Dash app's index_string (src.pipeline.embedding_app.build_app) - ample
# whitespace, no boxy borders/sidebars, a curated button-group instead of a framework dropdown
# for color_by, Plotly's own modebar hidden by the figure config (not CSS) since Dash renders
# it in an iframe-like shadow context CSS can't reach. See the design brief this was built
# against (14-08-26, user-supplied "Senior Frontend/UI-UX" prompt referencing
# pair-code.github.io/understanding-umap as the benchmark) - minimalism, differentiated H1/H2,
# transparent plot background, curated palette, no default-Streamlit/default-Plotly look.
CSS = f"""
body {{ font-family: {_FONT_STACK}; margin: 0; background: #fff; color: {_TEXT_COLOR}; }}
.page {{ max-width: 1100px; margin: 0 auto; padding: 48px 32px 96px; }}
/* 02-10-26 feedback: same size as .section-title ("Clustering Explorer") - the two headline
   titles the app has must read as the same weight of statement, not a page title that's
   visibly smaller than one of its own sections. */
.page-title {{ font-size: 40px; font-weight: 800; letter-spacing: -0.01em; text-align: center; margin: 0 0 14px; }}
/* 01-09-26 feedback: the descriptive/status texts across the app (this subtitle, .status-message,
   .anatomy-caption) read "troppo chiaro e scritto in piccolo" - all 3 bumped in size and to a
   darker gray, still clearly secondary to any heading (kept well under .section-heading/
   .anatomy-subject-title's own sizes) but no longer near-illegible. */
.page-subtitle {{ font-size: 19px; color: #595959; text-align: center; margin: 0 0 56px; }}
.controls {{ display: flex; flex-direction: column; align-items: center; gap: 24px; margin-bottom: 32px; }}
/* One field per selection step (Dato -> Pipeline -> Metodo -> Metrica -> Componenti -> Run),
   left-to-right in reading/decision order (2026-08, extended 15-08-26 when Pipeline became a
   real dropdown, not a fixed label) - wraps to multiple rows on a narrow viewport instead of
   overflowing horizontally. */
.picker-row {{ display: flex; flex-wrap: wrap; justify-content: center; align-items: flex-end; gap: 20px; }}
.picker-field {{ display: flex; flex-direction: column; gap: 6px; min-width: 200px; }}
.picker-label {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #767676; }}
.color-buttons {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }}
.color-buttons button {{
    font-family: inherit; font-size: 14px; padding: 8px 18px; cursor: pointer;
    border: 1px solid #ccc; border-radius: 999px; background: #fff; color: {_TEXT_COLOR};
    transition: border-color 0.15s, background 0.15s;
}}
.color-buttons button:hover {{ border-color: #4a90d9; }}
.color-buttons button.active {{ border-color: #4a90d9; border-width: 2px; background: #f0f7fd; font-weight: 600; }}
/* The main colour-mode row (06-10-26, on request): one row when every chip fits, otherwise two
   rows of balanced length instead of a flex wrap that strands a single chip on its own line.
   `text-wrap: balance` does exactly that for inline content, which a flex container is not -
   hence inline-block chips with a margin where the flex rows use `gap`. */
.color-buttons.chips-balanced {{ display: block; text-align: center; text-wrap: balance; }}
.color-buttons.chips-balanced button {{ display: inline-block; margin: 4px; }}
/* The grid chooser, shown under the colour chips only while a grid mode (lesion volume,
   disconnection) is active (30-09-26, on request; extended to disconnection 06-10-26). Same
   chip family as the row above, one step quieter, with a label so a lone "2mm" button is not a
   mystery. */
.grid-row {{ margin-top: 10px; align-items: center; }}
/* Inside an anatomy panel the same chooser sits between a section heading and the content it
   scopes, so it needs room on BOTH sides - as a bare 10px-top row it read as glued to the
   heading above and to the cluster title below (30-09-26). */
.anatomy-panel .grid-row {{ justify-content: center; margin: 26px 0 34px; }}
.grid-row-label {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #767676; margin-right: 4px; }}
.grid-row button {{ font-size: 13px; padding: 5px 14px; }}
/* width:100% + no Plotly config.responsive (see graph_content_for) - a stable CSS width set
   once at mount, not a JS ResizeObserver reacting to every later layout event (scrolling
   included) - that combination was the actual cause of the graph distorting on scroll. */
/* What the active colour mode means (06-10-26, on request): between the section heading and the
   plot, with room on both sides. min-height holds two lines so the plot below does not jump when
   a one-line description replaces a two-line one. */
.color-description {{
    max-width: 820px; min-height: 3em; margin: 0 auto 32px; text-align: center;
    font-size: 17px; line-height: 1.5; color: #595959;
}}
/* The meaning of each label of a categorical mode (ColorMode.legend): a bullet list under the sentence, centred as a
   block but read left-aligned. */
.tab-bar {{ display: flex; justify-content: center; gap: 8px; margin: 8px 0 8px; border-bottom: 1px solid {_GRID_BORDER}; }}
.tab-btn {{
    font-family: inherit; font-size: 18px; font-weight: 600; padding: 12px 30px; cursor: pointer; color: #767676;
    background: none; border: none; border-bottom: 3px solid transparent; margin-bottom: -1px;
}}
.tab-btn:hover {{ color: {_TEXT_COLOR}; }}
.tab-btn.active {{ color: {_TEXT_COLOR}; border-bottom-color: {_TEXT_COLOR}; }}
/* The first section of a tab is the top of its page: no heavy rule and a short gap, instead of the break that
   .section-divider draws between two sections of one page. */
.tab-content > .section-divider:first-child {{ margin-top: 32px; border-top: none; padding-top: 0; }}
.color-legend {{ display: inline-block; text-align: left; margin: 10px 0 0; padding-left: 22px; font-size: 16px; }}
.color-legend li {{ margin: 3px 0; }}
.graph-wrap {{ display: flex; justify-content: center; width: 100%; }}
.graph-wrap > div {{ width: 100%; }}
.status-message {{ text-align: center; color: #595959; font-size: 18px; margin: 64px 0; }}
/* Shared by all 3 section headings (Embedding Visualization / Anatomia lesionale / Overlap map
   per cluster, 01-09-26) - a class of its own rather than a nesting-based ".anatomy-panel h2"
   selector, since "Embedding Visualization" sits above the scatter, outside any .anatomy-panel.
   Same weight/scale family as .page-title (40px) - a real section header, not the 20px
   subheading this panel used to read as (feedback: "va scritto più grande" / "un pelo più
   grande" on a follow-up pass). */
.section-heading {{ font-size: 30px; font-weight: 800; margin: 40px 0 20px; text-align: center; }}
/* The three titles that open a tab ("Embedding Visualization", "Clustering Explorer", "Dendrogram Explorer") are
   the same size: the first one is a .section-heading, so it takes .section-title's size and keeps its own margins. */
#embedding-section {{ font-size: 40px; letter-spacing: -0.01em; }}
/* Anatomy panels (lesion viewer / cluster overlap map, 01-09-26) - same page-width container as
   .page itself (not .graph-wrap's centered flex, these are full-width blocks with their own
   heading), separated from the picker/scatter above by a thin rule instead of a boxy border. */
.composition-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 24px 16px; }}
.anatomy-panel {{ margin-top: 56px; padding-top: 32px; border-top: 1px solid {_GRID_BORDER}; }}
/* The per-subject -> per-cluster break (30-09-26). A heavier rule than .anatomy-panel's own
   hairline, because this separates two kinds of question, not two panels of the same kind. */
.section-divider {{ margin-top: 88px; padding-top: 52px; border-top: 3px solid {_TEXT_COLOR}; }}
.section-title {{ font-size: 40px; font-weight: 800; letter-spacing: -0.01em; text-align: center; margin: 0 0 10px; }}
.section-intro {{ font-size: 21px; line-height: 1.5; color: #595959; text-align: center; margin: 0 0 28px; }}
/* The explanation lines of the clustering evaluation panel: the size of .page-subtitle. */
.quality-intro {{ font-size: 19px; line-height: 1.5; color: #595959; text-align: center; margin: 0 0 28px; }}
/* The chooser that scopes every panel below: centred and wider than a picker-row field, so it
   reads as this section's own control rather than as one more form field. */
.cluster-chooser {{
    display: flex; flex-direction: column; align-items: center; gap: 8px;
    max-width: 260px; margin: 0 auto 24px;
}}
.cluster-chooser > div {{ width: 100%; font-size: 18px; }}
/* The tuning picker of the Dendrogram Explorer: run names are long. */
.cluster-chooser-wide {{ max-width: 760px; }}
/* Dendrogram Explorer: the walk starts well below the pickers, and each step is set apart from the previous one. */
/* Blocks that need more than the 1100 px of .page (the overview of every cluster, the walk down the tree): as wide as
   the window up to 1700 px, centred on the page. */
/* overflow-x: clip, not auto: auto would make the block a scroll container and the sticky embedding inside it (see
   .overview-embedding) would stick to the block, which never scrolls, instead of to the window. */
.wide-block {{ width: min(1700px, calc(100vw - 48px)); margin-left: 50%; transform: translateX(-50%); box-sizing: border-box; overflow-x: clip; }}
/* "all" in the cluster picker: the save buttons below belong to a single cluster's map. */
.anatomy-panel:has(.all-clusters-overview) .save-btn-row {{ display: none; }}
.overview-heading {{ font-size: 24px; font-weight: 700; text-align: center; margin: 64px 0 10px; }}
/* The two wide layouts below (the overview of every cluster, a step of the walk down the tree) are drawn at a fixed
   design width, 1652 px = the 1700 px of .wide-block minus its margins, because the maps are iframes of a fixed pixel
   size. A narrower window shrinks the whole drawing (zoom) instead of cutting it. The media queries are for browsers
   that do not know typed arithmetic in calc(); they read the window, not the block, so they are only a coarse step. */
.overview-body, .dendrogram-step-body {{ width: 1652px; margin-left: auto; margin-right: auto; }}
@media (max-width: 1700px) {{ .overview-body, .dendrogram-step-body {{ zoom: 0.95; }} }}
@media (max-width: 1600px) {{ .overview-body, .dendrogram-step-body {{ zoom: 0.88; }} }}
@media (max-width: 1500px) {{ .overview-body, .dendrogram-step-body {{ zoom: 0.8; }} }}
@media (max-width: 1350px) {{ .overview-body, .dendrogram-step-body {{ zoom: 0.72; }} }}
@media (max-width: 1250px) {{ .overview-body, .dendrogram-step-body {{ zoom: 0.65; }} }}
.overview-body, .dendrogram-step-body {{ zoom: min(1, calc((100vw - 48px) / 1652px)); }}
.overview-body {{ display: grid; grid-template-columns: 380px minmax(0, 1fr); gap: 36px; align-items: start; margin-top: 40px; }}
/* The embedding follows the reader down the maps and stops where the maps end (the end of .overview-body). */
.overview-embedding {{ position: sticky; top: 24px; }}
.overview-grid {{ display: grid; gap: 48px 64px; justify-content: center; align-items: start; }}
.map-tile-title {{ display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 18px; font-weight: 600; margin: 4px 0; }}
.map-tile-title.large {{ font-size: 20px; }}
.map-swatch {{ width: 15px; height: 15px; border-radius: 3px; flex: none; }}
.map-tile iframe {{ display: block; border: none; }}
.dendrogram-steps-title {{ text-align: center; font-size: 34px; font-weight: 800; margin: 96px 0 0; }}
.dendrogram-step {{ box-sizing: border-box; min-height: 900px; padding: 80px 0 10px; margin-top: 64px; border-top: 1px solid #d9d9d9; }}
.dendrogram-step.first {{ padding-top: 18px; margin-top: 0; border-top: none; }}
.dendrogram-step-title {{ font-size: 20px; margin: 0 0 36px; text-align: center; }}
.dendrogram-step-body {{ display: grid; grid-template-columns: 560px 1010px; justify-content: center; gap: 60px; align-items: start; }}
.dendrogram-step-maps {{ display: flex; flex-direction: column; gap: 10px; }}
.dendrogram-step-row {{ display: flex; gap: 12px; justify-content: center; align-items: flex-start; }}
/* The table of a step sits below the drawing, at the normal size of the page's other tables and not zoomed with it. */
/* Two classes: .stats-table-wrap, declared further down, sets its own margin-top and would win over a single one. */
.stats-table-wrap.dendrogram-step-table {{ max-width: 900px; margin: 88px auto 0; }}
.dendrogram-step-table .stats-table {{ width: auto; margin: 0 auto; }}
.dendrogram-step-table .stats-table th {{ white-space: normal; max-width: 92px; line-height: 1.3; font-size: 11.5px; padding: 0 12px 9px; }}
.dendrogram-step-table .stats-table td {{ padding: 13px 12px 11px; font-size: 15px; }}
.dendrogram-step-table .stats-cluster {{ font-size: 15px; }}
.cluster-chooser .picker-label {{ font-size: 16px; }}
/* The panel directly under the chooser must not re-draw the section break with its own rule. */
.section-divider + .anatomy-panel {{ margin-top: 96px; border-top: none; padding-top: 0; }}
/* A further bump over .section-heading's own 30px (01-09-26, follow-up feedback: "un po' più
   grandi") - kept scoped to the two anatomy panels, not "Embedding Visualization" above, since
   only these two were called out this time. */
.anatomy-panel .section-heading {{ margin-top: 0; font-size: 34px; }}
.anatomy-controls {{ display: flex; flex-wrap: wrap; align-items: flex-end; gap: 20px; margin-bottom: 20px; }}
/* The subject/cluster heading and its color-legend caption are ordinary HTML we render
   ourselves (01-09-26) - nilearn's own `title`/colorbar labels are drawn straight onto a
   <canvas> with no width check or line-wrapping, silently overflowing past the panel edge for
   anything longer than a few characters (see lesion_viewer_content_for's docstring). Rendering
   them here instead means they're never truncated and take this page's own font, not the
   browser's plain default the embedded nilearn page has no styling for at all. */
.anatomy-subject-title {{ font-size: 20px; font-weight: 600; margin: 0 0 10px; text-align: center; }}
/* 30-09-26: the caption used to run the panel's full 1100px - a ~150-character line that wraps
   at an arbitrary point and is genuinely hard to read. Capped at a normal measure and centred;
   the extra line-height is what stops the two lines reading as one block. */
.anatomy-caption {{
    font-size: 16px; line-height: 1.6; color: #595959; text-align: center;
    max-width: 68ch; margin: 0 auto 26px;
}}
/* The secondary half of a caption (why this map is what it is), one step quieter than the
   sentence that says what the colour means. */
.anatomy-note {{ display: block; margin-top: 6px; font-size: 14.5px; color: #767676; }}
/* 29-09-26: a per-cluster map built from fewer subjects than the cluster actually has (some
   unresolvable on disk, see resolve_available_lesion_paths) - visually distinct (amber) from
   the plain gray .anatomy-caption above it, so a real data gap doesn't read as routine text. */
/* 29-09-26 feedback: a real data gap was a thin amber line that read as routine caption text.
   Now a boxed callout - vivid label, BLACK body text (the body is the information; coloring it
   would make the whole block read as decoration and cost contrast), a colored left rule, a soft
   gradient and a low shadow to lift it off the page. */
.anatomy-warning {{
    font-size: 16px; line-height: 1.55; color: {_TEXT_COLOR}; text-align: left;
    background: #f4f4f3; border: 1px solid #e4e4e2; border-left: 5px solid #c26a00;
    border-radius: 10px; padding: 16px 20px; margin: 0 0 22px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}}
/* The one vivid element: the label alone says "not routine caption text", so the surface can
   stay a neutral grey a shade off the white page (29-09-26, on request: the amber wash read as
   a colored block of its own rather than as a quiet callout). */
.anatomy-warning .warning-label {{
    display: block; font-size: 13px; font-weight: 800; letter-spacing: 0.10em;
    text-transform: uppercase; color: #c26a00; margin-bottom: 6px;
}}
/* The subject ids that follow the message - long, scannable, and not prose. */
.anatomy-warning .warning-detail {{ display: block; margin-top: 8px; font-size: 14.5px; color: #5f5f5c; word-break: break-word; }}
/* Cross-cluster comparison table under the "Descrizione del cluster" figure (29-09-26, on
   request: "statistiche numeriche, più sotto, a confronto tra tutti i vari cluster"). A table,
   not a second chart, on purpose: the ask was for the numbers themselves, and 5-8 clusters x 5
   variables is past the point where color classes stay distinguishable. tabular-nums so the
   digits line up down a column, which is the whole reason to read it as a table. */
.stats-table-wrap {{ margin-top: 36px; overflow-x: auto; }}
.stats-table {{ border-collapse: collapse; width: 100%; }}
.stats-table th {{
    font-size: 12.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    color: #6e6e6e; text-align: right; padding: 0 16px 11px; white-space: nowrap;
    border-bottom: 2px solid #d8d8d8;
}}
.stats-table th:first-child, .stats-table td:first-child, .stats-table th.text-col, .stats-table td.text-col {{ text-align: left; }}
.stats-table td {{ padding: 17px 16px 15px; font-size: 17px; text-align: right; border-bottom: 1px solid #f2f2f2; vertical-align: top; }}
.stats-table tbody tr:last-child td {{ border-bottom: none; }}
.stats-table tr.selected td {{ background: #f4f9fd; }}
.stats-cluster {{ display: flex; align-items: center; gap: 10px; white-space: nowrap; font-weight: 600; font-size: 16px; }}
/* Same color this cluster has in the embedding scatter (plotting._palette_for_labels) - this
   column's only use of color, and it encodes identity, nothing else. */
.stats-swatch {{ width: 13px; height: 13px; border-radius: 3px; flex: none; }}
/* The value carries the weight; the ± spread is secondary ink beside it, not a second number
   competing for attention. tabular-nums so digits line up down a column. Bold (02-10-26
   feedback), one step heavier than .stats-cluster's own 600 - this is the number the table
   exists to show, the rest of the row is context for it. */
.stat-value {{
    font-size: 17px; font-weight: 700; color: {_TEXT_COLOR}; font-variant-numeric: tabular-nums;
    line-height: 1.3; white-space: nowrap;
}}
/* 30-09-26, on request: the ± spread is part of the same number as the mean, so it wears the
   same size, weight and ink. Only the coverage line below stays small and grey - that is the
   annotation, not the value. */
.stat-sd {{ margin-left: 4px; }}
.stat-empty {{ color: #b8b8b8; font-weight: 400; }}
/* Coverage, printed under the value only where the variable does not cover the whole
   cluster (_coverage_note). */
.stats-n {{ display: block; font-size: 15px; color: #767676; margin-top: 6px; font-weight: 400; font-variant-numeric: tabular-nums; }}
.stats-caption {{ font-size: 14.5px; line-height: 1.75; color: #6e6e6e; margin: 20px 0 0; }}
.stats-caption b {{ color: {_TEXT_COLOR}; font-weight: 600; }}
.anatomy-viewer-wrap {{ display: flex; justify-content: center; }}
.anatomy-viewer-wrap iframe {{ border: none; }}
/* Same pill shape as .color-buttons button - the save actions per panel read as the same
   family of control, not a second, differently-styled button style. Two buttons per panel
   now ("Salva HTML" + "Salva PNG", 11-09-26) - .save-btn-row lays them out side by side instead
   of each carrying its own centering margin. */
.save-btn-row {{ display: flex; justify-content: center; gap: 12px; margin-top: 16px; }}
.save-btn {{
    display: block; font-family: inherit; font-size: 13px; padding: 7px 16px; cursor: pointer;
    border: 1px solid #ccc; border-radius: 999px; background: #fff; color: {_TEXT_COLOR};
    transition: border-color 0.15s, background 0.15s;
}}
.save-btn:hover {{ border-color: #4a90d9; }}

/* Page index (08-10-26): a collapsed <details> pinned to the top-right corner, so it is out of the
   way until opened and follows the reader down the page. */
html {{ scroll-behavior: smooth; }}
.page-index {{
    position: fixed; top: 16px; right: 16px; z-index: 1000; max-width: 280px; max-height: 80vh;
    overflow-y: auto; background: #fff; border: 1px solid #ccc; border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.10); font-size: 14px;
}}
.page-index summary {{ cursor: pointer; font-weight: 700; padding: 9px 16px; list-style-position: inside; }}
.page-index nav {{ display: flex; flex-direction: column; padding: 2px 8px 10px; }}
.page-index-link {{ padding: 6px 10px; border-radius: 8px; color: {_TEXT_COLOR}; text-decoration: none; }}
.page-index-link:hover {{ background: #f0f7fd; }}
/* Comparison section (08-10-26): the two run pickers are wider than a normal picker-field, since
   a run label names modality, method and the whole run directory. */
.picker-field.wide {{ min-width: 460px; }}
/* The comparison tables (08-10-26 feedback: headers such as "Mediana cluster 1" made every column as
   wide as its title, so the table ran off the page): a header may break at "\n" and then stays as
   narrow as its longest word, centred above its numbers. */
.comparison-table-wrap {{ margin-top: 24px; }}
.comparison-table th {{ white-space: pre-line; text-align: center; vertical-align: bottom; line-height: 1.35; padding: 0 12px 11px; }}
.comparison-table th.text-col {{ text-align: left; }}
.comparison-table td {{ padding-left: 12px; padding-right: 12px; text-align: center; }}
.comparison-table td.text-col {{ text-align: left; }}
/* A note that was one long paragraph is now a short lead sentence plus one line per idea. */
.comparison-points {{ font-size: 16.5px; line-height: 1.6; color: #595959; max-width: 78ch; margin: 0 auto 22px; padding-left: 22px; }}
.comparison-points li {{ margin: 6px 0; }}
.comparison-points b {{ color: {_TEXT_COLOR}; font-weight: 600; }}
.comparison-lead {{ font-size: 17px; line-height: 1.55; color: {_TEXT_COLOR}; max-width: 78ch; margin: 0 auto 8px; }}
#comparison-cluster-row {{ margin-top: 28px; }}
.comparison-rule {{ max-width: 760px; margin: 20px auto 8px; text-align: center; font-size: 16px; line-height: 1.55; color: #595959; }}
.comparison-heading {{ font-size: 26px; font-weight: 800; margin: 56px 0 14px; text-align: center; }}
.comparison-subheading {{ font-size: 28px; font-weight: 700; margin: 56px 0 18px; }}
.comparison-note {{ font-size: 15.5px; line-height: 1.6; color: #595959; max-width: 78ch; margin: 28px auto 22px; }}
.comparison-note.centered {{ text-align: center; }}
.comparison-summary {{ margin: 28px auto 0; max-width: 78ch; font-size: 16px; line-height: 1.5; }}
.comparison-summary p, .comparison-summary-line {{ margin: 4px 0; }}
.comparison-summary-line {{ text-align: center; font-size: 17px; }}
.comparison-guide {{ margin: 32px 0 40px; font-size: 15.5px; line-height: 1.6; color: #595959; }}
.comparison-guide summary {{ cursor: pointer; font-size: 22px; font-weight: 700; color: {_TEXT_COLOR}; }}
.comparison-guide .stats-table {{ margin-top: 12px; max-width: 520px; }}
.comparison-guide .comparison-points {{ margin: 18px 0 14px; max-width: none; }}
.comparison-guide .comparison-subheading {{ font-size: 18px; margin: 22px 0 0; }}
"""


_INDEX_STRING = f"""<!DOCTYPE html>
<html>
<head>
{{%metas%}}
<title>NEMESIS — Embedding Explorer</title>
{{%favicon%}}
{{%css%}}
<style>{CSS}</style>
</head>
<body>
{{%app_entry%}}
<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>"""


def _italian_figure(figure: go.Figure) -> go.Figure:
    """`figure` with ',' as decimal separator and '.' for thousands in every number Plotly formats (ticks, hover,
    colorbars), as format_number does for the text of the page."""
    return figure.update_layout(separators=PLOTLY_SEPARATORS)
