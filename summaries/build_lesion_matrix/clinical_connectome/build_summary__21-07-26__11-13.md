# clinical_connectome_21-07-26
## 11:13

## Config

```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome",
  "datasets": [
    "UNIPD/WashU",
    "UNIPD/PASPORT",
    "UNIPD/PSP",
    "UKLFR/stroke_UKLFR"
  ],
  "reference_template_path": "data/clinical_connectome/UNIPD/WashU/sub-STUNIPD0001/lesion/manual_masks/anat/sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz",
  "lesion_glob": "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz",
  "binarize_threshold": 0.5,
  "resample_interpolation": "nearest",
  "parcellate": false,
  "atlas_path": null,
  "parcel_aggregation": null,
  "save_parcellated_volumes": false,
  "output_root": "data/derived/lesion_matrix",
  "run_name": "run1",
  "overwrite": false,
  "run_notes": null
}
```

## Summary

Matrix shape: 1150 subjects x 254865 features
Parcellated: false (voxel-wise)

| dataset | subjects |
|---|---|
| UKLFR/stroke_UKLFR | 697 |
| UNIPD/PASPORT | 83 |
| UNIPD/PSP | 168 |
| UNIPD/WashU | 202 |