"""Where a retrieved file lands locally, relative to a dataset's own folder.

Single source of truth for the local output layout - both
src.pipeline.retrieve_data (copy phase) and src.retrieval.verify (post-copy
checksum check) must agree on the exact same path for the same
(subject, RetrieveItem, filename), or verification would compare the wrong
file (or none at all). No filesystem dependency.

Layout is pipeline-first, mirroring real BIDS-Derivatives
(`<dataset>/derivatives/<pipeline>/sub-XXX/<datatype>/<file>`) rather than
grouping by subject first - deliberately chosen over an earlier subject-first
layout (`sub-XXX/<object>/<pipeline>/<datatype>/<file>`) once it was pointed
out that pipeline-first is what BIDS actually specifies, and that the
project intends to stop needing a fake pipeline name for non-BIDS-conformant
objects like `feature` over time (see _LOCAL_PIPELINE_LABEL_FOR_OBJECT). The
`object` axis (`lesion`/`feature`) itself never appears as its own path
segment any more - it's implicit in which pipeline folder a file sits under.
This trades away a structural guarantee the old layout had (two different
`object`s could never collide, since `object` was always the first path
segment) for BIDS conformance - safe today because the two pipeline-folder
names in use (`manual_masks`, `features`) don't collide, but not enforced by
any invariant in the code the way `KNOWN_OBJECTS` enforces `object` itself.
"""

from __future__ import annotations

from pathlib import Path

from src.retrieval.config import RetrievalConfig, RetrieveItem

# Real BIDS-Derivatives pipeline names (e.g. `manual_masks`) are used as-is
# via item.pipeline. Objects forbidding a pipeline (today: `feature`) have no
# such name at the source (see docs/dev/retrieval.md), so we choose one
# ourselves for local organization purposes only - not a claim that this is
# the pipeline name the source would use. Every object in
# config._OBJECTS_FORBIDDING_PIPELINE must have an entry here.
_LOCAL_PIPELINE_LABEL_FOR_OBJECT = {"feature": "features"}


def local_dataset_root(config: RetrievalConfig, dataset_name: str) -> Path:
    """Local root for one dataset's retrieved files - always nested under a
    single `derivatives/` level directly below `project`, regardless of
    which `object`/`pipeline` produced the file. Everything this pipeline
    ever retrieves (lesion masks via the real `manual_masks` BIDS-Derivatives
    pipeline, feature CSVs with no formal pipeline name at all - see
    docs/dev/retrieval.md) is itself derived/processed data, never a raw BIDS
    acquisition - native/raw retrieval is deliberately out of scope (see
    "This round vs. a future native/raw round" in that doc). One shared
    `derivatives/` above every dataset, not one per dataset mirroring the
    source's own `<dataset>/derivatives/<pipeline>/` layout, is a deliberate
    choice: it says "nothing under data/ is ever raw", true for the whole
    project at once, rather than "this specific pipeline's output happens to
    be a derivative", true per (dataset, pipeline) - see decision discussed
    when `feature` retrieval was added.

    `participants.tsv` also lives directly under this root (a sibling of the
    pipeline folders below) - it's a copy of a per-dataset file, not tied to
    one object/pipeline, so it doesn't need `local_relative_path`'s nesting.
    """
    return config.output_root / config.project / "derivatives" / dataset_name


def pipeline_folder(item: RetrieveItem) -> str:
    """The local top-level folder name for this item's `object` - the real
    BIDS-Derivatives pipeline name when the object has one (`item.pipeline`),
    or the registered stand-in for objects that structurally forbid one (see
    _LOCAL_PIPELINE_LABEL_FOR_OBJECT). Raises clearly if a pipeline-less
    object has no stand-in registered, rather than silently reusing the
    object name or crashing on a None path segment."""
    if item.pipeline is not None:
        return item.pipeline
    if item.object not in _LOCAL_PIPELINE_LABEL_FOR_OBJECT:
        raise ValueError(
            f"no local pipeline-folder label registered for object={item.object!r} "
            "- add it to output_layout._LOCAL_PIPELINE_LABEL_FOR_OBJECT"
        )
    return _LOCAL_PIPELINE_LABEL_FOR_OBJECT[item.object]


def local_relative_path(item: RetrieveItem, subject_id: str, filename: str) -> Path:
    """<pipeline-or-stand-in>/<subject_id>/<datatype>/<filename> - pipeline
    first, then subject, matching real BIDS-Derivatives ordering (see module
    docstring), unlike the dataset-root prefix from local_dataset_root()
    which groups by dataset, not by pipeline."""
    return Path(pipeline_folder(item), subject_id, item.datatype, filename)
