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

## Derived / combined atlases

| Atlas | Files | Built by | Short note |
| --- | --- | --- | --- |
| Glasser MMP + Harvard-Oxford subcortical, 372 regions | `glasser_hcp_harvardoxford_subcortical_372.nii.gz`, `glasser_hcp_harvardoxford_subcortical_372_labels.csv` | `src/pipeline/build_combined_atlas.py` (`config/pipelines/build_combined_atlas.json`) | 360 Glasser cortical parcels + 12 Harvard-Oxford subcortical structures (thalamus/caudate/putamen/pallidum/hippocampus/amygdala, L+R), merged into one label volume — reproduces the parcellation used by Thiebaut de Schotten et al. 2020 ahead of varimax PCA. Not checked into git (gitignored like every other `.nii.gz` in this folder); regenerate via `python -m src.pipeline.build_combined_atlas --config config/pipelines/build_combined_atlas.json` if missing. See `docs/guides/analysis.md` §0. |

## Notes

- Keep atlas filenames unchanged so scripts can reference them directly.
