"""Registry of embedding-coloring modes shared between dim_reduction.py's
production and fine-tuning output (src/analysis/embedding_plots.py).

Adding a new way to color an embedding (e.g. a clinical score) means adding
one entry here plus its name to a pipeline's `color_by` config list - no
other code changes. Each mode declares whether its values are a category
(rendered with a legend, see plotting.plot_embedding_categorical) or a
continuous quantity (rendered with a colorbar, see
plotting.plot_embedding_continuous), and how to compute one value per
subject from (metadata, X) - X is the raw feature matrix, used only by modes
that derive a value from it (volume); modes that only need metadata
(dataset, side) ignore their X argument.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from src.features.clinical import join_lesion_side, join_nihss

ColorKind = Literal["categorical", "continuous"]


@dataclass(frozen=True)
class ColorMode:
    kind: ColorKind
    compute: Callable[[pd.DataFrame, np.ndarray], np.ndarray]
    label: str
    # continuous only - see plot_embedding_continuous/plot_embedding_grid_blocks's
    # own log_scale param. Ignored for categorical modes.
    log_scale: bool = False


COLOR_MODES: dict[str, ColorMode] = {
    "dataset": ColorMode(
        kind="categorical",
        compute=lambda metadata, X: metadata["dataset"].to_numpy(),
        label="dataset",
    ),
    "side": ColorMode(
        kind="categorical",
        compute=lambda metadata, X: join_lesion_side(metadata).to_numpy(),
        label="lesion side",
    ),
    "volume": ColorMode(
        kind="continuous",
        # Same quantity dim_reduction.py's regress_out_volume/lesion_volume_voxels
        # column already uses - voxel count, not ml (a scalar rescaling, no need
        # to convert here either).
        compute=lambda metadata, X: X.sum(axis=1),
        label="lesion volume (voxels)",
        # Heavily right-skewed (a handful of large-lesion outliers otherwise
        # stretch a linear scale so far that almost every other point looks
        # the same dark color - visually confirmed on the real 1150-subject
        # cohort, session 2026-08-04) - log makes the whole cohort's spread
        # readable again.
        log_scale=True,
    ),
    "nihss": ColorMode(
        kind="continuous",
        # NaN for subjects with no resolvable NIHSS (dataset-wide gap, e.g.
        # PASPORT, or a per-subject missing cell) - see join_nihss and
        # plot_embedding_continuous's NaN handling (rendered neutral gray).
        compute=lambda metadata, X: join_nihss(metadata).to_numpy(),
        label="NIHSS (severity)",
        # Linear: less skewed than volume, and kept on the same viridis
        # palette as volume (not a second hue family) - deliberately, on
        # request, log_scale=False is the actual differentiator between the
        # two modes' plots, not the colormap.
    ),
}


def resolve_color_mode(name: str) -> ColorMode:
    """Raises ValueError (with the known-modes list) if `name` isn't
    registered - a color_by entry from config must fail with a clear
    message, not a raw KeyError.
    """
    if name not in COLOR_MODES:
        raise ValueError(f"unknown color_by mode {name!r} - known: {sorted(COLOR_MODES)}")
    return COLOR_MODES[name]
