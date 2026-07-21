# Atlases in this folder

This folder collects the atlas files used in the project. Paths below are relative to `assets/atlases/`.

## Cortical / cortex-based atlases

| Atlas | Files | Short note |
| --- | --- | --- |
| MNI Glasser HCP v1.0 | `MNI_Glasser_HCP_v1.0.nii.gz` | High-resolution multimodal cortical parcellation in MNI space. |
| Schaefer 2018, 200 parcels, 7 networks | `Schaefer200_space-MNI152NLin6_res-1x1x1.nii.gz`, `Schaefer200_7N.tsv` | Functional cortical parcellation with 7-network solution. |
| Schaefer 2018, 300 parcels, 7 networks | `Schaefer300_space-MNI152NLin6_res-1x1x1.nii.gz`, `Schaefer300_7N.tsv` | Same family, finer cortical resolution. |
| Schaefer 2018, 400 parcels, 7 networks | `Schaefer400_space-MNI152NLin6_res-1x1x1.nii.gz`, `Schaefer400_7N.tsv` | Same family, finer cortical resolution. |
| Schaefer 2018 + Tian subcortex, S1 | `Schaefer2018_200Parcels_7Networks_order_Tian_Subcortex_S1_MNI152NLin6Asym_1mm.nii.gz`, `Schaefer2018_200Parcels_7Networks_order_Tian_Subcortex_S1_label.txt` | Schaefer 200 parcels with Tian subcortical extension (scale S1). |
| Schaefer 2018 + Tian subcortex, S2 | `Schaefer2018_200Parcels_7Networks_order_Tian_Subcortex_S2_MNI152NLin6Asym_1mm.nii.gz`, `Schaefer2018_200Parcels_7Networks_order_Tian_Subcortex_S2_label.txt` | Schaefer 200 parcels with Tian subcortical extension (scale S2). |

## Subcortical / cerebellar atlases

| Atlas | Files | Short note |
| --- | --- | --- |
| Harvard-Oxford subcortical | `HarvardOxford-sub-maxprob-thr25-2mm.nii.gz` | Standard probabilistic subcortical atlas in MNI152 space. |
| Tian subcortex, S1 | `Tian_Subcortex_S1_3T.nii.gz`, `Tian_Subcortex_S1_3T_label.txt` | Multi-scale subcortical atlas, 3T version. |
| Tian subcortex, S2 | `Tian_Subcortex_S2_3T.nii.gz`, `Tian_Subcortex_S2_3T_label.txt` | Multi-scale subcortical atlas, 3T version. |
| Tian subcortex, S3 | `Tian_Subcortex_S3_3T.nii.gz`, `Tian_Subcortex_S3_3T_label.txt` | Multi-scale subcortical atlas, 3T version. |
| Tian subcortex, S4 | `Tian_Subcortex_S4_3T.nii.gz`, `Tian_Subcortex_S4_3T_label.txt` | Multi-scale subcortical atlas, 3T version. |
| Buckner 7n | `atl-Buckner7_space-MNI_dseg.nii`, `atl-Buckner7.tsv` | Cerebellar/network-based atlas. |

## Notes

- The Schaefer + Tian files are hybrid cortex-subcortex parcellations.
- The Tian subcortical bundle here is the 3T NIfTI version from `Tian2020MSA`.
- Keep atlas filenames unchanged so scripts can reference them directly.
