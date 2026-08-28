# enrich_lesion_metadata — 28-08-26 14:52:29

metadata_path: `data/derived/lesion_matrix/25-08_s1.2/metadata.csv`
compute_volume: False
Requested variables: ['age', 'sex', 'education', 'clinical_date']

## Coverage by dataset

| dataset | subjects | participants.tsv | missing subjects | missing variables |
|---|---|---|---|---|
| UCL-UK/UCLStrokeData | 4119 | found | — | clinical_date, education |
| UKLFR/stroke_UKLFR | 697 | found | — | — |
| UNIPD/PASPORT | 83 | found | — | clinical_date |
| UNIPD/PSP | 168 | found | — | — |
| UNIPD/WashU | 202 | found | — | — |

## Verdict

**OK** - safe to join (missing-variable gaps above become NaN, not an error).
