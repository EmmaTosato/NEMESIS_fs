# enrich_lesion_metadata — 28-08-26 00:22:27

metadata_path: `data/derived/sdc_matrix/27-08_s2.1/metadata.csv`
compute_volume: False
Requested variables: ['lesion_side', 'NIHSS']

## Coverage by dataset

| dataset | subjects | participants.tsv | missing subjects | missing variables |
|---|---|---|---|---|
| UKLFR/stroke_UKLFR | 673 | found | — | — |
| UNIPD/PASPORT | 83 | found | — | NIHSS, lesion_side |
| UNIPD/PSP | 168 | found | — | — |
| UNIPD/WashU | 195 | found | — | — |

## Verdict

**OK** - safe to join (missing-variable gaps above become NaN, not an error).
