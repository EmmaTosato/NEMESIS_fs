# Data retrieval — technical reference

Audience: developers/agents working on `src/retrieval/` and `src/pipeline/retrieve_data.py`. For "how do I run this", see `docs/guides/retrieval.md`.

Scope today: 4 stroke datasets in `Clinical_connectome` (`UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`). NEMESIS is a different source with a different layout (sessions, separate derivatives folders) and is **not** covered by this module — it will be addressed separately when that work starts, most likely by writing a second class alongside `Dataset`, not by generalizing this one speculatively.

## Module layout

```
src/retrieval/
├── config.py    # parsing/validation of data_retrieval.json - no filesystem I/O
└── dataset.py   # Dataset class - resolves paths for one dataset, does touch the filesystem
src/pipeline/
└── retrieve_data.py   # CLI entry point: validate upfront, copy, write report
```

Single-class design: **one** `Dataset` class is instantiated once per requested dataset name (`Dataset(project_root, "UNIPD/WashU")`), not a subclass per dataset. The 4 in-scope datasets share the same on-disk convention exactly; differences between them (which native sequences exist, presence of `participants.tsv`) are discovered from disk at runtime (`available_sequences()`, `has_mni_mask()`), never hardcoded per dataset name.

### `Dataset` — what `lesion_root` actually points to

```python
self.lesion_root = project_root / name      # e.g. .../UNIPD/WashU - the WHOLE dataset tree
self.features_root = project_root / "features" / name   # separate tree, Task 3, not used yet
```

`lesion_root` contains **both** native files (`sub-*/anat/...`) **and** the dataset's own `derivatives/manual_masks/...` subfolder — it is not "native-only". The axis that matters for lookups is the `space` parameter passed to methods (`native()` vs `mni_mask()`), not which root you start from. See the module docstring in `dataset.py` for the fuller writeup of this distinction (it caused real confusion during design — worth re-reading if extending this class).

`native()` and `mni_mask()` (not `anat()`/`derivatives()`) are the method names — "anat" is a BIDS datatype label reused ambiguously in both native and derivatives paths, so it is deliberately avoided as an identifier anywhere in this codebase; it only appears as a literal path-segment string when traversing the real on-disk folder name.

### Known limitation: `space="mni"` is not a generic space selector

`mni_mask()` is hardcoded to `derivatives/manual_masks/`. It works today because that is the *only* derivative that exists, and it happens to be in MNI space. If a second derivative appears — in MNI space or not — neither `native()` nor `mni_mask()` will find it automatically. Disambiguating between multiple derivatives (e.g. a `derivative` selector alongside `space`) is a decision to make when that second derivative actually exists, not now. See the docstring on `Dataset.mni_mask()` and the comment on `config.MNI_MODALITIES`.

## The STOP / WARNING / informational matrix

This is the core contract of the pipeline and is enforced in `src/pipeline/retrieve_data.py`:

| category | cases | where enforced |
|---|---|---|
| 🛑 STOP — validated upfront, across **all** requested datasets, before any file is copied | modality/space not structurally supported by a dataset · `group_filter` matches 0 subjects in a dataset · unknown explicit `subjects` entry · dataset root unreachable · invalid config | `_build_datasets`, `_validate_upfront` (`retrieve_data.py`), `load_config` (`config.py`) |
| ⚠️ WARNING — logged, run continues | file missing for a specific subject · copy fails for a specific file (permissions, disk full, ...) | `_retrieve_subject`, `_copy_one` |
| ℹ️ informational | destination already exists: skipped (`overwrite=false`) or overwritten (`overwrite=true`) | `_copy_one`, `_retrieve_participants` |

`group_filter` is **not** validated (and not applied) when `config.subjects` is set explicitly — picking exact subject IDs already expresses full intent, so group filtering would be redundant and potentially confusing (see `_validate_upfront`: the group-filter check is skipped entirely when `subjects is not None`).

`_build_datasets` instantiates every requested `Dataset` before any validation or copying starts — a missing dataset root raises immediately and nothing is copied for any dataset in the request, including ones that would have been valid.

## Config schema (`src/retrieval/config.py`)

`RetrievalConfig` fields: `output_root`, `project`, `project_root`, `datasets`, `group_filter`, `subjects`, `retrieve` (list of `RetrieveItem(space, modality)`), `include_tabular_data`, `overwrite`. All required fields are validated with no silent defaults (`load_config` raises `ValueError` naming the offending field). `config.py` never touches the filesystem — existence checks (dataset root, specific files) happen in `Dataset`/`retrieve_data.py`.

Native modalities: `T1w`, `T2w`, `FLAIR`, `CT`, `lesion_roi`. MNI modalities: `lesion_mask` (only one, see limitation above). Known groups: `ST`, `HC`, `PD`, `GM`.

## Output layout

```
<output_root>/<project>/<dataset>/
├── participants.tsv                        # verbatim copy, only if include_tabular_data and present at source
└── <subject_id>/lesion/
    ├── native/<original filename>.nii.gz
    └── mni/<original filename>.nii.gz
```

Filenames are preserved exactly as at the source (no renaming/transformation) — this is a straight copy, not a derived product.

## Report

Written to `reports/data_retrieval/<project>/<dd-mm-yy>__<hh-mm>.md` (fixed repo convention, like `data/`/`docs/`/`src/` — not itself in config, unlike `output_root`). Title is `<project>_<dd-mm-yy>` with the run time as a subtitle; the file name keeps minute precision so multiple runs on the same day don't collide.

Content, in order: a verbatim JSON dump of the fields actually read from the config (derived from the parsed `RetrievalConfig`, not a re-read of the file, so it can't drift from what the run actually used — see `_config_summary`); the aggregate summary table per dataset (subjects selected, copied, skipped, failed, participants status); then every WARNING-category miss (subject_id + what was missing), grouped per dataset with a `Missing Count = N` line and a `---` separator between datasets — never a list of successful copies, only anomalies. A dataset with zero misses is omitted from this section entirely.

No log file is currently written — `main()` only configures a console `StreamHandler` (`logging.basicConfig`, no `filename=`), so the narrative (skip/copied/warning lines) exists only in the terminal during the run and is not persisted. The report is the only persisted artifact per run.

## Testing

`tests/unit/` — synthetic fixtures in `tmp_path`, no EBRAIN mount required, run always. `tests/integration/` — against the real mount, `pytest.mark.skipif` if unreachable; several assert exact counts verified manually during design (e.g. WashU MNI mask count is 201, not 202 — one subject, `sub-STUNIPD0001`, has an orphaned derivative with no matching raw subject folder; see the comment in `tests/integration/test_lesion_counts.py`). Run with:

```bash
conda run -n nemesis python -m pytest tests/unit/ tests/integration/ -v
```
