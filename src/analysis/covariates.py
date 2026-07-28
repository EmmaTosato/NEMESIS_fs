"""Post-reduction covariate adjustment for dimensionality-reduction embeddings.

`jaccard`/`dice` already normalize distances by each subject's own lesion
size (see docs/methods/dimensionality_reduction.md) - regressing lesion
volume out again on top of one of those metrics would remove real
topographic signal, not a confound. This module stays metric-agnostic
itself (`regress_out_covariate` will happily residualize any embedding);
`check_volume_regression_compatible` is the one place that encodes which
metrics already do this normalization, so the incompatibility is caught
once, not re-derived at every call site.
"""

from __future__ import annotations

import numpy as np

_VOLUME_NORMALIZED_METRICS = {"jaccard", "dice"}


def regress_out_covariate(embedding: np.ndarray, covariate: np.ndarray) -> np.ndarray:
    """Removes the linear effect of `covariate` from each embedding column via OLS residuals."""
    if embedding.shape[0] != covariate.shape[0]:
        raise ValueError(
            f"embedding has {embedding.shape[0]} rows but covariate has {covariate.shape[0]} values "
            "- need exactly one covariate value per subject"
        )
    if np.std(covariate) == 0:
        raise ValueError("covariate has zero variance across subjects - nothing to regress out")

    design = np.column_stack([np.ones(covariate.shape[0]), covariate.astype(float)])
    coefficients, *_ = np.linalg.lstsq(design, embedding, rcond=None)
    return embedding - design @ coefficients


def check_volume_regression_compatible(regress_out_volume: bool, reduction_params: dict) -> None:
    """Raises if `regress_out_volume` is requested together with a metric that
    already normalizes distances by lesion volume (jaccard/dice) - stacking
    both would silently over-correct. A method/params with no `metric` key
    (pca, pacmap today) has no such normalization, so it is unaffected.
    """
    metric = reduction_params.get("metric")
    if regress_out_volume and metric in _VOLUME_NORMALIZED_METRICS:
        raise ValueError(
            f"regress_out_volume=True is incompatible with metric={metric!r} - {metric} already "
            "normalizes distances by lesion volume; regressing it out again would remove real "
            "topographic signal, not a confound. Set regress_out_volume=False or use a different metric."
        )
