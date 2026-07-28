# clinical_connectome_27-07-26
## 13:39

## Config

```json
{
  "project": "clinical_connectome",
  "masked_fc_root": "data/derived/features/masked_fc",
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
  "output_root": "data/derived/features/fc_matrix",
  "session_name": "s2",
  "overwrite": false,
  "run_notes": "seconda matrice impilata da FC mascherate (masked_fc/s2), le restanti 11 combo atlante (Yan200TianS2Buckner7N gia' impilata in s1) - contiene ancora NaN, nessuna imputazione, nessuna soglia di esclusione soggetto ancora decisa"
}
```

## Summary

| atlas combo | shape | constant edges dropped | NaN/subject (min/mean/max) |
|---|---|---:|---|
| Yan100TianS1Buckner7N | 169x7503 | 0 | 0/254.9/2453 |
| Yan100TianS2Buckner7N | 169x9591 | 0 | 0/360.6/3263 |
| Yan100TianS3Buckner7N | 169x12246 | 0 | 0/524.8/4245 |
| Yan200TianS1Buckner7N | 169x24753 | 0 | 0/827.4/7733 |
| Yan200TianS3Buckner7N | 169x32896 | 0 | 0/1283.3/10741 |
| Yan300TianS1Buckner7N | 169x52003 | 0 | 0/2132.1/17812 |
| Yan300TianS2Buckner7N | 169x57291 | 0 | 0/2416.4/19890 |
| Yan300TianS3Buckner7N | 169x63546 | 0 | 0/2814.9/22218 |
| Yan400TianS1Buckner7N | 169x89253 | 0 | 0/3604.9/31623 |
| Yan400TianS2Buckner7N | 169x96141 | 0 | 0/3973.5/34365 |
| Yan400TianS3Buckner7N | 169x104196 | 0 | 0/4483.9/37401 |
