# enrich_lesion_metadata — 28-08-26 14:51:39

metadata_path: `data/derived/lesion_matrix/21-07_s1.1/metadata.csv`
compute_volume: True
Requested variables: ['lesion_side', 'NIHSS', 'age', 'sex', 'education', 'clinical_date']

## Coverage by dataset

| dataset | subjects | participants.tsv | missing subjects | missing variables |
|---|---|---|---|---|
| UKLFR/stroke_UKLFR | 697 | found | — | — |
| UNIPD/PASPORT | 83 | found | — | NIHSS, clinical_date, lesion_side |
| UNIPD/PSP | 168 | found | — | — |
| UNIPD/WashU | 202 | found | — | — |

## Verdict

**OK** - safe to join (missing-variable gaps above become NaN, not an error).
