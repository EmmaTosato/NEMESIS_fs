# enrich_lesion_metadata — 26-08-26 11:11:07

metadata_path: `data/derived/lesion_matrix/25-08_s1.2/metadata.csv`
compute_volume: False
Requested variables: ['lesion_side', 'NIHSS']

## Coverage by dataset

| dataset | subjects | participants.tsv | missing subjects | missing variables |
|---|---|---|---|---|
| UCL-UK/UCLStrokeData | 4119 | found | — | NIHSS, lesion_side |
| UKLFR/stroke_UKLFR | 697 | found | — | — |
| UNIPD/PASPORT | 83 | found | — | NIHSS, lesion_side |
| UNIPD/PSP | 168 | found | — | — |
| UNIPD/WashU | 202 | found | — | — |

## Verdict

**OK** - safe to join (missing-variable gaps above become NaN, not an error).
