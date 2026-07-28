# clinical_connectome_27-07-26
## 12:05

## Config

```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome/derivatives",
  "dataset": "UNIPD/WashU",
  "atlas_root": "assets/atlases/fmriprep",
  "atlas_combos": [
    "Yan100TianS1Buckner7N",
    "Yan100TianS2Buckner7N",
    "Yan100TianS3Buckner7N",
    "Yan200TianS1Buckner7N",
    "Yan200TianS3Buckner7N",
    "Yan300TianS1Buckner7N",
    "Yan300TianS2Buckner7N",
    "Yan300TianS3Buckner7N",
    "Yan400TianS1Buckner7N",
    "Yan400TianS2Buckner7N",
    "Yan400TianS3Buckner7N"
  ],
  "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
  "fc_glob_template": "features/*/func/*_FC-pearson_atlas-{combo}.csv",
  "min_coverage": 0.5,
  "resample_interpolation": "nearest",
  "binarize_threshold": 0.5,
  "output_root": "data/derived/features/masked_fc",
  "session_name": "s2",
  "overwrite": false,
  "run_notes": "seconda run reale di masking FC-lesione, le restanti 11 combo atlante (Yan200TianS2Buckner7N gia' processata in s1)"
}
```

## Summary

| atlas combo | subjects masked | mean compromised nodes |
|---|---:|---:|
| Yan100TianS1Buckner7N | 169 | 1.9 |
| Yan100TianS2Buckner7N | 169 | 2.4 |
| Yan100TianS3Buckner7N | 169 | 3.2 |
| Yan200TianS1Buckner7N | 169 | 3.3 |
| Yan200TianS3Buckner7N | 169 | 4.7 |
| Yan300TianS1Buckner7N | 169 | 5.6 |
| Yan300TianS2Buckner7N | 169 | 6.1 |
| Yan300TianS3Buckner7N | 169 | 6.9 |
| Yan400TianS1Buckner7N | 169 | 7.0 |
| Yan400TianS2Buckner7N | 169 | 7.5 |
| Yan400TianS3Buckner7N | 169 | 8.3 |
