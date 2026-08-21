# enrich_lesion_metadata — 17-08-26 17:04:54

metadata_path: `data/derived/lesion_matrix/21-07_s1.1/metadata.csv`
compute_volume: False
Requested variables: ['age', 'sex', 'education', 'lesion_side', 'clinical_date', 'NIHSS']

## Coverage by dataset

| dataset | subjects | participants.tsv | missing subjects | missing variables |
|---|---|---|---|---|
| UKLFR/stroke_UKLFR | 697 | found | — | — |
| UNIPD/PASPORT | 83 | found | — | NIHSS, clinical_date, lesion_side |
| UNIPD/PSP | 168 | found | — | — |
| UNIPD/WashU | 202 | found | — | — |

## Verdict

**OK** - safe to join (missing-variable gaps above become NaN, not an error).
