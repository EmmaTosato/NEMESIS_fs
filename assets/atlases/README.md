# Atlases in this folder

This folder collects the atlas files used in the project. Paths below are relative to `assets/atlases/`.

## Cortical / cortex-based atlases

| Atlas | Files | Short note |
| --- | --- | --- |
| MNI Glasser HCP v1.0 | `MNI_Glasser_HCP_v1.0.nii.gz` | High-resolution multimodal cortical parcellation in MNI space. |

## Subcortical / cerebellar atlases

| Atlas | Files | Short note |
| --- | --- | --- |
| Harvard-Oxford subcortical | `HarvardOxford-sub-maxprob-thr25-2mm.nii.gz` | Standard probabilistic subcortical atlas in MNI152 space. Input to the combined Glasser+subcortical atlas below. |

## Notes

- The `build_combined_atlas.py` pipeline (Glasser MMP + Harvard-Oxford subcortical, 372-region combined atlas) and its output files were removed 25/08/26, along with `build_lesion_matrix.py`'s `parcellate` feature they fed — see `management/notes/TODO.md`. `MNI_Glasser_HCP_v1.0.nii.gz`/`HarvardOxford-sub-maxprob-thr25-2mm.nii.gz` above are kept as general-purpose reference atlases.

- Keep atlas filenames unchanged so scripts can reference them directly.
