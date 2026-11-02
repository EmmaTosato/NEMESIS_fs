"""The brain map of each component of a PCA run: where in the brain a component weighs.

Only a PCA-family run has them (its components are directions in the original voxel space, see
_is_pca_run); the maps themselves are computed and cached by component_maps, this panel reads
them and lays them out.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import nibabel as nib
import numpy as np
from dash import dcc, html
from nilearn import plotting as nilearn_plotting
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.component_map_plots import build_reproducibility_figure
from src.analysis.component_maps import ComponentMapSet, ComponentMapStore, MapGeometry, load_map_geometry, to_volume
from src.analysis.embedding_app.anatomy import _ANATOMY_VIEWER_WIDTH, _anatomy_viewer, _masked_for_view_colorbar
from src.analysis.embedding_app.blocks import _warning_box
from src.analysis.embedding_app.runs import ProductionRun, run_metadata
from src.analysis.embedding_app.style import _italian_figure
from src.utils.artifacts import MANIFEST_FILENAME, MATRIX_FILENAME, read_run_config
from src.utils.number_format import format_number


# --- PCA component maps (16-10-26) ---------------------------------------------------------------

# A voxel of a component's map is coloured when its |t| reaches this share of the component's peak |t|: with
# thousands of subjects even small effects have a high t, and a fixed |t| > 3 would colour almost the whole brain.
COMPONENT_MAP_THRESHOLD_FRACTION = 0.3
_COMPONENT_MAP_CMAP = "cold_hot"


@dataclass(frozen=True)
class ComponentMapData:
    """What the component-map panel needs for one pca run: the maps, where their voxels are, and whether the
    source matrix was modified after the run was written (the maps then pair the run's scores with a matrix that
    may not be the one they came from)."""

    maps: ComponentMapSet
    geometry: MapGeometry
    source_modified_after_run: bool


def _is_pca_run(run: ProductionRun) -> bool:
    return run.pipeline == "dim_reduction" and run.method == "pca"


def run_component_maps(run: ProductionRun, store: ComponentMapStore) -> ComponentMapData | None:
    """The component maps of a pca dim_reduction run (src/analysis/component_maps.py), or None while they are
    still being computed in the background.

    The scores are the run's own matrix.npy; the matrix they are regressed against is the run's `input_path`
    (relative to the folder the app is launched from, the repo root). Raises ValueError, with the cause, for a
    run that is not a pca one, a source matrix that is missing, not voxelwise, or not the run's (other subjects)."""
    if not _is_pca_run(run):
        raise ValueError("component maps exist only for dim_reduction runs with the pca method")
    input_path = read_run_config(run.path)["input_path"]
    source_dir = Path(input_path)
    if not (source_dir / MATRIX_FILENAME).is_file():
        raise ValueError(
            f"the matrix the run was computed on ({input_path}) does not exist: it is needed for the maps, "
            "and it is looked up from the folder the app was launched from"
        )
    geometry = load_map_geometry(source_dir)
    maps = store.request(source_dir, np.load(run.path / MATRIX_FILENAME), run_metadata(run)["subject_id"].tolist())
    if maps is None:
        return None
    written = datetime.fromisoformat(json.loads((run.path / MANIFEST_FILENAME).read_text())["created_at"])
    modified = datetime.fromtimestamp((source_dir / MATRIX_FILENAME).stat().st_mtime, tz=timezone.utc)
    return ComponentMapData(maps=maps, geometry=geometry, source_modified_after_run=modified > written)


def _build_component_map_view(data: ComponentMapData, component: int) -> tuple[StatMapView, float]:
    """(interactive view, peak t) of one component (1-based): the t-map of the component, voxels below
    COMPONENT_MAP_THRESHOLD_FRACTION of its peak left uncoloured, the three sections crossing at the peak.
    Raises ValueError for a component with an all-zero map or outside the run's components."""
    n_components = data.maps.t.shape[0]
    if not 1 <= component <= n_components:
        raise ValueError(f"component {component} does not exist: the run has {n_components}")
    t_map = np.asarray(data.maps.t[component - 1])
    peak_column = int(np.argmax(np.abs(t_map)))
    peak = float(t_map[peak_column])
    if peak == 0.0:
        raise ValueError(f"the map of component {component} is all zero: no voxel has an effect")
    peak_voxel = np.unravel_index(np.flatnonzero(data.geometry.mask)[peak_column], data.geometry.shape)
    peak_mm = nib.affines.apply_affine(data.geometry.affine, peak_voxel)
    shown = _masked_for_view_colorbar(to_volume(t_map, data.geometry), COMPONENT_MAP_THRESHOLD_FRACTION * abs(peak))
    view = nilearn_plotting.view_img(
        shown, bg_img="MNI152", black_bg=False, threshold=1e-6, cmap=_COMPONENT_MAP_CMAP, symmetric_cmap=True,
        vmax=abs(peak), cut_coords=tuple(float(c) for c in peak_mm), title=None, width_view=_ANATOMY_VIEWER_WIDTH,
    )
    return view, peak


def component_maps_content_for(
    run: ProductionRun,
    component: int,
    maps_of: Callable[[ProductionRun], ComponentMapData | None],
    view_of: Callable[[ComponentMapData, int], tuple[StatMapView, float]] = _build_component_map_view,
) -> tuple[html.Div | html.P, bool]:
    """(content, pending) of the "Mappe delle componenti" panel for one component (1-based) of a pca run:
    the reproducibility of every component's map, then the chosen component's t-map in an interactive viewer.
    `pending` is True while the maps are still being computed: the content then says so and the caller keeps
    polling. Same never-raises contract as the other *_content_for functions."""
    try:
        data = maps_of(run)
    except (ValueError, OSError) as exc:
        return html.P(str(exc), className="status-message"), False
    if data is None:
        return html.P(
            "Computing the maps: one pass over the voxel matrix for each subject, from a few minutes "
            "upwards depending on the matrix. It is saved to disk: next time it is instant. The page updates by itself.",
            className="status-message",
        ), True
    try:
        view, peak = view_of(data, component)
    except ValueError as exc:
        return html.P(str(exc), className="status-message"), False

    reproducibility = data.maps.reproducibility
    children: list = []
    if data.source_modified_after_run:
        children.append(_warning_box(
            "The matrix the run was computed on was modified after the run. If its subjects or its values "
            "have changed, the maps pair the run scores with data that is not what they came from."
        ))
    children += [
        html.P(
            f"Mean reproducibility {format_number(float(reproducibility.mean()), 3)} ± "
            f"{format_number(float(reproducibility.std(ddof=1)) if len(reproducibility) > 1 else 0.0, 3)}, "
            f"from {format_number(float(reproducibility.min()), 3)} (component {int(reproducibility.argmin()) + 1}) to "
            f"{format_number(float(reproducibility.max()), 3)} (component {int(reproducibility.argmax()) + 1}). "
            "The paper reports 0.813 ± 0.079 with halves of 666 subjects: here the halves are much larger, so the values are not directly comparable.",
            className="section-intro",
        ),
        dcc.Graph(
            figure=_italian_figure(build_reproducibility_figure(reproducibility, component)),
            config={"displayModeBar": True, "modeBarButtons": [["toImage"]], "displaylogo": False},
            style={"width": "100%"},
        ),
        _anatomy_viewer(
            view,
            heading=f"Component {component}: max t {format_number(abs(peak), 0)}, reproducibility {format_number(float(reproducibility[component - 1]), 2)}",
            caption=(
                "Red: the more a subject has this component, the more that voxel is disconnected. Blue: the more it has it, the less it is disconnected. "
                f"Voxels with |t| of at least {format_number(COMPONENT_MAP_THRESHOLD_FRACTION * 100, 0)}% of the peak are colored."
            ),
            note=(
                "The sign of a component is arbitrary: each map is oriented with the peak red, so look at the shape, "
                "not the color. The map is the t of a multiple regression per voxel on the scores of all components together "
                "(not the component weights), without a permutation test."
            ),
        ),
    ]
    return html.Div(children), False
