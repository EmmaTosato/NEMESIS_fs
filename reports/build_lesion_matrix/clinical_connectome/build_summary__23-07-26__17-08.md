# clinical_connectome_23-07-26
## 17:08

## Config

```json
{
  "project": "clinical_connectome",
  "data_modality": "lesion",
  "data_root": "data/clinical_connectome/derivatives",
  "datasets": [
    "UNIPD/WashU",
    "UNIPD/PASPORT",
    "UNIPD/PSP",
    "UKLFR/stroke_UKLFR"
  ],
  "reference_template_path": "data/clinical_connectome/derivatives/UNIPD/WashU/manual_masks/sub-STUNIPD0001/anat/sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz",
  "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
  "binarize_threshold": 0.5,
  "resample_interpolation": "nearest",
  "parcellate": true,
  "atlas_path": "assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz",
  "parcel_aggregation": "fraction_lesioned",
  "save_parcellated_volumes": false,
  "output_root": "data/derived/lesion_matrix",
  "session_name": "s1.2",
  "overwrite": false,
  "run_notes": "parcellated on the 372-region Glasser HCP + Harvard-Oxford subcortical atlas (build_combined_atlas.py output)"
}
```

## Summary

Matrix shape: 1150 subjects x 372 features
Parcellated: true (372 atlas parcels survived the constant-feature drop)

| dataset | subjects |
|---|---|
| UKLFR/stroke_UKLFR | 697 |
| UNIPD/PASPORT | 83 |
| UNIPD/PSP | 168 |
| UNIPD/WashU | 202 |