"""Shared contract every analysis-pipeline step conforms to.

A Step is a pure function: it receives the previous step's StepResult (or
None, only for the first step in a chain) plus its own already-validated
params, and returns a new StepResult. It performs no I/O and knows nothing
about caching, checkpoints, or where its output will be persisted - that is
the pipeline layer's responsibility (see src.pipeline.checkpoint), so a step
can later be run in-process, in a subprocess, or as a submitted cluster job
without any change to the step itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StepResult:
    """Output of a single pipeline step.

    `X` and `metadata` are always positionally aligned: row i of X describes
    the same sample as row i of metadata. A step that only transforms X (e.g.
    a dimensionality reduction) must carry `metadata` through unchanged
    except for adding columns (e.g. clustering adds a label column) -
    existing rows/columns are never reordered or dropped downstream.
    """

    X: np.ndarray
    metadata: pd.DataFrame
    params_used: dict[str, Any]
    step_name: str
    extra_arrays: dict[str, np.ndarray] = field(default_factory=dict)
    extra_tables: dict[str, pd.DataFrame] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.X.shape[0] != len(self.metadata):
            raise ValueError(
                f"StepResult for step {self.step_name!r}: X has {self.X.shape[0]} rows "
                f"but metadata has {len(self.metadata)} rows - must match"
            )


Step = Callable[[StepResult | None, dict[str, Any]], StepResult]
