# clinical_connectome_24-07-26
## 16:36

## Config

```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome/derivatives",
  "dataset": "UNIPD/WashU",
  "atlas_root": "assets/atlases/fmriprep",
  "atlas_combos": [
    "Yan200TianS2Buckner7N"
  ],
  "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
  "fc_glob_template": "features/*/func/*_FC-pearson_atlas-{combo}.csv",
  "min_coverage": 0.5,
  "resample_interpolation": "nearest",
  "binarize_threshold": 0.5,
  "output_root": "data/derived/features/masked_fc",
  "session_name": "s1",
  "overwrite": false,
  "run_notes": "prima run reale di masking FC-lesione, una sola combo atlante (Yan200TianS2Buckner7N) prima di estendere alle altre 11"
}
```

## Summary

| atlas combo | subjects masked | mean compromised nodes |
|---|---:|---:|
| Yan200TianS2Buckner7N | 169 | 3.9 |
