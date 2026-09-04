"""Where a retrieved file lands locally, relative to a dataset's own folder.

Single source of truth for the local output layout - both
src.pipeline.retrieve_data (copy phase) and src.retrieval.verify (post-copy
checksum check) must agree on the exact same path for the same
(subject, RetrieveItem, filename), or verification would compare the wrong
file (or none at all). No filesystem dependency.

Layout is pipeline-first, mirroring real BIDS-Derivatives
(`<dataset>/derivatives/<pipeline>/sub-XXX/<datatype>/<file>`) - see
docs/dev/retrieval.md's "Output layout" section for the full rationale and
the trade-off this makes against the earlier subject-first layout. One
exception: `sdc`'s `<datatype>` segment ("dwi") isn't a real folder at the
source, so it's omitted for that object - see
_OBJECTS_WITHOUT_DATATYPE_FOLDER below.
"""

from __future__ import annotations

from pathlib import Path

from src.retrieval.config import RetrievalConfig, RetrieveItem

# Real BIDS-Derivatives pipeline names (e.g. `manual_masks`) are used as-is
# via item.pipeline. Objects forbidding a pipeline (today: `feature`, `sdc`)
# have no such name at the source (see docs/dev/retrieval.md), so we choose
# one ourselves for local organization purposes only - not a claim that this
# is the pipeline name the source would use. `sdc` is the same Stage1+Stage2
# BCBToolKit output src/sdc/runner.py itself produces - just not run through
# our own `compute_sdc.py --mode manifest/run/aggregate` orchestration for
# this particular run, so it has no `manifest.csv`/`_status/` written by us
# (see docs/dev/retrieval.md). Every object in
# config._OBJECTS_FORBIDDING_PIPELINE must have an entry here.
_LOCAL_PIPELINE_LABEL_FOR_OBJECT = {"feature": "features", "sdc": "sdc"}

# `sdc`'s `datatype` ("dwi") is a BIDS content-type *label* only, not a real
# folder at the source: file_patterns_server.json's sdc templates land the
# file directly under `lesion/{subject_id}/`, with no `dwi/` segment (unlike
# lesion's `anat`/feature's `func`, which ARE real source folders) - so the
# local layout doesn't fabricate one either. Every object here skips the
# datatype path segment; anything not listed keeps it.
_OBJECTS_WITHOUT_DATATYPE_FOLDER = frozenset({"sdc"})


def local_dataset_root(config: RetrievalConfig, dataset_name: str) -> Path:
    """Local root for one dataset's retrieved files - always nested under a
    single `derivatives/` level directly below `project`, regardless of
    which `object`/`pipeline` produced the file (see docs/dev/retrieval.md
    for why one shared `derivatives/` and not one per dataset/pipeline).
    `participants.tsv` also lives directly under this root - a copy of a
    per-dataset file, not tied to one object/pipeline.
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
    which groups by dataset, not by pipeline. Objects in
    _OBJECTS_WITHOUT_DATATYPE_FOLDER (today: `sdc`) skip the datatype
    segment entirely - their `datatype` has no real folder at the source, so
    the file sits directly under <subject_id>/."""
    if item.object in _OBJECTS_WITHOUT_DATATYPE_FOLDER:
        return Path(pipeline_folder(item), subject_id, filename)
    return Path(pipeline_folder(item), subject_id, item.datatype, filename)
