"""Registry of available analysis-pipeline steps.

Adding a new step is a small, explicit change: implement a Step-shaped
function (see src.utils.step) plus its own params validator, then add one
entry here - no other module needs to change. src.analysis.config validates
step names against whatever registry is passed to it, and
src.pipeline.run_analysis_pipeline looks up steps by name from the same
registry, injected as an explicit parameter rather than imported directly -
so callers (tests, in particular) can supply their own small registry
without needing any real step implementation to exist.

STEP_REGISTRY is empty for now. Real steps (a lesion-mask feature extractor,
PCA/t-SNE/UMAP, clustering algorithms) are added in a follow-up once this
pipeline skeleton is in place - this is a deliberate, documented empty
state, not an oversight.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.utils.step import Step


@dataclass(frozen=True)
class StepDefinition:
    run: Step
    validate_params: Callable[[dict[str, Any]], dict[str, Any]]
    requires_input: bool


STEP_REGISTRY: dict[str, StepDefinition] = {}
