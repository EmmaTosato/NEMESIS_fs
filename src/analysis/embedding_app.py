"""Logic behind src.pipeline.embedding_app - a live Dash app to explore any already-written
dim_reduction.py OR clustering.py production run interactively (2D or 3D, color buttons
instead of a dropdown, editorial styling), replacing the old per-run
embedding_plot_interactive.html (removed 2026-08-14, see src/analysis/plotting.py's module
docstring and docs/guides/embedding_app.md).

Extended 15-08-26 (docs/dev/clustering_migration_plan.md §3, the `X.shape[1] == 3` row) to
also discover clustering.py's own production runs, not just dim_reduction.py's - both write
the exact same on-disk shape (matrix.npy/metadata.csv/manifest.json under
production/<method>/<run_name>, see src.utils.artifacts.save_matrix), so a single discovery
pass generalizes over the `<pipeline>` path segment (`dim_reduction` or `clustering`) rather
than needing two separate code paths. A clustering run's metadata.csv additionally has a
`cluster_label` column (src.analysis.clustering_tuning appends it in production, see
clustering.py::_run_one_method) - registered as its own COLOR_MODES entry
(src/analysis/embedding_coloring.py), so this app can color a clustering run by cluster same
as it colors any run by dataset/side/volume/nihss, all through the same generic mechanism.

No refit, no server-side recomputation of the embedding itself - reads matrix.npy/metadata.csv
straight off disk (src.utils.artifacts.load_matrix), same "replot, never re-fit" contract
src/pipeline/replot_dim_reduction.py already established, extended here to cover 3-component runs
too (that script only ever handled 2). A run whose own saved embedding has more than 3
columns (e.g. a real production run kept at its full n_components, no viz-only projection
ever persisted to disk - see production_run_display_error's docstring) is reported as
undisplayable rather than silently sliced to its first 2/3 columns - lessons_learned.md #16.

Kept separate from src/analysis/understanding_umap_report.py / understanding_umap_dash.py on
purpose: those read fine-tuning sweep output (tuning_results.csv/embeddings.npz across a whole
metric x n_neighbors x min_dist grid) to explore *how a parameter choice shapes the embedding*;
this module reads exactly one already-chosen production run at a time, to explore *the result
production settled on* - same distinction the user drew explicitly (14-08-26): "questi fanno
tuning, noi dobbiamo fare production". Two different questions, two different tools - not
sharing a module just because both end up building Plotly figures.

Extended 01-09-26 with two anatomy panels, both promoted from exploratory notebook prototypes
(notebooks/post-results_analysis/embeddings_analysis.ipynb §4,
embedding_to_anatomy_mapping.ipynb §2 - the latter's own docstring already flagged this
promotion as its natural next step) onto src.analysis.anatomical_maps: clicking a point in the
embedding shows that subject's real lesion in an interactive nilearn 3D viewer
(lesion_viewer_content_for), and any clustering.py run (metadata has cluster_label) additionally
gets a per-cluster lesion overlap/frequency map (overlap_map_content_for). Same "no caching,
always a fresh disk read + rebuild" philosophy as the rest of this module - see build_app's own
docstring.
"""

from __future__ import annotations

import io
import itertools
import logging
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate
from nilearn import plotting as nilearn_plotting
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.anatomical_maps import (
    BinaryMaskStore,
    build_mean_map,
    build_overlap_map,
    resolve_available_lesion_paths,
    resolve_lesion_paths,
)
from src.analysis.cluster_description import (
    CLUSTER_DESCRIPTION_VARIABLES,
    ClusterDescriptionVariable,
    ClusterStats,
    build_cluster_description_figure,
    cluster_composition,
    clusters_comparison_stats,
)
from src.analysis.embedding_coloring import COLOR_MODES
from src.analysis.embedding_coloring import (
    DEFAULT_VOLUME_GRID,
    VOLUME_MODE,
    available_volume_grids,
    volume_grid_column,
)
from src.analysis.embedding_coloring import color_values as read_color_values
from src.analysis.params import load_tag_params
from src.analysis.plotting import (
    _CATEGORICAL_PALETTE,
    _NOISE_COLOR,
    _palette_for_labels,
    compose_embedding_plot_title,
)
from src.utils.artifacts import MANIFEST_FILENAME, load_matrix, read_run_config, read_run_params

# "neutro" first, same convention as embedding_coloring.COLOR_MODES/the notebook prototype -
# the neutral single-color view is always available and always the default, every other
# entry is a registered color_by mode name.
NEUTRAL_MODE = "neutro"
COLOR_MODE_ORDER: tuple[str, ...] = (NEUTRAL_MODE, *COLOR_MODES.keys())

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
/* The volume-grid chooser, shown under the colour chips only while "volume" is active
   (30-09-26, on request). Same chip family as the row above, one step quieter, with a label
   so a lone "2mm" button is not a mystery. */
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
.graph-wrap {{ display: flex; justify-content: center; width: 100%; }}
.graph-wrap > div {{ width: 100%; }}
.status-message {{ text-align: center; color: #595959; font-size: 18px; margin: 64px 0; }}
/* Shared by all 3 section headings (Embedding Visualization / Anatomia lesionale / Overlap map
   per cluster, 01-09-26) - a class of its own rather than a nesting-based ".anatomy-panel h2"
   selector, since "Embedding Visualization" sits above the scatter, outside any .anatomy-panel.
   Same weight/scale family as .page-title (32px) - a real section header, not the 20px
   subheading this panel used to read as (feedback: "va scritto più grande" / "un pelo più
   grande" on a follow-up pass). */
.section-heading {{ font-size: 30px; font-weight: 800; margin: 40px 0 20px; text-align: center; }}
/* Anatomy panels (lesion viewer / cluster overlap map, 01-09-26) - same page-width container as
   .page itself (not .graph-wrap's centered flex, these are full-width blocks with their own
   heading), separated from the picker/scatter above by a thin rule instead of a boxy border. */
.anatomy-panel {{ margin-top: 56px; padding-top: 32px; border-top: 1px solid {_GRID_BORDER}; }}
/* The per-subject -> per-cluster break (30-09-26). A heavier rule than .anatomy-panel's own
   hairline, because this separates two kinds of question, not two panels of the same kind. */
.section-divider {{ margin-top: 88px; padding-top: 52px; border-top: 3px solid {_TEXT_COLOR}; }}
.section-title {{ font-size: 40px; font-weight: 800; letter-spacing: -0.01em; text-align: center; margin: 0 0 10px; }}
.section-intro {{ font-size: 17px; color: #595959; text-align: center; margin: 0 0 28px; }}
/* The chooser that scopes every panel below: centred and wider than a picker-row field, so it
   reads as this section's own control rather than as one more form field. */
.cluster-chooser {{
    display: flex; flex-direction: column; align-items: center; gap: 8px;
    max-width: 260px; margin: 0 auto 8px;
}}
.cluster-chooser > div {{ width: 100%; }}
.cluster-chooser .picker-label {{ font-size: 14px; }}
/* The panel directly under the chooser must not re-draw the section break with its own rule. */
.section-divider + .anatomy-panel {{ margin-top: 40px; border-top: none; padding-top: 0; }}
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
.stats-table th:first-child, .stats-table td:first-child {{ text-align: left; }}
.stats-table td {{ padding: 17px 16px 15px; text-align: right; border-bottom: 1px solid #f2f2f2; vertical-align: top; }}
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
.stats-n {{ display: block; font-size: 12.5px; color: #a0a0a0; margin-top: 6px; font-weight: 400; font-variant-numeric: tabular-nums; }}
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
"""


# The 2 production pipelines this app knows how to discover/display, in preference order
# (used only to pick a sensible default in the "Pipeline" picker - dim_reduction is the more
# mature, more commonly explored pipeline, see README.md's "what's implemented so far" - not
# an alphabetical accident like every other *_options helper below, so kept as its own
# explicitly ordered constant rather than a set).
PRODUCTION_PIPELINES: tuple[str, ...] = ("dim_reduction", "clustering")


@dataclass(frozen=True)
class ProductionRun:
    """One production run discovered under results/<modality>/<pipeline>/production/<method>/
    [<reduction_method>/]<run_name> (pipeline is "dim_reduction" or "clustering", see
    PRODUCTION_PIPELINES) - path is the absolute run directory (what load_matrix needs), the
    rest are its own path segments (what the UI and compose_embedding_plot_title need), kept
    apart rather than re-parsed from path every time.

    reduction_method is None for a dim_reduction.py run (no such segment exists in its path -
    method there already *is* the reduction method) and a real value (e.g. "umap", or "raw" for
    clustering directly on an un-reduced matrix) for a clustering.py run (31-08-26,
    src.analysis.model_config.ClusteringConfig.reduction_method) - the extra segment exists so
    clustering results from different source embeddings never land in the same folder.
    """

    modality: str
    pipeline: str
    method: str
    run_name: str
    path: Path
    reduction_method: str | None = None

    @property
    def key(self) -> str:
        """Stable, unique-per-run string - used as a Dash dropdown option value (Dash
        options need a hashable, JSON-serializable value, not a Path)."""
        parts = [self.modality, self.pipeline, self.method]
        if self.reduction_method is not None:
            parts.append(self.reduction_method)
        parts.append(self.run_name)
        return "/".join(parts)

    @property
    def results_relative_path(self) -> Path:
        """<modality>/<pipeline>/production/<method>/[<reduction_method>/]<run_name>, prefixed
        with "results" - compose_embedding_plot_title (src/analysis/plotting.py) derives the
        modality from an output_dir's own path segments and expects a "results/..."-relative
        Path, not an absolute one (an absolute path's first segment is "/", not "results" - see
        notebooks/post-results_analysis's own fix for the identical issue, 13-08-26)."""
        base = Path("results") / self.modality / self.pipeline / "production" / self.method
        if self.reduction_method is not None:
            base = base / self.reduction_method
        return base / self.run_name


@dataclass(frozen=True)
class LesionViewerConfig:
    """Everything src.analysis.anatomical_maps needs to resolve/build a lesion anatomy map,
    bundled so callbacks don't carry 5 loose params (same reasoning as ProductionRun itself).
    Built once at startup by src.pipeline.embedding_app from build_lesion_matrix.json (via
    src.analysis.build_config.load_build_matrix_config) - the same config/loader
    build_lesion_matrix.py itself uses, never re-parsed by hand here.
    """

    data_root: Path
    lesion_glob: str
    reference_img: nib.Nifti1Image
    binarize_threshold: float
    resample_interpolation: str


# Same fixed pattern as src.features.sdc.build_sdc_voxelwise_matrix's own
# f"sdc/*/*_res-1_desc-{object_}.nii.gz" with object_="disconnectome" - this app only ever wants
# the disconnectome map itself (never "lesion", SDC's own other known object, see
# src.features.sdc.KNOWN_OBJECTS - that one is already covered by the lesion viewer above,
# reading straight from manual_masks/ instead of sdc/), so the pattern is inlined as a plain
# constant here rather than threading an unused object_ parameter through SdcViewerConfig.
SDC_DISCONNECTOME_GLOB = "sdc/*/*_res-1_desc-disconnectome.nii.gz"


@dataclass(frozen=True)
class SdcViewerConfig:
    """Everything the SDC disconnectome anatomy panels need - same bundling reasoning as
    LesionViewerConfig. Built once at startup by src.pipeline.embedding_app from
    build_sdc_matrix.json's own voxelwise fields (via
    src.analysis.build_config.load_build_sdc_matrix_config) - the same config/loader
    build_sdc_matrix.py itself uses for its 'voxelwise' representation, never re-parsed by hand
    here. Its own reference_img/resample_interpolation are loaded separately from
    LesionViewerConfig's (never reused across the two - build_sdc_matrix.json's own
    reference_template_path is a different grid, res-1, from build_lesion_matrix.json's res-2,
    confirmed by reading both configs rather than assumed identical).

    No binarize_threshold, unlike LesionViewerConfig: disconnectome values are a continuous
    [0, 1] probability, never binarized (see src.features.sdc's own module docstring) - both
    anatomy panels below use a near-zero display threshold instead (same reasoning as the lesion
    cluster-overlap map's own 1e-6, see overlap_map_content_for).
    """

    data_root: Path
    disconnectome_glob: str
    reference_img: nib.Nifti1Image
    resample_interpolation: str


def discover_production_runs(results_root: Path) -> list[ProductionRun]:
    """Scans results_root/*/<pipeline>/production/*/* (dim_reduction) or
    results_root/*/<pipeline>/production/*/*/* (clustering, one extra <reduction_method>
    segment - 31-08-26) for valid run directories (must contain manifest.json - the same
    existence check src.utils.artifacts.load_matrix itself uses to decide a run was actually
    completed, not left behind by an interrupted build), across every pipeline in
    PRODUCTION_PIPELINES.

    Generic across modality/method on purpose (2026-08-14, on request: "Tutti, generico") -
    today only lesion/umap (plus lesion/pca, lesion/tsne, lesion/pacmap, lesion/clustering's
    various methods) exist, but a future modality (e.g. sdc) or method needs zero changes here
    to show up, since nothing about the path shape is hardcoded beyond <pipeline>/production's
    own fixed segments. `clustering.py`'s old "comparison" pseudo-method directory (its own
    generation removed 01-09-26, docs/dev/models.md - existing ones from before that date can
    still sit on disk) is naturally excluded here without any special-casing: it only ever held
    a config.md, never a manifest.json, so it fails the same existence check every other
    incomplete/non-run directory does.

    Returns an empty list if results_root doesn't exist or has no matching runs at all - not
    an error: a completely fresh checkout with no pipeline ever run is a legitimate starting
    state for this app (the caller/UI decides how to represent "nothing to show").
    Sorted by (modality, pipeline, method, reduction_method, run_name) for a deterministic
    dropdown order.
    """
    if not results_root.exists():
        return []
    runs = []
    for pipeline in PRODUCTION_PIPELINES:
        glob_pattern = f"*/{pipeline}/production/*/*/*" if pipeline == "clustering" else f"*/{pipeline}/production/*/*"
        for path in results_root.glob(glob_pattern):
            if not (path.is_dir() and (path / MANIFEST_FILENAME).exists()):
                continue
            # relative_to(results_root)'s own parts, not raw negative indices into the
            # absolute path - self-documenting and correct regardless of how deep
            # results_root's own absolute path happens to be.
            parts = path.relative_to(results_root).parts
            if pipeline == "clustering":
                modality, _pipeline_segment, _production, method, reduction_method, run_name = parts
            else:
                modality, _pipeline_segment, _production, method, run_name = parts
                reduction_method = None
            runs.append(
                ProductionRun(
                    modality=modality, pipeline=pipeline, method=method, reduction_method=reduction_method, run_name=run_name, path=path
                )
            )
    return sorted(runs, key=lambda run: (run.modality, run.pipeline, run.method, run.reduction_method or "", run.run_name))


# A run_name's own leading "DD-MM" (every run seen so far: "13-08_s1.1-vol_m_dice_nc3",
# "23-07_s1.1-vol_c150", ...) - used only to order/default the "Giorno" picker chronologically
# (most recent last), never to validate or reject a run_name that doesn't match: a run
# without a recognizable date prefix still shows up, just sorted alphabetically after every
# dated one instead of crashing the picker over a display-order nicety.
_DATE_PREFIX_RE = re.compile(r"^(\d{2})-(\d{2})_")


def _run_chronological_key(run: ProductionRun) -> tuple:
    match = _DATE_PREFIX_RE.match(run.run_name)
    if match is None:
        return (1, 0, 0, run.run_name)
    day, month = int(match.group(1)), int(match.group(2))
    return (0, month, day, run.run_name)


def modality_options(runs: list[ProductionRun]) -> list[str]:
    """Distinct modalities across `runs`, sorted - step 1 of the picker ("Dato"). Only
    "lesion" exists today; a future modality shows up here with zero code changes (same
    generic-discovery contract as discover_production_runs itself)."""
    return sorted({run.modality for run in runs})


def pipeline_options(runs: list[ProductionRun], modality: str) -> list[str]:
    """Distinct pipelines available for `modality` - step 2 of the picker ("Pipeline"), now a
    real choice (15-08-26) rather than the fixed "dim_reduction · produzione" label it used to
    be, since this app discovers both dim_reduction.py and clustering.py runs. Ordered by
    PRODUCTION_PIPELINES' own preference order, not alphabetically (dim_reduction first,
    matching every other *_options helper's plain `sorted()` would put clustering first
    instead - a worse default given dim_reduction is the more mature pipeline)."""
    available = {run.pipeline for run in runs if run.modality == modality}
    return [pipeline for pipeline in PRODUCTION_PIPELINES if pipeline in available]


def method_options(runs: list[ProductionRun], modality: str, pipeline: str) -> list[str]:
    """Distinct methods available for (modality, pipeline), sorted - step 3 of the picker
    ("Metodo": a dim_reduction method like umap/pca, or a clustering method like
    kmeans/hdbscan, depending on the pipeline chosen in step 2)."""
    return sorted({run.method for run in runs if run.modality == modality and run.pipeline == pipeline})


def runs_for(runs: list[ProductionRun], modality: str, pipeline: str, method: str) -> list[ProductionRun]:
    """Runs matching (modality, pipeline, method), chronologically ordered (oldest first, most
    recent last) - the base scope every later picker step (Metrica/Componenti/Run) narrows
    further. Scoped this tightly is the whole point of the multi-step picker (2026-08-14, on
    request): the original single flat dropdown mixed every method's runs together, so picking
    a run meant scanning entries that weren't even the same method."""
    return sorted(
        (run for run in runs if run.modality == modality and run.pipeline == pipeline and run.method == method),
        key=_run_chronological_key,
    )


# Sentinel for "this axis doesn't apply to this run at all" - shared across all 3 narrowing
# axes this app offers (Metrica/Componenti: PCA/PaCMAP dim_reduction runs have no 'metric' key,
# config/registry/params_reduction.json; Parametri: a clustering run built directly on
# un-reduced data, reduction_method="raw", has no upstream-embedding metric/n_components; a
# clustering method with no tag_param registered at all - none today). One shared "—" rather
# than a separate sentinel per axis, so the picker's placeholder reads identically everywhere.
NO_METRIC = "—"

# Sibling sentinel for "this run's own axis has no 'n_components' value" (see NO_METRIC) - an
# int, not a string like NO_METRIC, to keep n_components_options' return type uniform
# (list[int]) - -1 is safely distinct from any real n_components value (always >= 1).
NO_N_COMPONENTS = -1

def _n_components_option_label(n: int) -> str:
    """Dropdown label for one n_components_options() value - AUDIT_FINDINGS.md #64:
    NO_N_COMPONENTS (-1, the clustering-pipeline sentinel) gets NO_METRIC's own readable
    placeholder ("—") instead of the literal string "-1", the same treatment NO_METRIC
    already gets on the metric picker for the analogous case."""
    return NO_METRIC if n == NO_N_COMPONENTS else str(n)


def run_params(run: ProductionRun) -> dict:
    """The exact resolved params dict the run's own pipeline (dim_reduction.py or
    clustering.py) actually used - never re-derived by parsing the run_name's own free-text
    convention (e.g. "nc3"/"m_dice" is a human-chosen session-name shorthand for umap
    specifically, not a guaranteed, parseable field every method's run_name follows -
    pca/tsne/pacmap/clustering runs don't). Thin wrapper over
    src.utils.artifacts.read_run_params (single source of truth, also reused by
    clustering.py's viz_embedding_path cross-check) - see that function's docstring for the
    exact contract/error cases.
    """
    return read_run_params(run.path)


def run_metadata(run: ProductionRun) -> pd.DataFrame:
    """run's own metadata.csv (subject_id/dataset/... columns), independent of the embedding's
    own dimensionality - unlike load_run, this never raises UndisplayableRunError: the anatomy
    panels (lesion_viewer_content_for, cluster_options) only need metadata's columns, not a
    2-or-3-component embedding to plot, so a run with e.g. n_components=10 still exposes them.
    """
    _matrix, metadata, _extra_arrays = load_matrix(run.path)
    return metadata


def _run_params_or_none(run: ProductionRun) -> dict | None:
    """run_params(run), isolated per-run (HIGH #25, 2026-08 - lesson #21). The 3 picker
    helpers below each call this once per run in a comprehension - a single run with a
    corrupt/truncated config.md must not take down every other run's picker options with
    it (e.g. metric_options iterating 8 runs for one method, one has a bad config.md ->
    the whole method used to become unexplorable in the app, not just that one run).
    None on failure, logged as a warning - callers filter it out and keep going.
    """
    try:
        return run_params(run)
    except ValueError as exc:
        logging.warning("%s: cannot read resolved params, excluding this run from picker options: %s", run.path, exc)
        return None


def run_reduction_axis(run: ProductionRun) -> tuple[str, int]:
    """(metric, n_components) of the embedding actually behind this run's own points.

    For a dim_reduction.py run that's the run's own resolved params (run_params). For a
    clustering.py run that's the *upstream* embedding's own metric/n_components (config.md's
    "## Config" fenced block - reduction_metric/reduction_n_components, 31-08-26 -
    src.utils.artifacts.read_run_config - never the clustering method's own hyperparameters,
    which have no metric/n_components concept at all, see tag_param_options for those).
    01-09-26: real clustering runs are built from more than one source embedding (different
    metric/n_components), so this app must let that vary per run here too, not collapse every
    clustering run to one sentinel the way it used to.

    NO_METRIC/NO_N_COMPONENTS when a run genuinely has neither (pca/pacmap for dim_reduction; a
    clustering run built directly on raw un-reduced data - reduction_method="raw" - config.md
    then records reduction_metric/reduction_n_components as "", not a real value).
    """
    if run.pipeline == "dim_reduction":
        params = run_params(run)
        return params.get("metric", NO_METRIC), params.get("n_components", NO_N_COMPONENTS)
    config = read_run_config(run.path)
    metric = config.get("reduction_metric") or NO_METRIC
    raw_n_components = config.get("reduction_n_components") or None
    n_components = int(raw_n_components) if raw_n_components else NO_N_COMPONENTS
    return metric, n_components


def _run_reduction_axis_or_none(run: ProductionRun) -> tuple[str, int] | None:
    """run_reduction_axis(run), isolated per-run (same reasoning as _run_params_or_none) - a
    single run with a corrupt/truncated config.md must not take down every other run's picker
    options with it."""
    try:
        return run_reduction_axis(run)
    except ValueError as exc:
        logging.warning("%s: cannot read resolved reduction axis, excluding this run from picker options: %s", run.path, exc)
        return None


def _runs_for_reduction_axis(
    runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str, n_components: int
) -> list[ProductionRun]:
    """runs_for(...) further narrowed to runs whose own run_reduction_axis equals
    (metric, n_components) - the shared filter metric_options/n_components_options/
    tag_param_options/runs_matching all build on, so "which embedding is this run on" is
    computed in exactly one place. Order preserved from runs_for's own chronological sort."""
    return [
        run
        for run in runs_for(runs, modality, pipeline, method)
        if (axis := _run_reduction_axis_or_none(run)) is not None and axis == (metric, n_components)
    ]


def metric_options(runs: list[ProductionRun], modality: str, pipeline: str, method: str) -> list[str]:
    """Distinct `metric` values actually used by (modality, pipeline, method)'s own runs,
    sorted - NO_METRIC included if any of them has no metric axis at all (run_reduction_axis).
    For a clustering.py run this is the *upstream embedding's* own metric, not the clustering
    method's hyperparameters (see tag_param_options for those)."""
    values = {
        axis[0]
        for run in runs_for(runs, modality, pipeline, method)
        if (axis := _run_reduction_axis_or_none(run)) is not None
    }
    return sorted(values)


def n_components_options(runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str) -> list[int]:
    """Distinct `n_components` values among (modality, pipeline, method, metric)'s own runs
    (metric being run_reduction_axis's own upstream-embedding metric, see metric_options),
    sorted ascending - includes every value actually used, even ones this app can't display
    (e.g. 150 for the full-dimensionality PCA production run): the picker's job is to reflect
    what was actually run, not to pre-filter it down to what's displayable (graph_content_for
    already reports that clearly per-run, see UndisplayableRunError)."""
    values = {
        axis[1]
        for run in runs_for(runs, modality, pipeline, method)
        if (axis := _run_reduction_axis_or_none(run)) is not None and axis[0] == metric
    }
    return sorted(values)


def _run_tag_param_label(run: ProductionRun, tag_param: list[str]) -> str | None:
    """Human-readable "key=value, key2=value2" combination of `run`'s own values for
    `tag_param` (params_clustering.json's registered hyperparameter names for this method, in
    their own declared order) - doubles as the tag_param picker's own option value (two runs
    with the same combination share the same label by construction, no separate encode/decode
    step needed). None if `run`'s own params can't be read, or don't actually carry one of the
    registered keys (a registry/artifact mismatch - excluded, not guessed)."""
    params = _run_params_or_none(run)
    if params is None:
        return None
    try:
        values = {key: params[key] for key in tag_param}
    except KeyError as exc:
        logging.warning("%s: params missing tag_param key %s, excluding this run from picker options", run.path, exc)
        return None
    return ", ".join(f"{key}={value}" for key, value in values.items())


def _load_tag_params_or_none(clustering_params_file: str | Path, method: str) -> list[str] | None:
    """load_tag_params(clustering_params_file, method), isolated the same way
    _run_params_or_none isolates a single run's own corrupt config.md (lesson #21) - but here
    the failure isn't per-run, it's per-method: `method` has production runs on disk (that's
    the only way this app ever offers it as a choice, see method_options) yet has no entry at
    all in clustering_params_file (config/registry/params_clustering.json) - a real
    registry/artifact mismatch, e.g. a method renamed/dropped from the registry after its
    production output was already written (lessons_learned.md #12 - this happened for real,
    dbscan -> hdbscan). None on failure, logged as a warning - callers treat it the same as "no
    tag_param declared for this method" (NO_METRIC), never a raw crash of the Parametri picker
    step."""
    try:
        return load_tag_params(clustering_params_file, method)
    except ValueError as exc:
        logging.warning(
            "%s: method %r has production runs but no entry in the clustering params registry, "
            "cannot resolve its tag_param combinations: %s", clustering_params_file, method, exc,
        )
        return None


def tag_param_options(
    runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str, n_components: int,
    clustering_params_file: str | Path,
) -> list[str]:
    """Distinct combinations of `method`'s own registered tag_param values
    (config/registry/params_clustering.json, e.g. n_clusters+linkage for agglomerative,
    min_cluster_size+min_samples for hdbscan) actually run among (modality, pipeline, method)'s
    runs on the (metric, n_components) upstream embedding - 01-09-26, on request: a flat "Run"
    dropdown mixing every k/linkage combination together, with no way to narrow by them, was the
    exact complaint that prompted this step.

    dim_reduction pipeline runs, any clustering method with no tag_param registered at all (none
    today - every params_clustering.json entry declares at least one), and a clustering method
    missing from the registry entirely (_load_tag_params_or_none) all resolve to exactly
    [NO_METRIC] (this axis's own "doesn't apply" sentinel - reused rather than a redundant third
    one, see NO_METRIC's own docstring) - the last case still logs a warning naming the real
    cause, so a registry/artifact mismatch is never silently indistinguishable from "this method
    genuinely has no tag_param" in the logs, even though the picker UI reads the same either way."""
    if pipeline != "clustering":
        return [NO_METRIC]
    tag_param = _load_tag_params_or_none(clustering_params_file, method)
    if not tag_param:
        return [NO_METRIC]
    labels = {
        label
        for run in _runs_for_reduction_axis(runs, modality, pipeline, method, metric, n_components)
        if (label := _run_tag_param_label(run, tag_param)) is not None
    }
    return sorted(labels)


def runs_matching(
    runs: list[ProductionRun], modality: str, pipeline: str, method: str, metric: str, n_components: int,
    tag_params_label: str, clustering_params_file: str | Path,
) -> list[ProductionRun]:
    """Runs matching (modality, pipeline, method, metric, n_components, tag_params_label)
    exactly, chronologically ordered - the final picker step ("Run"): today this is usually
    exactly one run (each combination has only ever been produced once), but stays a list rather
    than assuming that - a rerun of the same combination on a later date is a legitimate, real
    scenario this picker must keep showing both of, not silently collapse to one.

    dim_reduction pipeline runs (tag_params_label always NO_METRIC there, see tag_param_options)
    skip the tag_params_label filter entirely - it's a no-op for them, not a real narrowing. Same
    for a clustering method missing from the registry (_load_tag_params_or_none) - tag_param_options
    already collapses that case to NO_METRIC too, so this filter is consistently a no-op for it here,
    never a second crash site for the same registry gap (this function has its own direct
    load_tag_params call, a separate caller from tag_param_options - see AUDIT_FINDINGS-style
    isolation, both call sites of the same registry lookup need the same isolation, not just the
    first one found)."""
    candidates = _runs_for_reduction_axis(runs, modality, pipeline, method, metric, n_components)
    if pipeline != "clustering" or tag_params_label == NO_METRIC:
        return candidates
    tag_param = _load_tag_params_or_none(clustering_params_file, method)
    if not tag_param:
        return []
    return [run for run in candidates if _run_tag_param_label(run, tag_param) == tag_params_label]


class UndisplayableRunError(ValueError):
    """A production run's saved embedding has more than 3 columns - no viz-only projection
    was ever persisted for it (dim_reduction.py's viz_embedding is refit in-memory and used
    only to write the now-removed embedding_plot_interactive.html/PNGs at production time,
    never saved to disk on its own), and this app, like src/pipeline/replot_dim_reduction.py, never
    reloads the original feature matrix to refit one - slicing embedding[:, :3] instead would
    be the exact mistake lessons_learned.md #16 documents (a UMAP/t-SNE/PaCMAP embedding's
    columns carry no importance ordering, so a slice is an arbitrary cut, not a summary)."""


def load_run(run: ProductionRun) -> tuple[np.ndarray, pd.DataFrame]:
    """Loads `run`'s embedding + metadata via load_matrix, raising UndisplayableRunError (not
    silently slicing) if the saved embedding has other than 2 or 3 columns."""
    embedding, metadata, _extra_arrays = load_matrix(run.path)
    n_dims = embedding.shape[1]
    if n_dims not in (2, 3):
        # AUDIT_FINDINGS.md #43/#44: this message used to always point at dim_reduction.py's
        # viz_n_components, even for a clustering.py run - clustering.py has no such config
        # field (it never reduces dimensionality itself, see docs/dev/models.md's
        # "reduced_data (declarative-only)" section) and rerunning it would leave matrix.npy's
        # dimensionality unchanged either way, so that advice would not fix anything there.
        if run.pipeline == "dim_reduction":
            fix_hint = "rerun dim_reduction.py with viz_n_components 2 or 3, or pick a different run"
        else:
            fix_hint = (
                f"{run.pipeline}.py does not reduce dimensionality itself - point its input_path at an "
                "already-2-or-3-component matrix (e.g. a dim_reduction.py production embedding), or pick a different run"
            )
        raise UndisplayableRunError(
            f"Run {run.path} has a saved embedding with {n_dims} components - this app can only display an "
            f"already-2-or-3-component embedding: {fix_hint}."
        )
    return embedding, metadata


def _color_label(mode_name: str) -> str | None:
    return None if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label


def run_title(run: ProductionRun, mode_name: str) -> str:
    """Same production-style title every other plot in this pipeline uses (e.g. "Lesions -
    Umap - dataset") - compose_embedding_plot_title is the single source of truth for this
    format, never re-derived by hand here."""
    return compose_embedding_plot_title(run.results_relative_path, run.method, _color_label(mode_name))


def _palette_for(categories: list[str], missing_label: str = "unknown") -> dict[str, str]:
    palette: dict[str, str] = {}
    colors = itertools.cycle(_CATEGORICAL_PALETTE)
    for category in categories:
        palette[category] = _NOISE_COLOR if category == missing_label else next(colors)
    return palette


def _log_decade_ticks(values: np.ndarray) -> tuple[list[float], list[str]]:
    """Decade tick positions (in log10 space) spanning `values`' real (non-log) range, e.g.
    [1, 10, 100, 1000] for a 1..2000 range - the same "one tick per order of magnitude" a
    matplotlib LogNorm colorbar's default LogFormatter would pick, reimplemented here because
    Plotly has no log-scale colorbar of its own (see build_embedding_figure's docstring)."""
    lo = int(np.floor(np.log10(values.min())))
    hi = int(np.ceil(np.log10(values.max())))
    ticks = [10.0**exponent for exponent in range(lo, hi + 1)]
    return [float(np.log10(tick)) for tick in ticks], [f"{tick:g}" for tick in ticks]


def build_embedding_figure(
    embedding: np.ndarray,
    metadata: pd.DataFrame,
    mode_name: str,
    xlabel: str,
    ylabel: str,
    title: str,
    zlabel: str | None = None,
    volume_grid: str = DEFAULT_VOLUME_GRID,
) -> go.Figure:
    """Builds the Plotly figure for one (run, color mode) combination - 2D if `zlabel` is
    None, 3D otherwise (branches on `embedding.shape[1]`/`zlabel` the same way the
    post-results_analysis notebook's show_embedding_plotly prototype does, since this
    function IS that prototype, promoted to reusable src/ code once the notebook exploration
    settled on a final style - never a re-derivation by hand).

    Unlike the removed plot_embedding_interactive, a continuous mode's log_scale is honored
    here: values are log10-transformed for the marker color, with the colorbar's own ticks
    relabeled back to real units (_log_decade_ticks) - plotly has no direct LogNorm-equivalent
    color axis, so this is done by hand rather than left linear as the old function was.

    Raises UndisplayableRunError-independent ValueErrors for a bad embedding/mode/metadata
    combination (e.g. `mode_name` not in COLOR_MODE_ORDER) - a caller that only ever offers
    COLOR_MODE_ORDER's own entries as UI choices should never actually hit these.
    """
    if mode_name not in COLOR_MODE_ORDER:
        raise ValueError(f"unknown color mode {mode_name!r} - known: {list(COLOR_MODE_ORDER)}")
    is_3d = zlabel is not None
    if is_3d and embedding.shape[1] != 3:
        raise ValueError(f"zlabel given but embedding has {embedding.shape[1]} columns, not 3")
    if not is_3d and embedding.shape[1] < 2:
        raise ValueError(f"The figure needs at least 2 columns, got shape {embedding.shape}")

    scatter_cls = go.Scatter3d if is_3d else go.Scatter
    marker_kwargs = dict(
        size=6,
        opacity=1.0 if is_3d else 0.85,
        line=dict(width=0.6, color="white") if is_3d else dict(width=0),
    )
    subject_ids = metadata["subject_id"].to_numpy() if "subject_id" in metadata.columns else None

    def _trace_kwargs(mask: np.ndarray | None = None) -> dict:
        idx = np.where(mask)[0] if mask is not None else np.arange(embedding.shape[0])
        kw = dict(x=embedding[idx, 0], y=embedding[idx, 1])
        if is_3d:
            kw["z"] = embedding[idx, 2]
        if subject_ids is not None:
            kw["text"] = subject_ids[idx]
            kw["hoverinfo"] = "text"
        return kw

    fig = go.Figure()
    has_colorbar = False  # set below for a continuous mode - moves the legend so it can't sit on top of it

    if mode_name == NEUTRAL_MODE:
        fig.add_trace(scatter_cls(**_trace_kwargs(), mode="markers", marker=dict(color="#3aa9e0", **marker_kwargs)))
    else:
        mode = COLOR_MODES[mode_name]
        # The volume mode reads whichever grid the button row below the colour chips has
        # selected; every other mode uses its own declared registry column.
        registry_column = volume_grid_column(volume_grid) if mode_name == VOLUME_MODE else None
        values = read_color_values(metadata, mode_name, registry_column=registry_column)

        if mode.kind == "categorical":
            unique_categories = sorted(pd.unique(values).tolist())
            palette = _palette_for(unique_categories)
            for category in unique_categories:
                fig.add_trace(
                    scatter_cls(
                        **_trace_kwargs(values == category), mode="markers", name=str(category),
                        marker=dict(color=palette[category], **marker_kwargs),
                    )
                )
        else:
            values = np.asarray(values, dtype=float)
            is_missing = np.isnan(values)
            color_values = values
            colorbar_kwargs: dict = dict(title=mode.label)
            if mode.log_scale:
                non_missing = values[~is_missing]
                # A NEGATIVE value is impossible for every log-scaled mode this registry has
                # (all are counts) - that is corrupt data and must stop the plot.
                if (non_missing < 0).any():
                    raise ValueError(
                        f"Color mode {mode_name!r} is log_scale but has negative values - "
                        f"cannot log-transform, and a negative count is not a legitimate value"
                    )
                # ZERO is legitimate and expected (30-09-26): lesion volume on the 2mm grid is
                # a nearest-neighbour resample of a 1mm mask, so a small lesion can come out at
                # 0 voxels without the mask being empty (docs/dev/metadata.md). log10(0) has no
                # position on the scale, which is exactly what "missing" means here - so it is
                # drawn neutral gray like any other missing value, not treated as corrupt.
                # Refusing the whole plot over it made the mode unusable for real cohorts.
                zero = ~is_missing & (values == 0)
                if zero.any():
                    logging.warning(
                        "color mode %r: %d subject(s) have volume 0 on this grid - no position "
                        "on a log scale, drawn as missing (gray)",
                        mode_name, int(zero.sum()),
                    )
                    is_missing = is_missing | zero
                color_values = np.where(is_missing, np.nan, np.log10(np.where(is_missing, 1.0, values)))
                # Recomputed after folding the zeros in: the decade ticks are built from the
                # values actually drawn on the scale, and a 0 left in here would make the
                # lower bound log10(0) = -inf.
                non_missing = values[~is_missing]
                if non_missing.size:
                    tickvals, ticktext = _log_decade_ticks(non_missing)
                    colorbar_kwargs = dict(title=mode.label, tickvals=tickvals, ticktext=ticktext)

            if is_missing.any():
                fig.add_trace(
                    scatter_cls(
                        **_trace_kwargs(is_missing), mode="markers", name="missing",
                        marker=dict(color=_NOISE_COLOR, **marker_kwargs),
                    )
                )
            # AUDIT_FINDINGS.md #65: this trace used to be added unconditionally - when
            # every value for this color mode is NaN (e.g. "nihss" on a dataset without
            # not enriched in the registry yet), it got x=[]/y=[] (nothing to plot) but
            # still showed up as a legend entry with mode.label and no visible marker,
            # confusing next to the real "missing" trace that already explains the gap.
            if (~is_missing).any():
                has_colorbar = True
                fig.add_trace(
                    scatter_cls(
                        **_trace_kwargs(~is_missing), mode="markers", name=mode.label,
                        # showlegend=False (02-10-26 feedback: "la legenda ... si sovrappone"):
                        # the colorbar already carries this trace's own name as its title, so a
                        # legend entry repeating it just duplicates that label - and Plotly's
                        # default legend position (top-right) sits exactly where the colorbar
                        # does, so the two visibly overlapped. The "missing"/"centroide" entries
                        # above/below still need the legend, so it is moved (not removed) below.
                        showlegend=False,
                        marker=dict(
                            color=color_values[~is_missing], colorscale="Viridis", colorbar=colorbar_kwargs,
                            **marker_kwargs,
                        ),
                    )
                )

    axis_style = dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=_GRID_BORDER)
    layout_kwargs = dict(
        title=dict(text=title, font=dict(size=18, family=_FONT_STACK, color=_TEXT_COLOR), x=0.02, xanchor="left"),
        template="simple_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT_STACK, color=_TEXT_COLOR),
        # Extra bottom margin only where the legend is relocated there (has_colorbar) - a plain
        # categorical/neutral mode keeps the default top-right legend, no colorbar to collide with.
        margin=dict(l=10, r=10, t=70, b=70 if has_colorbar else 10),
        height=680 if is_3d else 560,
    )
    if has_colorbar:
        # A continuous mode's colorbar sits at the plot's right edge, the same corner Plotly's
        # own default legend occupies - moved below the plot instead of overlapping it.
        layout_kwargs["legend"] = dict(orientation="h", xanchor="center", x=0.5, yanchor="top", y=-0.12)
    if is_3d:
        thin_axis = dict(showbackground=False, showgrid=False, zeroline=True, linewidth=1, showline=True)
        layout_kwargs["scene"] = dict(
            xaxis=dict(title=xlabel, **thin_axis),
            yaxis=dict(title=ylabel, **thin_axis),
            zaxis=dict(title=zlabel, **thin_axis),
            aspectmode="data",
        )
    else:
        layout_kwargs["xaxis"] = dict(title=xlabel, **axis_style)
        layout_kwargs["yaxis"] = dict(title=ylabel, **axis_style)

    fig.update_layout(**layout_kwargs)
    return fig


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


def _add_cluster_centroids_trace(figure: go.Figure, embedding: np.ndarray, metadata: pd.DataFrame) -> None:
    """Overlays a black-outlined circle + cluster_label text at each cluster's centroid
    (cluster_centroids_with_nearest_subject) on top of `figure`'s own point traces - same
    circled-centroid style as notebooks/post-results_analysis/clustering_evaluation.ipynb's
    plot_embedding_with_centroids (29-09-26, on request), added as an extra Plotly trace on
    the live interactive scatter instead of a separate static matplotlib plot.

    The trace starts hidden (visible="legendonly", 29-09-26 on request): the circles sit on top
    of the points and are a deliberate lookup ("where is cluster 3 centred"), not the default
    view. Clicking its legend entry turns it on.

    A no-op for a dim_reduction.py run (no cluster_label column) - mutates `figure` in place,
    nothing to return."""
    column = COLOR_MODES["cluster_label"].column
    if column not in metadata.columns:
        return
    centroids = cluster_centroids_with_nearest_subject(embedding, metadata)
    dim_columns = [c for c in centroids.columns if c.startswith("dim")]
    is_3d = len(dim_columns) == 3
    scatter_cls = go.Scatter3d if is_3d else go.Scatter
    coords_kwargs = dict(x=centroids[dim_columns[0]], y=centroids[dim_columns[1]])
    if is_3d:
        coords_kwargs["z"] = centroids[dim_columns[2]]
    figure.add_trace(
        scatter_cls(
            **coords_kwargs, mode="markers+text", name="centroide",
            text=[str(label) for label in centroids.index],
            textposition="middle center",
            textfont=dict(color="black", size=11, family=_FONT_STACK),
            marker=dict(size=18 if is_3d else 22, color="rgba(0,0,0,0)", line=dict(width=2, color="black")),
            hovertext=[
                f"cluster {label} - rappresentante: {row.nearest_subject_id}"
                for label, row in centroids.iterrows()
            ],
            hoverinfo="text",
            # Off until the reader asks for it from the legend (29-09-26, on request).
            # "legendonly" is the one way to do this that keeps the trace in the legend as a
            # dimmed, clickable entry - visible=False would drop it from the legend entirely,
            # leaving no way to turn it back on.
            visible="legendonly",
            showlegend=True,
        )
    )


def graph_content_for(
    run: ProductionRun, mode_name: str, volume_grid: str = DEFAULT_VOLUME_GRID
) -> html.P | dcc.Graph:
    """The graph-area.children Dash callback's actual body, pulled out as a plain function -
    directly unit-testable (no Dash callback-context wrapping to fight, see
    tests/unit/test_embedding_app.py) and kept as the single place this logic lives, not
    duplicated between a callback closure and a test harness.

    Returns an html.P status message (never raises) for a run that can't be displayed
    (UndisplayableRunError from load_run, or a ValueError from build_embedding_figure - e.g. a
    color mode's own persisted column missing from this particular run's metadata.csv), a
    dcc.Graph otherwise. Modebar hidden via the Graph's own config (Plotly's modebar is
    rendered inside the figure's own DOM subtree, unreachable by page-level CSS).

    config has no "responsive": True (2026-08-14, on request: the graph "si sminchia" on
    scroll) - Plotly's responsive mode attaches a ResizeObserver that recomputes the plot's
    size on every layout event, not just an actual window resize; scrolling a page that
    contains a WebGL scatter3d canvas is exactly the kind of layout event known to misfire
    that observer (a corrupted/squished redraw, not a crash - easy to miss in isolated
    testing, only visible once the page is tall enough to scroll). Sized instead by CSS
    (.graph-wrap/.graph-wrap > div, width: 100%) applied once at mount - the graph still
    fills the available width on load, it just doesn't keep re-measuring itself afterwards.
    """
    try:
        embedding, metadata = load_run(run)
    except UndisplayableRunError as exc:
        return html.P(str(exc), className="status-message")

    zlabel = f"{run.method} dim 3" if embedding.shape[1] == 3 else None
    try:
        figure = build_embedding_figure(
            embedding, metadata, mode_name,
            f"{run.method} dim 1", f"{run.method} dim 2", run_title(run, mode_name),
            volume_grid=volume_grid,
            zlabel=zlabel,
        )
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    _add_cluster_centroids_trace(figure, embedding, metadata)

    # modeBarButtons (not modeBarButtonsToRemove): an explicit whitelist survives 2D<->3D
    # unchanged (Plotly's default button set differs between them - a removal-list would need
    # its own 3D variant to actually hide everything else), and "toImage" is the one save
    # affordance this app offers per plot (01-09-26, on request) - still hidden until hover
    # (Plotly's own default displayModeBar="hover"), so the minimal look from 14-08-26 holds.
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}
    return dcc.Graph(id="embedding-graph", figure=figure, config=config, style={"width": "100%"})


# nilearn.plotting.view_img's own default (600px) reads narrow inside this page's 1100px-wide
# .page container, next to the 34px anatomy-panel headings (01-09-26 feedback) - both anatomy
# viewers pass this explicitly instead. Height scales with it automatically (nilearn's own
# _json_view_size keeps the sagittal/coronal/axial aspect ratio, never distorted by width_view).
_ANATOMY_VIEWER_WIDTH = 900

# Display cmap/threshold shared by every ortho/interactive SDC disconnectome view (single-subject
# viewer, per-cluster mean map, and their own static-PNG downloads - never the glass-brain
# download, which has its own separate threshold/alpha below). cmap="magma" - briefly changed to
# "nipy_spectral" on 29-09-26 (to match Thiebaut de Schotten et al. 2020's own Fig. 1 colormap),
# reverted the same day ("non mi piace la palette arcobaleno") in favor of a sequential,
# single-hue-family colormap - plasma/viridis were also compared on real data
# (tmp/anatomy_rendering/130_cluster_disconnection_*, 131_disconnectome_single_*) before settling
# back on magma, already used elsewhere in this app (glass-brain download below, cluster overlap's
# sibling "hot"). threshold=0.02 (was the near-zero epsilon 1e-6, kept across both colormap
# choices) - at 1e-6, near-zero disconnection-probability noise renders in the colormap's own
# near-black floor color, scattered as ugly black speckle across the brain on both the
# single-subject map and, worse, the per-cluster mean map ("troppo nero" feedback, 29-09-26) -
# confirmed clean at 0.02 against a real 975-subject cluster mean and a real single-subject map
# (tmp/anatomy_rendering/110_cluster_disconnection_*, 120_disconnectome_single_*). Distinct
# problem from the glass-brain streaking below (that one is specific to projecting/summing along
# the full volume depth), but the same fix shape - raise the near-zero epsilon to a real floor.
_DISCONNECTOME_CMAP = "magma"
_DISCONNECTOME_DISPLAY_THRESHOLD = 0.02


def _masked_for_view_colorbar(img: nib.Nifti1Image, threshold: float) -> nib.Nifti1Image:
    """A copy of img with every voxel inside [-threshold, threshold] zeroed - lets a view_img
    call receive a near-zero epsilon (1e-6, this app's usual "any non-zero voxel" convention)
    instead of a real, wide threshold like _DISCONNECTOME_DISPLAY_THRESHOLD.

    view_img's own interactive colorbar paints every value inside [-threshold, threshold] flat
    opaque gray (nilearn.plotting._engine_utils.threshold_cmap, hardcoded gray (0.5, 0.5, 0.5,
    1.0), not configurable through view_img's public API) - invisible for a near-zero epsilon
    (a sliver against vmax) but a visibly wide gray band at the low end of the scale for a real
    threshold like 0.02 (30-09-26 feedback: "perché c'è del grigio nella scala"). Zeroing the
    data ourselves the same way nilearn's own thresholding would (html_stat_map._threshold_data:
    values inside [-threshold, threshold] become 0) and passing 1e-6 to view_img instead hides
    the exact same voxels without the artifact. Callers keep passing the real, unmasked image to
    every other consumer (PNG download, cached return value) - this masked copy exists only for
    what view_img itself renders."""
    data = img.get_fdata()
    masked = np.where(np.abs(data) > threshold, data, 0.0).astype(data.dtype)
    return nib.Nifti1Image(masked, img.affine)

# --- Per-cluster disconnection map: two readings of the same subjects (30-09-26) ------------
# The mean map and the lesion overlap map are the SAME estimator (voxelwise mean over the
# cluster) on different data, but that makes them mean different things: averaging BINARY
# masks yields a fraction of subjects, averaging CONTINUOUS probabilities does not. A mean of
# 0.6 could be "every subject at 0.6" or "60% at 1.0 and 40% at 0.0" - indistinguishable - so
# it cannot be read as "60% of the cluster is disconnected here", which is exactly what the
# lesion overlap map does say. "percent" restores that reading by binarizing each subject
# first and then counting, making the two maps identical by construction.
DISCONNECTION_PERCENT_MODE = "percent"
DISCONNECTION_MEAN_MODE = "mean"
DEFAULT_DISCONNECTION_MAP_MODE = DISCONNECTION_PERCENT_MODE
DISCONNECTION_MAP_MODE_LABELS = {
    DISCONNECTION_PERCENT_MODE: "% soggetti disconnessi",
    DISCONNECTION_MEAN_MODE: "probabilità media",
}
# The per-subject probability a voxel must EXCEED for that subject to count as disconnected
# there (build_overlap_map binarizes with a strict >, same as for a lesion mask).
# 0.5 is "more likely disconnected than not" - the same more-likely-than-not cutoff the
# lesion-mask literature uses to binarize a smoothed probabilistic mask (e.g. Keator et al.
# 2021, knowledge/nemesis_related/). Declared here as ONE named constant rather than exposed
# as a slider: a threshold the reader can sweep invites fishing for the value that makes a
# cluster look separable, which is not what this panel is for. Changing it is a deliberate,
# reviewable edit - and it must be stated wherever the map is shown, since the map's meaning
# depends on it entirely.
DISCONNECTION_PROBABILITY_THRESHOLD = 0.5

# Display-only threshold/alpha for the SDC glass-brain static download (29-09-26, on request) -
# deliberately not the same threshold the SDC ortho/interactive views use above (see
# _static_glass_brain_png_bytes' own docstring for why a glass-brain projection needs its own,
# higher threshold). Picked by comparing 1e-6/0.05/0.1/0.2 against real subject data
# (tmp/anatomy_rendering/90_disconnectome_glass_lyrz_magma_alpha90_thr*.png) and confirmed by the
# user - 0.1 hides the near-zero noise streaks without cutting into the real signal.
_DISCONNECTOME_GLASS_BRAIN_THRESHOLD = 0.1
_DISCONNECTOME_GLASS_BRAIN_ALPHA = 0.9


def cluster_options(metadata: pd.DataFrame) -> list[int]:
    """Sorted distinct cluster_label values in `metadata` - only meaningful for a clustering.py
    run (dim_reduction.py runs never have this column, see ProductionRun.pipeline). HDBSCAN's
    noise label (-1) is included like any other value - the same treatment
    COLOR_MODES["cluster_label"] already gives it, never hidden."""
    column = COLOR_MODES["cluster_label"].column
    return sorted(int(value) for value in pd.unique(metadata[column]))


def cluster_centroids_with_nearest_subject(embedding: np.ndarray, metadata: pd.DataFrame) -> pd.DataFrame:
    """Per-cluster centroid (mean of that cluster's own embedding coordinates) plus the real
    subject_id closest to it in that same embedding space (Euclidean distance) - promoted
    29-09-26 from notebooks/post-results_analysis/clustering_evaluation.ipynb's own
    cluster_centroids/nearest_subject_to_centroid (same algorithm, adapted to read `metadata`
    directly instead of a notebook-local extended_runs dict). A centroid is a mean point, not
    a real subject - this is the closest real one, used both to overlay circled centroids on
    the embedding scatter (graph_content_for) and to pick which real subject's anatomy the
    "Soggetto rappresentativo del cluster" panel shows (representative_subject_content_for).

    Distance is computed in the reduced embedding space (the same dim0/dim1[/dim2] coordinates
    plotted), not the original pre-reduction feature space - consistent with where the
    centroid circle itself is drawn (see docs/dev/anatomical_maps.md).

    Returns one row per cluster_label, indexed by it, with columns dim0..dim{n-1} (centroid
    coordinates), nearest_subject_id, distance_to_centroid.

    Raises ValueError if `metadata` has no cluster_label column (only a clustering.py run has
    one - dim_reduction.py runs never reach this) or if `embedding`/`metadata` have mismatched
    row counts (would silently misalign points to the wrong subject_id otherwise)."""
    column = COLOR_MODES["cluster_label"].column
    if column not in metadata.columns:
        raise ValueError(f"metadata has no {column!r} column - centroids only apply to a clustering.py run")
    if len(embedding) != len(metadata):
        raise ValueError(f"embedding has {len(embedding)} rows but metadata has {len(metadata)} - can't align them")

    dim_columns = [f"dim{i}" for i in range(embedding.shape[1])]
    coords = pd.DataFrame(embedding, columns=dim_columns)
    coords[column] = metadata[column].to_numpy()
    coords["subject_id"] = metadata["subject_id"].to_numpy()

    rows = []
    for cluster_label, group in coords.groupby(column):
        centroid = group[dim_columns].mean()
        distances = np.linalg.norm(group[dim_columns].to_numpy() - centroid.to_numpy(), axis=1)
        nearest_position = distances.argmin()
        rows.append({
            column: cluster_label,
            **centroid.to_dict(),
            "nearest_subject_id": group["subject_id"].iloc[nearest_position],
            "distance_to_centroid": float(distances[nearest_position]),
        })
    return pd.DataFrame(rows).set_index(column)


def _resolve_subject_dataset(metadata: pd.DataFrame, subject_id: str) -> str:
    matches = metadata.loc[metadata["subject_id"] == subject_id, "dataset"]
    if matches.empty:
        raise ValueError(f"{subject_id!r} not found in this run's metadata")
    return matches.iloc[0]


def _style_nilearn_html(html_page: str) -> str:
    """nilearn's view_img HTML has no <style> block at all (verified against a real generated
    page, 01-09-26) - the only ordinary, CSS-reachable text it has (the "Opacity" label/slider)
    renders in the browser's plain default font instead of this app's own (feedback: "Opacity
    deve rispettare lo stesso font"). Injected once, right before </head> (present exactly once
    in every nilearn-generated page), reused for both the embedded iframe and the "Salva HTML"
    download - both should look the same."""
    style_block = f"<style>body {{ font-family: {_FONT_STACK}; color: {_TEXT_COLOR}; font-size: 14px; }}</style>"
    return html_page.replace("</head>", f"{style_block}\n</head>", 1)


def _static_glass_brain_png_bytes(
    stat_map_img: str | nib.Nifti1Image, *, threshold: float, cmap: str, colorbar: bool, alpha: float = 1.0
) -> bytes:
    """Glass-brain counterpart to _static_png_bytes' plot_stat_map rendering (29-09-26, on
    request) - a single transparent-brain projection (nilearn.plotting.plot_glass_brain,
    display_mode="lyrz") instead of 3 flat ortho slices, for each anatomy panel's own "Salva PNG
    (glass brain)" button. black_bg=False/plot_abs=False mirror _static_png_bytes' own
    white-background, non-negative-data choices.

    Unlike plot_stat_map, plot_glass_brain projects (sums) along the full depth of the volume -
    a near-zero display threshold (e.g. the 1e-6 epsilon _build_subject_disconnectome_view uses
    to show "any real disconnection probability") makes faint background noise visible as thin
    dark streaks across the whole silhouette, confirmed on real disconnectome data (tmp/
    anatomy_rendering/, 29-09-26). Each caller passes a threshold picked for its own data -
    _DISCONNECTOME_GLASS_BRAIN_THRESHOLD for the SDC panels, lesion_cfg.binarize_threshold for
    the lesion panel (already clean at that threshold - a binary mask has no near-zero noise to
    hide) - never a shared default that would silently reintroduce the streaking for one caller
    while being wrong for the other."""
    display = nilearn_plotting.plot_glass_brain(
        stat_map_img, threshold=threshold, cmap=cmap, colorbar=colorbar, black_bg=False,
        display_mode="lyrz", plot_abs=False, alpha=alpha,
    )
    buffer = io.BytesIO()
    display.savefig(buffer, dpi=150)
    display.close()
    buffer.seek(0)
    return buffer.getvalue()


def _static_png_bytes(stat_map_img: str | nib.Nifti1Image, *, threshold: float, cmap: str, colorbar: bool) -> bytes:
    """Non-interactive PNG counterpart to the "Salva HTML" download (11-09-26, on request) -
    view_img's own HTML page has no static-image export, so this renders the same stat_map_img
    a second time via nilearn.plotting.plot_stat_map instead, matching the interactive view's own
    bg_img/threshold/cmap/colorbar choices (see _build_subject_lesion_view/
    _build_cluster_overlap_view) rather than an independently-styled second rendering.
    symmetric_cbar=False mirrors view_img's own symmetric_cmap=False: both maps this app ever
    passes here are non-negative (a binary lesion mask, or a 0-100% overlap percentage), so
    nilearn's "auto" guess is unnecessary to rely on. No bg_img passed - unlike view_img,
    plot_stat_map's own `bg_img` default already *is* an MNI152 template object, not a string
    shortcut (view_img's own "MNI152" string raises `ValueError: File not found` if passed here,
    confirmed against the installed nilearn version rather than assumed). Matplotlib's Agg
    backend is already active process-wide by the time this runs (src.analysis.plotting, imported
    by this module, sets it at import time) - no figure ever reaches a GUI backend."""
    display = nilearn_plotting.plot_stat_map(
        stat_map_img, black_bg=False, threshold=threshold, cmap=cmap, colorbar=colorbar, title=None,
        symmetric_cbar=False,
    )
    buffer = io.BytesIO()
    display.savefig(buffer, dpi=150)
    display.close()
    buffer.seek(0)
    return buffer.getvalue()


def _anatomy_viewer(
    view: StatMapView, heading: str, caption: str, warning: str | None = None, note: str | None = None
) -> html.Div:
    """Shared layout for both anatomy panels: a heading + a one-line color-legend caption, both
    ordinary HTML we render ourselves (never nilearn's own `title`/colorbar text - see
    _build_subject_lesion_view's docstring for why), above the iframe sized to the view's own
    exact pixel dimensions (view.width/height) and centered, instead of stretching a fixed-height
    iframe to the panel's full width and leaving the rest as dead space (01-09-26 feedback: the
    scatter's own .graph-wrap already established this "centered, content-sized" pattern).

    warning (29-09-26, on request): an optional extra line, rendered between the caption and the
    iframe, for a cluster-level map built from fewer subjects than the cluster actually has (see
    overlap_map_content_for/disconnection_map_content_for) - omitted (no 3rd `<p>` at all, not an
    empty one) when every requested subject resolved, so a panel with nothing to report keeps
    exactly its original 2-paragraph shape.

    key=heading on the Iframe (01-09-26 bug fix - "se cambio il cluster non mi si cambia la
    mappa"): a browser doesn't reliably re-navigate an <iframe> just because its own `srcDoc`
    attribute value changed in place - React/Dash's default diffing patches the attribute on the
    *same* DOM node, which several browsers then leave showing their stale, already-rendered
    content. `key` forces Dash's front-end to unmount+remount the node instead of patching it in
    place whenever `heading` changes - and `heading` (a subject_id or "Cluster N (n=...)") is
    already guaranteed to change whenever the actual content does, so no separate id is needed.
    """
    # note (30-09-26): a second, quieter line inside the same paragraph - for the part of a
    # caption that explains WHY the map is built this way rather than what the colour means.
    # One paragraph, not two, so the two lines stay visually bound to each other.
    # Kept a plain string when there is no note, so a panel that never had one (both
    # single-subject viewers, the lesion overlap map) keeps exactly its previous shape.
    caption_children = caption if note is None else [caption, html.Span(note, className="anatomy-note")]
    children = [
        html.H3(heading, className="anatomy-subject-title"),
        html.P(caption_children, className="anatomy-caption"),
    ]
    if warning is not None:
        children.append(_warning_box(warning))
    children.append(
        html.Div(
            html.Iframe(
                key=heading, srcDoc=_style_nilearn_html(view.html),
                style={"width": f"{view.width}px", "height": f"{view.height}px"},
            ),
            className="anatomy-viewer-wrap",
        )
    )
    return html.Div(children)


def _build_subject_lesion_view(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, lesion_cfg: LesionViewerConfig
) -> tuple[StatMapView, str]:
    """Returns (view, dataset) - dataset is needed by the caller to build its own subject-name
    heading, since title=None below (nilearn draws `title` straight onto its <canvas>, with no
    width check or line-wrapping at all - a moderately long subject_id silently overflows past
    the panel edge with no way to fix it via CSS; see _anatomy_viewer). colorbar=False: this is
    a binary lesion mask (voxel is lesioned or not) - a 0/1 colorbar conveys no real gradient
    information, unlike the cluster overlap map below.

    Raises ValueError (never silently) if subject_id/dataset/lesion file can't be resolved -
    see resolve_lesion_paths. threshold reuses lesion_cfg.binarize_threshold rather than a
    second hardcoded 0.5, so the viewer shows exactly the same binarization the source feature
    matrix used, not an independently-chosen display threshold.

    cmap="autumn" (briefly changed to "magma" on 29-09-26, reverted same day - magma's top color
    for a binary mask is a near-white pale yellow, "troppo pallido" against the white background
    on real data; autumn's is a solid bright yellow, confirmed against several alternatives -
    hot/inferno/plasma equally or more washed out, Reds/YlOrRd a legible but duller dark red -
    tmp/anatomy_rendering/100_lesion_ortho_*.png). See _download_lesion_png for the matching
    static-PNG cmap and _download_lesion_glass_png for the glass-brain download's own (same)
    "autumn" choice."""
    dataset = _resolve_subject_dataset(metadata, subject_id)
    lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob)
    view = nilearn_plotting.view_img(
        str(lesion_paths[subject_id]), bg_img="MNI152", black_bg=False, threshold=lesion_cfg.binarize_threshold,
        cmap="autumn", symmetric_cmap=False, title=None, colorbar=False, width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, dataset


def lesion_viewer_content_for(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, lesion_cfg: LesionViewerConfig
) -> html.Div | html.P:
    """graph_content_for's own never-raises contract, extended to this panel: an html.P status
    message on any resolution failure (subject not in this run, dataset unresolvable, lesion
    file missing on disk) instead of crashing the click callback - a single bad subject must
    not take down the whole app (lesson #21's isolation principle, applied per-click here)."""
    try:
        view, dataset = _build_subject_lesion_view(run, subject_id, metadata, lesion_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(view, f"{subject_id} ({dataset})", "Zona colorata = Lesione")


def _build_cluster_overlap_view(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig,
    mask_store: BinaryMaskStore | None = None,
) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
    """Returns (view, n_subjects, percentage_img, missing_subjects) - n_subjects is needed by
    the caller to build its own heading (title=None here, same reasoning as
    _build_subject_lesion_view); percentage_img (the same image the view itself renders) is
    returned alongside it (11-09-26) so the "Salva PNG" download can reuse it rather than paying
    build_overlap_map's per-subject load+resample cost a second time. colorbar stays on (unlike
    the subject viewer): the overlap percentage is a genuinely continuous, informative value.

    missing_subjects (29-09-26, on request) lists cluster members whose lesion mask isn't
    resolvable on disk right now (resolve_available_lesion_paths) - excluded from the map
    instead of failing the whole panel over them (a real, already-documented local data gap,
    e.g. after a lesion-mask swap left some subjects' raw files no longer retrieved on this
    machine - .claude/history/data_changelog.md 23-09-26). n_subjects counts only the resolved
    subjects actually used - the same denominator build_overlap_map's percentage is computed
    against, never the cluster's full nominal size.

    Raises ValueError if cluster_label has no subjects in this run's metadata, or if EVERY one
    of them is unresolvable (see resolve_available_lesion_paths/build_overlap_map) - a map with
    zero subjects behind it is not a legitimate partial result. threshold is a near-zero epsilon
    (not lesion_cfg.binarize_threshold, which binarizes each individual subject's mask before
    counting - see build_overlap_map) so every voxel with any real overlap (>0%) is shown, not
    just voxels above some display-only cutoff."""
    column = COLOR_MODES["cluster_label"].column
    cluster_metadata = metadata.loc[metadata[column] == cluster_label]
    if cluster_metadata.empty:
        raise ValueError(f"no subjects with {column}={cluster_label!r} in this run's metadata")
    dataset_by_subject = dict(zip(cluster_metadata["subject_id"], cluster_metadata["dataset"]))
    lesion_paths, missing_subjects = resolve_available_lesion_paths(
        list(dataset_by_subject), dataset_by_subject, lesion_cfg.data_root, lesion_cfg.lesion_glob
    )
    _count_img, percentage_img = build_overlap_map(
        lesion_paths, lesion_cfg.reference_img, lesion_cfg.binarize_threshold, lesion_cfg.resample_interpolation,
        store=mask_store,
    )
    view = nilearn_plotting.view_img(
        percentage_img, bg_img="MNI152", black_bg=False, threshold=1e-6, cmap="hot", symmetric_cmap=False, title=None,
        width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, len(lesion_paths), percentage_img, missing_subjects


def _warning_box(message: str, detail: str | None = None) -> html.Div:
    """The shared boxed callout for every "partial result" warning on the page (29-09-26
    feedback: "warning tipo questo devono essere renderizzati un po' meglio").

    An uppercase vivid label carries the alarm; the message itself stays BLACK body text. That
    split is deliberate: coloring the whole block would make the information read as decoration
    and cost it contrast, while the label alone is enough to say "this is not routine caption
    text" - which is exactly how the previous thin amber line failed.

    detail: the long, non-prose tail (a list of subject ids), set apart from the sentence so the
    sentence stays readable when the tail runs to a dozen ids."""
    children: list = [html.Span("Attenzione", className="warning-label"), message]
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
        f"{len(missing_subjects)} soggetti del cluster esclusi dalla mappa (dato non trovato su disco): "
        f"{', '.join(sorted(missing_subjects))}"
    )


def _unregistered_subjects_warning(unregistered: list[str]) -> html.Div | None:
    """Sibling of _missing_subjects_warning for cluster_description_content_for (29-09-26) - a
    DIFFERENT gap, deliberately worded so the two are never confused: _missing_subjects_warning
    is about a subject whose lesion/disconnectome FILE isn't on disk (excluded from that map),
    this one is about a subject with no row in assets/metadata/participants.csv at all (still
    counted in the panel's own n/total, just with no value for any variable). None when every
    subject of the cluster resolved."""
    if not unregistered:
        return None
    return _warning_box(
        f"{len(unregistered)} soggetti di questo cluster non hanno una riga nel registro "
        f"(assets/metadata/participants.csv). Contano nel totale di ogni variabile, ma non "
        f"portano alcun valore.",
        detail=", ".join(unregistered),
    )


def overlap_map_content_for(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig,
    build_view: Callable[
        [ProductionRun, pd.DataFrame, int, LesionViewerConfig], tuple[StatMapView, int, nib.Nifti1Image, list[str]]
    ] = _build_cluster_overlap_view,
) -> html.Div | html.P:
    """Same never-raises contract as lesion_viewer_content_for - a cluster with zero resolvable
    subjects shows a status message in the panel, not a crashed callback. A cluster with *some*
    (not all) unresolvable subjects instead renders the map over its available subjects, with an
    extra warning line naming which ones were excluded (_missing_subjects_warning) - never a
    silent partial result.

    build_view defaults to the always-fresh _build_cluster_overlap_view (what every test calls
    this with) - build_app passes its own cached wrapper instead (01-09-26 perf fix: measured
    ~40ms/subject, dominating the whole panel's response time for a real several-hundred-subject
    cluster - see anatomical_maps.build_overlap_map's own docstring), so switching back to an
    already-viewed cluster in the running app is instant, without this function itself needing
    to know anything about caching."""
    try:
        view, n_subjects, _percentage_img, missing_subjects = build_view(run, metadata, cluster_label, lesion_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(
        view, f"Cluster {cluster_label} (n={n_subjects})",
        "Colore = % di soggetti del cluster con lesione in quel voxel (0-100%)",
        warning=_missing_subjects_warning(missing_subjects),
    )


def _build_subject_disconnectome_view(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, sdc_cfg: SdcViewerConfig
) -> tuple[StatMapView, str]:
    """Returns (view, dataset) - same reasoning as _build_subject_lesion_view (single-source
    title, resolved via resolve_lesion_paths against sdc_cfg's own disconnectome_glob rather
    than lesion_cfg's lesion_glob). colorbar=True (unlike the lesion viewer): disconnectome
    values are a genuinely continuous [0, 1] probability per voxel, not a binary mask - a
    colorbar conveys real information here. Masks with _DISCONNECTOME_DISPLAY_THRESHOLD before
    viewing, not a binarize threshold (disconnectome values are never binarized, see
    src.features.sdc's module docstring) - see that constant's own docstring for why it isn't a
    near-zero epsilon, and _masked_for_view_colorbar's for why view_img itself gets 1e-6 instead.

    Raises ValueError (never silently) if subject_id/dataset/disconnectome file can't be
    resolved - see resolve_lesion_paths."""
    dataset = _resolve_subject_dataset(metadata, subject_id)
    disconnectome_paths = resolve_lesion_paths(
        [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
    )
    disconnectome_img = nib.load(str(disconnectome_paths[subject_id]))
    view = nilearn_plotting.view_img(
        _masked_for_view_colorbar(disconnectome_img, _DISCONNECTOME_DISPLAY_THRESHOLD), bg_img="MNI152",
        black_bg=False, threshold=1e-6, cmap=_DISCONNECTOME_CMAP, symmetric_cmap=False,
        title=None, colorbar=True, width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, dataset


def disconnectome_viewer_content_for(
    run: ProductionRun, subject_id: str, metadata: pd.DataFrame, sdc_cfg: SdcViewerConfig
) -> html.Div | html.P:
    """lesion_viewer_content_for's own never-raises contract, for the SDC disconnectome panel -
    an html.P status message on any resolution failure instead of crashing the click callback."""
    try:
        view, dataset = _build_subject_disconnectome_view(run, subject_id, metadata, sdc_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(view, f"{subject_id} ({dataset})", "Colore = probabilità di disconnessione per voxel (0-1)")


def _build_cluster_disconnection_view(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, sdc_cfg: SdcViewerConfig,
    map_mode: str = DEFAULT_DISCONNECTION_MAP_MODE, mask_store: BinaryMaskStore | None = None,
) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
    """Returns (view, n_subjects, mean_img, missing_subjects) - same reasoning as
    _build_cluster_overlap_view (including missing_subjects - see its own docstring), but the
    continuous-data counterpart: build_mean_map's voxelwise mean instead of build_overlap_map's
    binarized count/percentage (there is no "binarize each subject then count" step for a value
    that's already a continuous probability, see build_mean_map's own docstring). mean_img is
    returned alongside the view (same reasoning as percentage_img above) so the "Salva PNG"
    download can reuse it rather than paying build_mean_map's per-subject load+resample cost a
    second time.

    map_mode (30-09-26, on request):

    - "percent" (default) binarizes each subject's disconnectome at
      DISCONNECTION_PROBABILITY_THRESHOLD and counts, via the SAME build_overlap_map the lesion
      panel uses - so the two maps become the same quantity, "% of the cluster's subjects
      affected in this voxel", and are directly comparable. Displayed with the same near-zero
      display threshold as the lesion overlap map, for the same reason.
    - "mean" is the previous behaviour, build_mean_map's voxelwise mean of the continuous
      probabilities. It uses the full information instead of discarding it at a cutoff, so it
      still sees widespread sub-threshold disconnection that "percent" shows as empty - but it
      is NOT a proportion of subjects (see the constants above).

    Raises ValueError for an unknown map_mode, if cluster_label has no subjects in this run's
    metadata, or if EVERY one of them is unresolvable (see resolve_available_lesion_paths)."""
    if map_mode not in DISCONNECTION_MAP_MODE_LABELS:
        raise ValueError(
            f"unknown disconnection map mode {map_mode!r} - known: {sorted(DISCONNECTION_MAP_MODE_LABELS)}"
        )
    column = COLOR_MODES["cluster_label"].column
    cluster_metadata = metadata.loc[metadata[column] == cluster_label]
    if cluster_metadata.empty:
        raise ValueError(f"no subjects with {column}={cluster_label!r} in this run's metadata")
    dataset_by_subject = dict(zip(cluster_metadata["subject_id"], cluster_metadata["dataset"]))
    disconnectome_paths, missing_subjects = resolve_available_lesion_paths(
        list(dataset_by_subject), dataset_by_subject, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
    )
    if map_mode == DISCONNECTION_PERCENT_MODE:
        _count_img, img = build_overlap_map(
            disconnectome_paths, sdc_cfg.reference_img,
            DISCONNECTION_PROBABILITY_THRESHOLD, sdc_cfg.resample_interpolation, store=mask_store,
        )
        display_threshold = 1e-6  # any non-zero voxel, exactly as the lesion overlap map
        view_source = img
    else:
        img = build_mean_map(disconnectome_paths, sdc_cfg.reference_img, sdc_cfg.resample_interpolation)
        # threshold=1e-6 below, not _DISCONNECTOME_DISPLAY_THRESHOLD directly - see
        # _masked_for_view_colorbar's own docstring (avoids view_img's gray sub-threshold band).
        view_source = _masked_for_view_colorbar(img, _DISCONNECTOME_DISPLAY_THRESHOLD)
        display_threshold = 1e-6
    # The colormap stays magma in both modes: it encodes WHICH DATA this is (disconnection,
    # not lesion), a cue the app uses everywhere, while the scale is what now matches the
    # lesion map in "percent".
    view = nilearn_plotting.view_img(
        view_source, bg_img="MNI152", black_bg=False, threshold=display_threshold,
        cmap=_DISCONNECTOME_CMAP, symmetric_cmap=False, title=None, width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, len(disconnectome_paths), img, missing_subjects


def disconnection_map_content_for(
    run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, sdc_cfg: SdcViewerConfig,
    build_view: Callable[
        ..., tuple[StatMapView, int, nib.Nifti1Image, list[str]]
    ] = _build_cluster_disconnection_view,
    map_mode: str = DEFAULT_DISCONNECTION_MAP_MODE,
) -> html.Div | html.P:
    """Same never-raises contract as overlap_map_content_for (including the same skip-and-warn
    behavior for a cluster with *some* unresolvable subjects, _missing_subjects_warning) - a
    cluster with zero resolvable subjects shows a status message in the panel, not a crashed
    callback.

    build_view defaults to the always-fresh _build_cluster_disconnection_view (what every test
    calls this with) - build_app passes its own cached wrapper instead, same perf reasoning as
    overlap_map_content_for's own cache (per-subject load+resample dominates the panel's response
    time for a real several-hundred-subject cluster)."""
    try:
        view, n_subjects, _img, missing_subjects = build_view(run, metadata, cluster_label, sdc_cfg, map_mode)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    # The caption states the threshold in "percent" mode: the map's whole meaning depends on
    # it, so it must never be read without it.
    if map_mode == DISCONNECTION_PERCENT_MODE:
        caption = "Colore = % di soggetti del cluster disconnessi in quel voxel (0-100%)."
        note = (
            f"Un soggetto conta come disconnesso in un voxel se lì la sua probabilità di "
            f"disconnessione supera {DISCONNECTION_PROBABILITY_THRESHOLD:g} - stessa soglia e "
            f"stessa logica dell'overlap map lesionale, quindi i due pannelli sono "
            f"confrontabili direttamente."
        )
    else:
        caption = "Colore = probabilità media di disconnessione del cluster in quel voxel (0-1)."
        note = "La media dice quanto forte è la disconnessione."
    return _anatomy_viewer(
        view, f"Cluster {cluster_label} (n={n_subjects})", caption,
        warning=_missing_subjects_warning(missing_subjects), note=note,
    )


def representative_subject_content_for(
    run: ProductionRun, embedding: np.ndarray, metadata: pd.DataFrame, cluster_label: int,
    lesion_cfg: LesionViewerConfig, sdc_cfg: SdcViewerConfig,
) -> html.Div | html.P:
    """Panel "Soggetto rappresentativo del cluster" (29-09-26, on request), shown after the
    two per-cluster map panels: the real subject closest to `cluster_label`'s centroid in the
    embedding space (cluster_centroids_with_nearest_subject) - a centroid is a mean point, not
    a real subject, this shows the closest real one instead. Dispatches to the lesion or SDC
    disconnectome viewer by `run.modality` (mirroring notebooks/post-results_analysis/
    clustering_evaluation.ipynb's plot_representative_map, which dispatches by parsing
    `input_path` instead - this app already has modality as a first-class ProductionRun field,
    no string-matching needed).

    Same never-raises contract as every other *_content_for function here: an empty/
    unresolvable cluster, or a representative subject whose file can't be resolved on disk,
    renders an html.P status message instead of crashing the callback."""
    try:
        centroids = cluster_centroids_with_nearest_subject(embedding, metadata)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    if cluster_label not in centroids.index:
        column = COLOR_MODES["cluster_label"].column
        return html.P(f"no subjects with {column}={cluster_label!r} in this run's metadata", className="status-message")
    subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
    distance = centroids.loc[cluster_label, "distance_to_centroid"]

    try:
        if run.modality == "lesion":
            view, dataset = _build_subject_lesion_view(run, subject_id, metadata, lesion_cfg)
        else:
            view, dataset = _build_subject_disconnectome_view(run, subject_id, metadata, sdc_cfg)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")
    return _anatomy_viewer(
        view, f"Cluster {cluster_label} — rappresentante: {subject_id} ({dataset})",
        f"Soggetto reale più vicino al centroide del cluster nello spazio embedding (distanza={distance:.3f})",
    )


def _format_number(value: float, decimals: int) -> str:
    """Italian number formatting: '.' groups thousands, ',' is the decimal separator -
    5265.4 -> '5.265,4' (29-09-26 feedback: "i numeri non sono ben scritti, non si capisce
    molto bene"). The whole app is in Italian, so English-formatted numbers ('5 265.4') read
    as a foreign convention exactly where the reader is scanning fastest.

    Done by swapping Python's own grouped format rather than with `locale`: locale is process
    global, depends on what happens to be installed on the machine, and would silently change
    every other number this process formats."""
    grouped = f"{value:,.{decimals}f}"          # 5,265.4
    return grouped.translate(str.maketrans({",": ".", ".": ","}))


def _format_continuous_cell(summary: dict, variable: ClusterDescriptionVariable) -> html.Td:
    """`media ± ds` at this variable's own declared precision, plus the coverage note where the
    variable does not cover the whole cluster.

    No in-cell bar (29-09-26, on request: "non voglio quelle righe colorate nella tabella, mi
    confondono la lettura"). The cross-cluster comparison is carried by the numbers alone -
    which is what the Italian formatting and the larger type are for - while the figure above
    stays the visual read.

    An empty cell is "—", never "nan ± nan" and never a blank that could read as a rendering gap.
    """
    if summary["n_available"] == 0:
        return html.Td([html.Div("—", className="stat-value stat-empty")])

    decimals = variable.decimals
    mean = _format_number(summary["mean"], decimals)
    # std is None for a single subject: a standard deviation of one value does not exist, which
    # is a different statement from "0".
    spread = None if summary["std"] is None else f"± {_format_number(summary['std'], decimals)}"

    value = [mean] if spread is None else [mean, " ", html.Span(spread, className="stat-sd")]
    return html.Td(
        [html.Div(value, className="stat-value"), _coverage_note(summary)],
        # Hover detail only - median/min/max enhance, they never gate: the headline number and
        # the coverage are both readable without hovering.
        title=(
            f"mediana {_format_number(summary['median'], decimals)} · "
            f"min {_format_number(summary['min'], decimals)} · "
            f"max {_format_number(summary['max'], decimals)}"
        ),
    )


def _format_categorical_cell(summary: dict) -> html.Td:
    """Counts per category, sorted by name so a category keeps the same position in every row
    and the column can be read downwards. No proportion bar (29-09-26, on request) - the
    figure's own bar chart above carries that."""
    if summary["n_available"] == 0:
        return html.Td([html.Div("—", className="stat-value stat-empty")])

    label = " · ".join(f"{c} {summary['counts'][c]}" for c in sorted(summary["counts"]))
    return html.Td([html.Div(label, className="stat-value"), _coverage_note(summary)])


def _coverage_note(summary: dict) -> html.Span | None:
    """The n_available/n_total line, shown ONLY where the variable is actually incomplete.

    It used to sit under every cell: 25 near-identical fractions competing with the values they
    were annotating, which is how a coverage note stops being read at all. Printed only when it
    says something, it goes back to being a signal. Full coverage is not silently assumed
    either - the caption under the table states the rule."""
    if summary["n_available"] == summary["n_total"]:
        return None
    return html.Span(f"{summary['n_available']}/{summary['n_total']}", className="stats-n")


def _clusters_comparison_table(stats: list[ClusterStats], selected_cluster: int) -> html.Div:
    """The cross-cluster comparison table rendered under the selected cluster's own figure
    (29-09-26, on request) - one row per cluster, one column per CLUSTER_DESCRIPTION_VARIABLES
    entry, so a variable is read down a column across clusters rather than by flipping the
    dropdown between them.

    A table rather than a second figure: the ask was for the numbers themselves, and a 5-8
    cluster x 5 variable grid is past the point where a reader can hold that many color classes
    apart. It doubles as the table view the figure's own fills require for accessibility. In-cell
    bars were tried and removed on request (29-09-26) - they competed with the digits rather
    than supporting them.

    Every cluster of the run is listed, including the selected one (highlighted) and hdbscan's
    noise bucket (-1, labelled as such rather than shown as a cluster named "-1")."""
    palette = _palette_for_labels([stat.cluster_label for stat in stats])
    # Plain headers: the per-variable colored underline was dropped on request (29-09-26). The
    # figure above still colors each variable and the in-cell bars carry the same hue, so the
    # column/panel tie survives without a second colored rule competing with the header text.
    header = html.Tr([
        html.Th("Cluster"), html.Th("Soggetti"),
        *[html.Th(variable.label) for variable in CLUSTER_DESCRIPTION_VARIABLES],
    ])

    rows = []
    for stat in stats:
        name = "Rumore" if stat.cluster_label == -1 else f"Cluster {stat.cluster_label}"
        size = [html.Div(_format_number(stat.n_total, 0), className="stat-value")]
        if stat.n_unregistered:
            size.append(html.Span(f"{stat.n_unregistered} fuori registro", className="stats-n"))
        cells = [
            _format_categorical_cell(stat.summaries[v.name]) if v.kind == "categorical"
            else _format_continuous_cell(stat.summaries[v.name], v)
            for v in CLUSTER_DESCRIPTION_VARIABLES
        ]
        rows.append(
            html.Tr(
                [
                    html.Td(html.Div([
                        html.Span(className="stats-swatch", style={"background": palette[stat.cluster_label]}),
                        name,
                    ], className="stats-cluster")),
                    html.Td(size),
                    *cells,
                ],
                className="selected" if stat.cluster_label == selected_cluster else "",
            )
        )

    return html.Div(
        [
            html.Table([html.Thead(header), html.Tbody(rows)], className="stats-table"),
            html.P(
                [
                    html.B("Valori: "),
                    "media ± deviazione standard.",
                    html.Br(),
                    html.B("Sesso: "),
                    "conteggio per categoria.",
                    html.Br(),
                    html.B("Numero sotto il valore: "),
                    "soggetti che hanno quella variabile, sul totale del cluster. Compare solo "
                    "dove la variabile non copre tutto il cluster.",
                    html.Br(),
                    html.B("Mouse su una cella: "),
                    "mediana, minimo e massimo.",
                ],
                className="stats-caption",
            ),
        ],
        className="stats-table-wrap",
    )


def cluster_description_content_for(metadata: pd.DataFrame, cluster_label: int) -> dcc.Graph | html.Div | html.P:
    """Panel "Descrizione del cluster" (29-09-26, on request), shown after the two frequency-map
    panels - age/sex/education/NIHSS/lesion-volume composition of `cluster_label`'s subjects
    (src.analysis.cluster_description.cluster_composition/build_cluster_description_figure),
    every one of them read from assets/metadata/participants.csv (see that module's own
    docstring for why, not a run's own metadata.csv). Visible for any clustering.py run
    regardless of modality - unlike the two frequency-map panels, this doesn't need a
    disconnectome/lesion mask file at all, only the subject registry.

    Same never-raises contract as every other *_content_for function here: an empty cluster
    renders an html.P status message instead of crashing the callback. A cluster whose subjects
    are only *partly* in the registry is not an error at all (29-09-26, on request): the figure
    is built over everyone, with the unregistered subjects counted in each variable's n_total
    but contributing no value, and an _unregistered_subjects_warning line naming them is
    rendered above it - the same "partial result, never silent" shape the two anatomy panels
    already use for a subject whose mask file is missing. Rendered as a plain dcc.Graph (Plotly's own "toImage"
    camera icon is this panel's only export, same as the main embedding scatter) - no Salva
    HTML/PNG buttons, those exist only for the nilearn iframe-based anatomy panels above, which
    have no built-in export of their own."""
    try:
        composition, unregistered = cluster_composition(metadata, cluster_label)
        stats = clusters_comparison_stats(metadata)
    except ValueError as exc:
        return html.P(str(exc), className="status-message")

    palette = _palette_for_labels([stat.cluster_label for stat in stats])
    figure = build_cluster_description_figure(composition, cluster_label, color=palette.get(cluster_label))
    config = {"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False}

    children: list = []
    warning = _unregistered_subjects_warning(unregistered)
    if warning is not None:
        children.append(warning)
    children.append(dcc.Graph(figure=figure, config=config, style={"width": "100%"}))
    children.append(_clusters_comparison_table(stats, cluster_label))
    return html.Div(children)


def _color_button_label(mode_name: str) -> str:
    # Raw mode.label, not .capitalize()'d - "NIHSS (severity)".capitalize() would produce
    # "Nihss (severity)" (str.capitalize lowercases every character but the first), the same
    # trap the notebook prototype's _panel_title left uncorrected; sidestepped here by not
    # reformatting the label's casing at all, same as compose_embedding_plot_title's own
    
    return "neutro" if mode_name == NEUTRAL_MODE else COLOR_MODES[mode_name].label


_LESION_PLACEHOLDER = html.P("Clicca un punto nell'embedding per vedere la lesione.", className="status-message")
_DISCONNECTOME_PLACEHOLDER = html.P(
    "Clicca un punto nell'embedding per vedere il disconnettoma.", className="status-message"
)


def build_app(
    runs: list[ProductionRun],
    lesion_cfg: LesionViewerConfig,
    sdc_cfg: SdcViewerConfig,
    clustering_params_file: str | Path,
    preload: bool = False,
) -> Dash:
    """Builds the Dash app: a run picker (dcc.Dropdown, one entry per discovered production
    run) plus a color-mode button group (COLOR_MODE_ORDER, styled as a chip row via CSS, not
    a second dropdown - the design brief this was built against, 14-08-26, asked for "bottoni"
    explicitly) driving one dcc.Graph. No client-side state beyond which button is active
    (dcc.Store) - the embedding/figure itself is rebuilt server-side on every run/color change
    (load_run + build_embedding_figure), never cached: at this cohort size (~1150 subjects,
    matrix.npy a few hundred KB at most) a fresh disk read + figure build is fast enough that
    a cache would add complexity for no measurable benefit. Same philosophy holds for the
    single-subject lesion viewer added 01-09-26 (one small NIfTI, also fast enough uncached) -
    but *not* for the per-cluster overlap map (same panel-family, very different cost: measured
    ~40ms/subject to load+resample, dominating the whole panel's response time for a real
    several-hundred-subject cluster), which this app does cache in-process
    (cluster_view_cache/_cached_cluster_overlap_view below, 01-09-26 perf fix). The two SDC
    disconnectome panels added 29-09-26 (single-subject viewer, per-cluster mean-disconnection
    map) mirror this exact split - single-subject uncached, per-cluster cached
    (disconnection_view_cache/_cached_cluster_disconnection_view) - same per-subject cost shape,
    just averaging instead of counting (build_mean_map vs build_overlap_map).

    suppress_callback_exceptions=True (01-09-26): the anatomy panels' own callbacks reference
    component ids ("embedding-graph") that only exist once graph_content_for actually renders a
    Graph into graph-area's children - never part of the static app.layout tree itself - the
    standard Dash idiom for wiring a callback to a dynamically-created component.

    clustering_params_file (01-09-26): config/registry/params_clustering.json (or an equivalent
    test fixture) - the picker's own "Parametri" step (tag_param_options/runs_matching) reads
    each clustering method's registered tag_param list from it, so a run can be narrowed by its
    own n_clusters/linkage/etc., not just by the upstream embedding's metric/n_components.

    Raises ValueError if `runs` is empty - an app with a run picker offering nothing to pick
    is a broken starting state, not a legitimate empty one (unlike
    discover_production_runs itself, which legitimately can return an empty list for a fresh
    checkout - the CLI entry point, src.pipeline.embedding_app, is what decides that's worth
    failing loudly on before ever calling this).
    """
    if not runs:
        raise ValueError("The app needs at least one production run - none were discovered, nothing to display")

    runs_by_key = {run.key: run for run in runs}

    # Per-subject "voxels above threshold" memos (30-09-26), shared by every run and cluster of
    # this app instance - see BinaryMaskStore. Plain closure variables, like the view caches.
    lesion_store = BinaryMaskStore(lesion_cfg.reference_img, lesion_cfg.resample_interpolation, lesion_cfg.binarize_threshold)
    disconnection_store = BinaryMaskStore(
        sdc_cfg.reference_img, sdc_cfg.resample_interpolation, DISCONNECTION_PROBABILITY_THRESHOLD
    )
    default_modality = modality_options(runs)[0]

    # Cluster-overlap-map cache (01-09-26 perf fix) - process-lifetime, in-memory, scoped to
    # this one app instance (a plain closure variable, not a module-level global -
    # code_standards.md §1 "no stato globale"). Keyed by (run.key, cluster_label): switching
    # back to an already-viewed cluster (or re-viewing it via the "Salva HTML" button after
    # already looking at it) is then instant instead of re-loading+resampling every subject's
    # real NIfTI mask from disk again. A failed build (ValueError - an unresolvable subject) is
    # never cached, so a transient/fixable problem can be retried on the next click.
    cluster_view_cache: dict[tuple[str, int], tuple[StatMapView, int, nib.Nifti1Image, list[str]]] = {}

    def _cached_cluster_overlap_view(
        run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, lesion_cfg: LesionViewerConfig
    ) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
        cache_key = (run.key, cluster_label)
        if cache_key not in cluster_view_cache:
            cluster_view_cache[cache_key] = _build_cluster_overlap_view(
                run, metadata, cluster_label, lesion_cfg, mask_store=lesion_store
            )
        return cluster_view_cache[cache_key]

    # Same caching reasoning as cluster_view_cache above, for the SDC per-cluster mean
    # disconnection map (29-09-26) - a separate dict/cache_key namespace since a (run.key,
    # cluster_label) pair for a clustering run could in principle collide across the two if
    # they shared one dict (a clustering run's own key doesn't encode which of the two anatomy
    # families produced a given cache entry).
    disconnection_view_cache: dict[
        tuple[str, int, str], tuple[StatMapView, int, nib.Nifti1Image, list[str]]
    ] = {}

    def _cached_cluster_disconnection_view(
        run: ProductionRun, metadata: pd.DataFrame, cluster_label: int, sdc_cfg: SdcViewerConfig,
        map_mode: str = DEFAULT_DISCONNECTION_MAP_MODE,
    ) -> tuple[StatMapView, int, nib.Nifti1Image, list[str]]:
        # map_mode is part of the key (30-09-26): the same cluster now has two different maps,
        # and keying on (run, cluster) alone would serve whichever was built first for both.
        cache_key = (run.key, cluster_label, map_mode)
        if cache_key not in disconnection_view_cache:
            disconnection_view_cache[cache_key] = _build_cluster_disconnection_view(
                run, metadata, cluster_label, sdc_cfg, map_mode, mask_store=disconnection_store
            )
        return disconnection_view_cache[cache_key]

    app = Dash(__name__, suppress_callback_exceptions=True)
    app.index_string = _INDEX_STRING

    color_buttons = [
        html.Button(
            _color_button_label(mode),
            id={"type": "color-mode-btn", "mode": mode},
            n_clicks=0,
            className="active" if mode == NEUTRAL_MODE else "",
        )
        for mode in COLOR_MODE_ORDER
    ]

    # Resolved once at build time, not per callback: which volume grids the registry holds is
    # a property of participants.csv, which this process does not rewrite while running.
    grids = available_volume_grids()
    volume_grid_buttons = [
        html.Button(
            grid,
            id={"type": "volume-grid-btn", "grid": grid},
            n_clicks=0,
            className="active" if grid == DEFAULT_VOLUME_GRID else "",
        )
        for grid in grids
    ]

    # 6-step decision order, left to right (2026-08-14, on request - replaces the previous
    # single flat "every run from every method mixed together" dropdown, then extended with
    # explicit Metrica/Componenti steps rather than leaving them buried in the Run label's own
    # free-text run_name): Dato (modality) -> Pipeline -> Metodo -> Metrica -> Componenti ->
    # Run (scoped by every step before it). Pipeline became a real choice, not a fixed label,
    # 15-08-26 (docs/dev/clustering_migration_plan.md §3) once this app started discovering
    # clustering.py runs too - Metrica/Componenti still show up for a clustering-pipeline run
    # (uniform layout across both pipelines), just resolved to their one NO_METRIC/
    # NO_N_COMPONENTS sentinel option each (see metric_options/n_components_options), since
    # clustering method params have no metric/n_components axis to offer. Steps 2-6's own
    # options are populated by the cascading callbacks below, empty at layout-build time.
    def _picker_field(label: str, dropdown_id: str) -> html.Div:
        return html.Div(
            className="picker-field",
            children=[html.Label(label, className="picker-label"), dcc.Dropdown(id=dropdown_id, clearable=False)],
        )

    app.layout = html.Div(
        className="page",
        children=[
            html.H1("Embedding Explorer", className="page-title"),
            html.P(
                "Esplorazione interattiva dei run di produzione — scegli un run e una colorazione.",
                className="page-subtitle",
            ),
            html.Div(
                className="controls",
                children=[
                    # Two rows (2026-08-14, on request): Dato/Pipeline/Metodo (the "which
                    # pipeline output" question) above, Metrica/Componenti/Run (the "which
                    # exact combination that pipeline produced" question) below.
                    html.Div(
                        className="picker-row",
                        children=[
                            html.Div(
                                className="picker-field",
                                children=[
                                    html.Label("Dato", className="picker-label"),
                                    dcc.Dropdown(
                                        id="modality-picker",
                                        options=[{"label": m, "value": m} for m in modality_options(runs)],
                                        value=default_modality,
                                        clearable=False,
                                    ),
                                ],
                            ),
                            _picker_field("Pipeline", "pipeline-picker"),
                            _picker_field("Metodo", "method-picker"),
                        ],
                    ),
                    html.Div(
                        className="picker-row",
                        children=[
                            _picker_field("Metrica", "metric-picker"),
                            _picker_field("Componenti", "n-components-picker"),
                            # "Parametri" (01-09-26, on request): real clustering runs vary by
                            # more than just the upstream embedding's metric/n_components - each
                            # method's own hyperparameters (n_clusters/linkage for agglomerative,
                            # etc.) do too. NO_METRIC-only for dim_reduction (see
                            # tag_param_options) - kept in this same row so the picker still
                            # reads as one uniform 4-step sequence across both pipelines.
                            _picker_field("Parametri", "tag-params-picker"),
                            _picker_field("Run", "run-picker"),
                        ],
                    ),
                    html.Div(color_buttons, className="color-buttons"),
                    # Only meaningful while "volume" is the active colour mode, so it is
                    # hidden otherwise (a grid chooser floating under an unrelated mode
                    # reads as a second, broken colour row). Built from the grids the
                    # registry can actually serve today - one button now, two as soon as
                    # enrich_metadata.py writes lesion_volume_voxels_1mm.
                    html.Div(
                        [
                            html.Span("Griglia volume", className="grid-row-label"),
                            *volume_grid_buttons,
                        ],
                        id="volume-grid-row",
                        className="color-buttons grid-row",
                        style={"display": "none"},
                    ),
                ],
            ),
            dcc.Store(id="selected-color-mode", data=NEUTRAL_MODE),
            dcc.Store(id="selected-volume-grid", data=DEFAULT_VOLUME_GRID),
            dcc.Store(id="selected-disconnection-mode", data=DEFAULT_DISCONNECTION_MAP_MODE),
            html.H2("Embedding Visualization", className="section-heading"),
            html.Div(id="graph-area", className="graph-wrap"),
            # Always-visible (per design decision, 01-09-26 - not an appear-on-click popup):
            # placeholder until a point is clicked, subject's nilearn viewer afterward.
            html.Div(
                className="anatomy-panel",
                children=[
                    html.H2("Anatomia lesionale", className="section-heading"),
                    html.Div(id="lesion-viewer-content", children=_LESION_PLACEHOLDER),
                    # Single source of truth for "which subject is actually visible in the panel
                    # above right now" (01-09-26 bug fix) - set atomically with
                    # lesion-viewer-content.children by the same callback below, never derived
                    # separately from embedding-graph.clickData again downstream. clickData is a
                    # client-side prop that does NOT reset just because a *different* dcc.Graph
                    # instance with the same id gets mounted in its place (switching run-picker
                    # replaces graph-area's children, but React/Dash patches the same-id node
                    # rather than remounting it) - the Save buttons below used to read clickData
                    # directly via State, so after a run change they kept silently offering a
                    # download for the *previous* run's clicked subject even though this panel
                    # had already reset to the placeholder, with no visible link between what was
                    # shown and what got downloaded. None whenever the panel shows the placeholder
                    # or an unresolvable-subject error, so a stale/absent selection can never be
                    # downloaded regardless of what embedding-graph.clickData still holds.
                    dcc.Store(id="lesion-viewer-subject", data=None),
                    html.Div(
                        className="save-btn-row",
                        children=[
                            html.Button("Salva HTML", id="lesion-save-btn", n_clicks=0, className="save-btn"),
                            html.Button("Salva PNG", id="lesion-png-btn", n_clicks=0, className="save-btn"),
                            html.Button(
                                "Salva PNG (glass brain)", id="lesion-glass-png-btn", n_clicks=0, className="save-btn"
                            ),
                        ],
                    ),
                    dcc.Download(id="lesion-download"),
                    dcc.Download(id="lesion-png-download"),
                    dcc.Download(id="lesion-glass-png-download"),
                ],
            ),
            # Hidden by default (style toggled by _update_disconnectome_panel_visibility below) -
            # only a modality="sdc" run (its subjects have a disconnectome-map.nii.gz on disk,
            # see SDC_DISCONNECTOME_GLOB) ever shows this panel; a "lesion" run has no such file,
            # showing it there would be either empty or a crash on every single click (01-09-26 -
            # 29-09-26 SDC extension, on request: "come per le lesioni ... plottare anche la
            # frequency map con la disconnessione").
            html.Div(
                id="disconnectome-panel",
                className="anatomy-panel",
                style={"display": "none"},
                children=[
                    html.H2("Disconnessione (SDC)", className="section-heading"),
                    html.Div(id="disconnectome-viewer-content", children=_DISCONNECTOME_PLACEHOLDER),
                    # Same clickData-persistence fix as lesion-viewer-subject above, same reasoning.
                    dcc.Store(id="disconnectome-viewer-subject", data=None),
                    html.Div(
                        className="save-btn-row",
                        children=[
                            html.Button("Salva HTML", id="disconnectome-save-btn", n_clicks=0, className="save-btn"),
                            html.Button("Salva PNG", id="disconnectome-png-btn", n_clicks=0, className="save-btn"),
                            html.Button(
                                "Salva PNG (glass brain)", id="disconnectome-glass-png-btn", n_clicks=0,
                                className="save-btn",
                            ),
                        ],
                    ),
                    dcc.Download(id="disconnectome-download"),
                    dcc.Download(id="disconnectome-png-download"),
                    dcc.Download(id="disconnectome-glass-png-download"),
                ],
            ),
            # Hidden by default (style toggled by _update_cluster_picker below) - only a
            # 30-09-26, on request: everything below is per-CLUSTER, everything above is
            # per-subject/whole-run. The break is marked with a heavier rule and its own
            # title, and the cluster chooser is lifted out of the first panel it happened to
            # live in (cluster-map-panel) to sit here, centred, as the section's first act -
            # it scopes every panel that follows, so it belongs to the section, not to one of
            # its panels. Callbacks still resolve it by component id, so nothing else moves.
            html.Div(
                id="clustering-section",
                className="section-divider",
                style={"display": "none"},
                children=[
                    html.H2("Clustering Explorer", className="section-title"),
                    html.P(
                        "Le sezioni qui sotto descrivono un cluster alla volta. Scegli quale.",
                        className="section-intro",
                    ),
                    html.Div(
                        className="cluster-chooser",
                        children=[
                            html.Label("Cluster", className="picker-label"),
                            dcc.Dropdown(id="cluster-picker", clearable=False),
                        ],
                    ),
                ],
            ),
            # clustering.py run (metadata has cluster_label) ever shows this panel.
            html.Div(
                id="cluster-map-panel",
                className="anatomy-panel",
                style={"display": "none"},
                children=[
                    html.H2("Overlap map per cluster", className="section-heading"),
                    html.Div(id="cluster-map-content"),
                    html.Div(
                        className="save-btn-row",
                        children=[
                            html.Button("Salva HTML", id="cluster-save-btn", n_clicks=0, className="save-btn"),
                            html.Button("Salva PNG", id="cluster-png-btn", n_clicks=0, className="save-btn"),
                        ],
                    ),
                    dcc.Download(id="cluster-download"),
                    dcc.Download(id="cluster-png-download"),
                ],
            ),
            # Hidden by default (style toggled by _update_disconnection_map_panel_visibility
            # below) - needs BOTH a modality="sdc" run (a disconnectome file to average) AND a
            # clustering.py run (a cluster_label to group by), unlike disconnectome-panel above
            # which only needs the former. Reuses cluster-picker itself (no separate "Cluster"
            # dropdown here) - the same clustering run has exactly one set of clusters regardless
            # of which map family (lesion overlap vs disconnection mean) is being viewed, so a
            # second dropdown would only ever show the identical options as the first.
            html.Div(
                id="disconnection-map-panel",
                className="anatomy-panel",
                style={"display": "none"},
                children=[
                    html.H2("Disconnessione per cluster", className="section-heading"),
                    # 30-09-26: two readings of the same subjects, explicitly chosen rather
                    # than one silently assumed - see DISCONNECTION_PERCENT_MODE's comment.
                    html.Div(
                        [
                            html.Span("Mappa", className="grid-row-label"),
                            *[
                                html.Button(
                                    DISCONNECTION_MAP_MODE_LABELS[mode],
                                    id={"type": "disconnection-mode-btn", "mode": mode},
                                    n_clicks=0,
                                    className="active" if mode == DEFAULT_DISCONNECTION_MAP_MODE else "",
                                )
                                for mode in DISCONNECTION_MAP_MODE_LABELS
                            ],
                        ],
                        className="color-buttons grid-row",
                    ),
                    html.Div(id="disconnection-map-content"),
                    html.Div(
                        className="save-btn-row",
                        children=[
                            html.Button("Salva HTML", id="disconnection-save-btn", n_clicks=0, className="save-btn"),
                            html.Button("Salva PNG", id="disconnection-png-btn", n_clicks=0, className="save-btn"),
                        ],
                    ),
                    dcc.Download(id="disconnection-download"),
                    dcc.Download(id="disconnection-png-download"),
                ],
            ),
            # Hidden by default (style toggled by _update_cluster_picker below, same condition
            # as cluster-map-panel/disconnection-map-panel - run.pipeline == "clustering") -
            # 29-09-26, on request: shown *after* the two per-cluster map panels above (moved
            # there the same day, from its first position above them), driven by the *same*
            # "Cluster" dropdown they already share (cluster-picker itself is defined inside
            # cluster-map-panel above - Dash resolves callbacks by component id regardless of
            # where in the tree that id physically lives).
            html.Div(
                id="representative-subject-panel",
                className="anatomy-panel",
                style={"display": "none"},
                children=[
                    html.H2("Soggetto rappresentativo del cluster", className="section-heading"),
                    html.Div(id="representative-subject-content"),
                    html.Div(
                        className="save-btn-row",
                        children=[
                            html.Button("Salva HTML", id="representative-save-btn", n_clicks=0, className="save-btn"),
                            html.Button("Salva PNG", id="representative-png-btn", n_clicks=0, className="save-btn"),
                        ],
                    ),
                    dcc.Download(id="representative-download"),
                    dcc.Download(id="representative-png-download"),
                ],
            ),
            # Hidden by default (style toggled by _update_cluster_picker below, same condition
            # as cluster-map-panel - run.pipeline == "clustering") - 29-09-26, on request: last
            # of the per-cluster panels, driven by the same shared cluster-picker. Visible for
            # any clustering.py run regardless of modality (age/sex/education/NIHSS/lesion
            # volume come from the subject registry, not from a disconnectome/lesion file).
            html.Div(
                id="cluster-description-panel",
                className="anatomy-panel",
                style={"display": "none"},
                children=[
                    html.H2("Descrizione del cluster", className="section-heading"),
                    html.Div(id="cluster-description-content"),
                ],
            ),
        ],
    )

    @app.callback(
        Output("pipeline-picker", "options"),
        Output("pipeline-picker", "value"),
        Input("modality-picker", "value"),
    )
    def _update_pipeline_picker(modality: str):
        pipelines = pipeline_options(runs, modality)
        return [{"label": p, "value": p} for p in pipelines], pipelines[0]

    @app.callback(
        Output("method-picker", "options"),
        Output("method-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
    )
    def _update_method_picker(modality: str, pipeline: str | None):
        if pipeline is None:
            raise PreventUpdate
        methods = method_options(runs, modality, pipeline)
        return [{"label": m, "value": m} for m in methods], methods[0]

    @app.callback(
        Output("metric-picker", "options"),
        Output("metric-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
    )
    def _update_metric_picker(modality: str, pipeline: str | None, method: str | None):
        if pipeline is None or method is None:
            raise PreventUpdate
        metrics = metric_options(runs, modality, pipeline, method)
        return [{"label": m, "value": m} for m in metrics], metrics[0]

    @app.callback(
        Output("n-components-picker", "options"),
        Output("n-components-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
        Input("metric-picker", "value"),
    )
    def _update_n_components_picker(modality: str, pipeline: str | None, method: str | None, metric: str | None):
        if pipeline is None or method is None or metric is None:
            raise PreventUpdate
        n_components_values = n_components_options(runs, modality, pipeline, method, metric)
        options = [{"label": _n_components_option_label(n), "value": n} for n in n_components_values]
        return options, n_components_values[0]

    @app.callback(
        Output("tag-params-picker", "options"),
        Output("tag-params-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
        Input("metric-picker", "value"),
        Input("n-components-picker", "value"),
    )
    def _update_tag_params_picker(
        modality: str, pipeline: str | None, method: str | None, metric: str | None, n_components: int | None
    ):
        if pipeline is None or method is None or metric is None or n_components is None:
            raise PreventUpdate
        labels = tag_param_options(runs, modality, pipeline, method, metric, n_components, clustering_params_file)
        return [{"label": label, "value": label} for label in labels], labels[0]

    @app.callback(
        Output("run-picker", "options"),
        Output("run-picker", "value"),
        Input("modality-picker", "value"),
        Input("pipeline-picker", "value"),
        Input("method-picker", "value"),
        Input("metric-picker", "value"),
        Input("n-components-picker", "value"),
        Input("tag-params-picker", "value"),
    )
    def _update_run_picker(
        modality: str, pipeline: str | None, method: str | None, metric: str | None, n_components: int | None,
        tag_params_label: str | None,
    ):
        if pipeline is None or method is None or metric is None or n_components is None or tag_params_label is None:
            # An upstream picker just changed and hasn't propagated its new value here yet -
            # each cascading callback is a separate step in Dash's dependency graph, not a
            # synchronous call chain.
            raise PreventUpdate
        matching = runs_matching(runs, modality, pipeline, method, metric, n_components, tag_params_label, clustering_params_file)
        options = [{"label": run.run_name, "value": run.key} for run in matching]
        default_run_key = matching[-1].key  # most recent by _run_chronological_key
        return options, default_run_key

    @app.callback(
        Output("selected-color-mode", "data"),
        Input({"type": "color-mode-btn", "mode": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _select_color_mode(_all_n_clicks: list[int]) -> str:
        if ctx.triggered_id is None:
            raise PreventUpdate
        return ctx.triggered_id["mode"]

    @app.callback(
        Output({"type": "color-mode-btn", "mode": ALL}, "className"),
        Input("selected-color-mode", "data"),
        State({"type": "color-mode-btn", "mode": ALL}, "id"),
    )
    def _highlight_active_button(selected_mode: str, ids: list[dict]) -> list[str]:
        return ["active" if button_id["mode"] == selected_mode else "" for button_id in ids]

    @app.callback(
        Output("selected-volume-grid", "data"),
        Input({"type": "volume-grid-btn", "grid": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _select_volume_grid(_all_n_clicks: list[int]) -> str:
        if ctx.triggered_id is None:
            raise PreventUpdate
        return ctx.triggered_id["grid"]

    @app.callback(
        Output({"type": "volume-grid-btn", "grid": ALL}, "className"),
        Input("selected-volume-grid", "data"),
        State({"type": "volume-grid-btn", "grid": ALL}, "id"),
    )
    def _highlight_active_grid(selected_grid: str, ids: list[dict]) -> list[str]:
        return ["active" if button_id["grid"] == selected_grid else "" for button_id in ids]

    @app.callback(
        Output("volume-grid-row", "style"),
        Input("selected-color-mode", "data"),
    )
    def _toggle_volume_grid_row(selected_mode: str) -> dict:
        return {} if selected_mode == VOLUME_MODE else {"display": "none"}

    @app.callback(
        Output("graph-area", "children"),
        Input("run-picker", "value"),
        Input("selected-color-mode", "data"),
        Input("selected-volume-grid", "data"),
    )
    def _update_graph(run_key: str | None, selected_mode: str, volume_grid: str):
        if run_key is None:
            raise PreventUpdate
        return graph_content_for(runs_by_key[run_key], selected_mode, volume_grid)

    @app.callback(
        Output("lesion-viewer-content", "children"),
        Output("lesion-viewer-subject", "data"),
        Input("embedding-graph", "clickData"),
        Input("run-picker", "value"),
    )
    def _update_lesion_viewer(click_data: dict | None, run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        # A run change resets to the placeholder (ctx.triggered_id tells the two Inputs apart) -
        # a subject clicked on a previous run must not linger once the picker moves on. The
        # Store resets to None in lockstep, so the Save buttons below (reading it, not
        # embedding-graph.clickData directly) can never offer a stale cross-run download - see
        # the Store's own docstring in app.layout for the clickData-persistence bug this fixes.
        if ctx.triggered_id == "run-picker" or click_data is None:
            return _LESION_PLACEHOLDER, None
        subject_id = click_data["points"][0].get("text")
        if subject_id is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        return lesion_viewer_content_for(run, subject_id, run_metadata(run), lesion_cfg), subject_id

    @app.callback(
        Output("lesion-download", "data"),
        Input("lesion-save-btn", "n_clicks"),
        State("lesion-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_lesion_html(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            view, _dataset = _build_subject_lesion_view(run, subject_id, run_metadata(run), lesion_cfg)
        except ValueError:
            # The visible panel already reports this via lesion_viewer_content_for - the save
            # button simply has nothing to offer, not a second error surface.
            raise PreventUpdate
        return dcc.send_string(_style_nilearn_html(view.html), filename=f"{subject_id}_lesion_3d.html")

    @app.callback(
        Output("lesion-png-download", "data"),
        Input("lesion-png-btn", "n_clicks"),
        State("lesion-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_lesion_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            # Resolves the subject's real lesion mask path directly - no need to build the
            # interactive view_img (_build_subject_lesion_view) just to render a static PNG.
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob)
        except ValueError:
            # Same never-raises-into-the-callback contract as _download_lesion_html: the visible
            # panel already reports this, the save button simply has nothing to offer.
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            str(lesion_paths[subject_id]), threshold=lesion_cfg.binarize_threshold, cmap="autumn", colorbar=False,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_lesion.png")

    @app.callback(
        Output("lesion-glass-png-download", "data"),
        Input("lesion-glass-png-btn", "n_clicks"),
        State("lesion-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_lesion_glass_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            lesion_paths = resolve_lesion_paths([subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob)
        except ValueError:
            # Same never-raises-into-the-callback contract as _download_lesion_png.
            raise PreventUpdate
        # cmap="autumn" - same choice as _build_subject_lesion_view's own ortho view (see its
        # docstring): a binary mask has no gradient to show, autumn's solid bright yellow reads
        # clearly on both the ortho and this glass-brain projection.
        png_bytes = _static_glass_brain_png_bytes(
            str(lesion_paths[subject_id]), threshold=lesion_cfg.binarize_threshold, cmap="autumn", colorbar=False,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_lesion_glass.png")

    @app.callback(
        Output("disconnectome-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_disconnectome_panel_visibility(run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        return {} if runs_by_key[run_key].modality == "sdc" else {"display": "none"}

    @app.callback(
        Output("disconnectome-viewer-content", "children"),
        Output("disconnectome-viewer-subject", "data"),
        Input("embedding-graph", "clickData"),
        Input("run-picker", "value"),
    )
    def _update_disconnectome_viewer(click_data: dict | None, run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        # Same run-change reset as _update_lesion_viewer, plus a modality gate: a "lesion" run's
        # subjects don't have a disconnectome-map.nii.gz to resolve at all (this panel stays
        # hidden for them via _update_disconnectome_panel_visibility, but its own content must
        # still reset rather than linger/attempt a doomed resolution on every click).
        if run.modality != "sdc" or ctx.triggered_id == "run-picker" or click_data is None:
            return _DISCONNECTOME_PLACEHOLDER, None
        subject_id = click_data["points"][0].get("text")
        if subject_id is None:
            raise PreventUpdate
        return disconnectome_viewer_content_for(run, subject_id, run_metadata(run), sdc_cfg), subject_id

    @app.callback(
        Output("disconnectome-download", "data"),
        Input("disconnectome-save-btn", "n_clicks"),
        State("disconnectome-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnectome_html(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            view, _dataset = _build_subject_disconnectome_view(run, subject_id, run_metadata(run), sdc_cfg)
        except ValueError:
            raise PreventUpdate
        return dcc.send_string(_style_nilearn_html(view.html), filename=f"{subject_id}_disconnectome.html")

    @app.callback(
        Output("disconnectome-png-download", "data"),
        Input("disconnectome-png-btn", "n_clicks"),
        State("disconnectome-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnectome_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            disconnectome_paths = resolve_lesion_paths(
                [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
            )
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            str(disconnectome_paths[subject_id]), threshold=_DISCONNECTOME_DISPLAY_THRESHOLD,
            cmap=_DISCONNECTOME_CMAP, colorbar=True,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_disconnectome.png")

    @app.callback(
        Output("disconnectome-glass-png-download", "data"),
        Input("disconnectome-glass-png-btn", "n_clicks"),
        State("disconnectome-viewer-subject", "data"),
        State("run-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnectome_glass_png(_n_clicks: int, subject_id: str | None, run_key: str | None):
        if subject_id is None or run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        try:
            dataset = _resolve_subject_dataset(run_metadata(run), subject_id)
            disconnectome_paths = resolve_lesion_paths(
                [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
            )
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_glass_brain_png_bytes(
            str(disconnectome_paths[subject_id]), threshold=_DISCONNECTOME_GLASS_BRAIN_THRESHOLD, cmap="magma",
            colorbar=True, alpha=_DISCONNECTOME_GLASS_BRAIN_ALPHA,
        )
        return dcc.send_bytes(png_bytes, filename=f"{subject_id}_disconnectome_glass.png")

    @app.callback(
        Output("cluster-picker", "options"),
        Output("cluster-picker", "value"),
        Output("clustering-section", "style"),
        Output("cluster-map-panel", "style"),
        Output("representative-subject-panel", "style"),
        Output("cluster-description-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_cluster_picker(run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        hidden = {"display": "none"}
        if run.pipeline != "clustering":
            return [], None, hidden, hidden, hidden, hidden
        clusters = cluster_options(run_metadata(run))
        return (
            [{"label": str(cluster_label), "value": cluster_label} for cluster_label in clusters],
            clusters[0], {}, {}, {}, {},
        )

    @app.callback(
        Output("cluster-map-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
    )
    def _update_cluster_map(run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        return overlap_map_content_for(run, run_metadata(run), cluster_label, lesion_cfg, build_view=_cached_cluster_overlap_view)

    @app.callback(
        Output("representative-subject-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
    )
    def _update_representative_subject(run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            embedding, metadata = load_run(run)
        except UndisplayableRunError as exc:
            # Same never-raises-into-the-callback contract as every other *_content_for
            # panel - the main graph above already shows this same error for this run.
            return html.P(str(exc), className="status-message")
        return representative_subject_content_for(run, embedding, metadata, cluster_label, lesion_cfg, sdc_cfg)

    @app.callback(
        Output("cluster-description-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
    )
    def _update_cluster_description(run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        return cluster_description_content_for(run_metadata(run), cluster_label)

    @app.callback(
        Output("representative-download", "data"),
        Input("representative-save-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_representative_html(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            embedding, metadata = load_run(run)
            centroids = cluster_centroids_with_nearest_subject(embedding, metadata)
            subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
            if run.modality == "lesion":
                view, _dataset = _build_subject_lesion_view(run, subject_id, metadata, lesion_cfg)
            else:
                view, _dataset = _build_subject_disconnectome_view(run, subject_id, metadata, sdc_cfg)
        except (ValueError, KeyError):
            # Same never-raises-into-the-callback contract as _download_lesion_html: the
            # visible panel already reports this, the save button simply has nothing to offer.
            # ValueError also covers UndisplayableRunError (its own subclass) from load_run.
            raise PreventUpdate
        return dcc.send_string(
            _style_nilearn_html(view.html), filename=f"cluster_{cluster_label}_representative_{subject_id}.html"
        )

    @app.callback(
        Output("representative-png-download", "data"),
        Input("representative-png-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_representative_png(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            embedding, metadata = load_run(run)
            centroids = cluster_centroids_with_nearest_subject(embedding, metadata)
            subject_id = centroids.loc[cluster_label, "nearest_subject_id"]
            dataset = _resolve_subject_dataset(metadata, subject_id)
            if run.modality == "lesion":
                lesion_paths = resolve_lesion_paths(
                    [subject_id], {subject_id: dataset}, lesion_cfg.data_root, lesion_cfg.lesion_glob
                )
                png_bytes = _static_png_bytes(
                    str(lesion_paths[subject_id]), threshold=lesion_cfg.binarize_threshold, cmap="autumn",
                    colorbar=False,
                )
            else:
                disconnectome_paths = resolve_lesion_paths(
                    [subject_id], {subject_id: dataset}, sdc_cfg.data_root, sdc_cfg.disconnectome_glob
                )
                png_bytes = _static_png_bytes(
                    str(disconnectome_paths[subject_id]), threshold=_DISCONNECTOME_DISPLAY_THRESHOLD,
                    cmap=_DISCONNECTOME_CMAP, colorbar=True,
                )
        except (ValueError, KeyError):
            raise PreventUpdate
        return dcc.send_bytes(png_bytes, filename=f"cluster_{cluster_label}_representative_{subject_id}.png")

    @app.callback(
        Output("cluster-download", "data"),
        Input("cluster-save-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_cluster_html(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            view, _n_subjects, _percentage_img, _missing = _cached_cluster_overlap_view(run, run_metadata(run), cluster_label, lesion_cfg)
        except ValueError:
            raise PreventUpdate
        return dcc.send_string(_style_nilearn_html(view.html), filename=f"cluster_{cluster_label}_overlap_map.html")

    @app.callback(
        Output("cluster-png-download", "data"),
        Input("cluster-png-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_cluster_png(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.pipeline != "clustering":
            raise PreventUpdate
        try:
            # Reuses the same process-lifetime cache the HTML download/panel display already
            # populate - percentage_img is the exact image the interactive view itself renders,
            # not a second build_overlap_map pass (see _build_cluster_overlap_view's docstring).
            _view, _n_subjects, percentage_img, _missing = _cached_cluster_overlap_view(run, run_metadata(run), cluster_label, lesion_cfg)
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_png_bytes(percentage_img, threshold=1e-6, cmap="hot", colorbar=True)
        return dcc.send_bytes(png_bytes, filename=f"cluster_{cluster_label}_overlap_map.png")

    @app.callback(
        Output("disconnection-map-panel", "style"),
        Input("run-picker", "value"),
    )
    def _update_disconnection_map_panel_visibility(run_key: str | None):
        if run_key is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        return {} if (run.modality == "sdc" and run.pipeline == "clustering") else {"display": "none"}

    @app.callback(
        Output("disconnection-map-content", "children"),
        Input("run-picker", "value"),
        Input("cluster-picker", "value"),
        Input("selected-disconnection-mode", "data"),
    )
    def _update_disconnection_map(run_key: str | None, cluster_label: int | None, map_mode: str):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        return disconnection_map_content_for(
            run, run_metadata(run), cluster_label, sdc_cfg,
            build_view=_cached_cluster_disconnection_view, map_mode=map_mode,
        )

    @app.callback(
        Output("selected-disconnection-mode", "data"),
        Input({"type": "disconnection-mode-btn", "mode": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def _select_disconnection_mode(_all_n_clicks: list[int]) -> str:
        if ctx.triggered_id is None:
            raise PreventUpdate
        return ctx.triggered_id["mode"]

    @app.callback(
        Output({"type": "disconnection-mode-btn", "mode": ALL}, "className"),
        Input("selected-disconnection-mode", "data"),
        State({"type": "disconnection-mode-btn", "mode": ALL}, "id"),
    )
    def _highlight_active_disconnection_mode(selected: str, ids: list[dict]) -> list[str]:
        return ["active" if button_id["mode"] == selected else "" for button_id in ids]

    @app.callback(
        Output("disconnection-download", "data"),
        Input("disconnection-save-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnection_html(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        try:
            view, _n_subjects, _mean_img, _missing = _cached_cluster_disconnection_view(run, run_metadata(run), cluster_label, sdc_cfg)
        except ValueError:
            raise PreventUpdate
        return dcc.send_string(
            _style_nilearn_html(view.html), filename=f"cluster_{cluster_label}_disconnection_mean_map.html"
        )

    @app.callback(
        Output("disconnection-png-download", "data"),
        Input("disconnection-png-btn", "n_clicks"),
        State("run-picker", "value"),
        State("cluster-picker", "value"),
        prevent_initial_call=True,
    )
    def _download_disconnection_png(_n_clicks: int, run_key: str | None, cluster_label: int | None):
        if run_key is None or cluster_label is None:
            raise PreventUpdate
        run = runs_by_key[run_key]
        if run.modality != "sdc" or run.pipeline != "clustering":
            raise PreventUpdate
        try:
            # Reuses the same process-lifetime cache the HTML download/panel display already
            # populate - mean_img is the exact image the interactive view itself renders, not a
            # second build_mean_map pass (see _build_cluster_disconnection_view's docstring).
            _view, _n_subjects, mean_img, _missing = _cached_cluster_disconnection_view(run, run_metadata(run), cluster_label, sdc_cfg)
        except ValueError:
            raise PreventUpdate
        png_bytes = _static_png_bytes(
            mean_img, threshold=_DISCONNECTOME_DISPLAY_THRESHOLD, cmap=_DISCONNECTOME_CMAP, colorbar=True,
        )
        return dcc.send_bytes(png_bytes, filename=f"cluster_{cluster_label}_disconnection_mean_map.png")

    def _preload_stores() -> None:
        """Reads every subject of every clustering run once, in the background, into the two
        BinaryMaskStores, so that afterwards ANY cluster of ANY run is a bincount + a ~1s render
        instead of minutes of reading NIfTIs (30-09-26, a live-demo need: all masks and SDC
        must browse fast). Lesion masks for every clustering run's subjects; disconnectomes for
        the subjects of sdc-modality runs only (the one modality showing that panel). Background
        optimisation only: a failure is logged with its traceback and leaves the store as far as
        it got - a click then reads whatever is still missing itself and raises visibly in the
        panel, nothing is hidden."""
        datasets: dict[str, dict[str, str]] = {"lesion": {}, "disconnection": {}}
        for run in runs:
            if run.pipeline != "clustering":
                continue
            metadata = run_metadata(run)
            by_subject = dict(zip(metadata["subject_id"], metadata["dataset"]))
            datasets["lesion"].update(by_subject)
            if run.modality == "sdc":
                datasets["disconnection"].update(by_subject)
        for name, store, cfg_data_root, glob in (
            ("lesion", lesion_store, lesion_cfg.data_root, lesion_cfg.lesion_glob),
            ("disconnection", disconnection_store, sdc_cfg.data_root, sdc_cfg.disconnectome_glob),
        ):
            by_subject = datasets[name]
            if not by_subject:
                continue
            try:
                paths, _missing = resolve_available_lesion_paths(list(by_subject), by_subject, cfg_data_root, glob)
                logging.info("preload %s: reading %d subject(s)", name, len(paths))
                store.preload(paths.values())
            except (ValueError, OSError):
                logging.warning("preload %s failed", name, exc_info=True)
                continue
            logging.info("preload %s: done, %d subject(s) in memory", name, len(paths))

    if preload:
        threading.Thread(target=_preload_stores, name="store-preload", daemon=True).start()

    return app
