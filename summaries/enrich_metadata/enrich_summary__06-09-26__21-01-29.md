# enrich_metadata — 06-09-26 21:01:29

file: `assets/metadata/participants.csv` · fill: False · variables: age, sex, education, lesion_side, NIHSS, clinical_date
lesion_volume_from: data/derived/lesion_matrix/06-09_s1.3-vol
notes: Prima run di enrich_metadata: sostituisce enrich_lesion_metadata, scrive le colonne cliniche direttamente in participants.csv.

## Celle vuote per dataset e variabile

| dataset | soggetti | age | sex | education | lesion_side | NIHSS | clinical_date |
|---|---|---|---|---|---|---|---|
| UCL-UK/UCLStrokeData | 4119 | 632 | 641 | — (assente) | — (assente) | — (assente) | — (assente) |
| UKE/WAKEUP_acute | 451 | 0 | 0 | 451 | 14 | 0 | — (assente) |
| UKLFR/stroke_UKLFR | 729 | 3 | 3 | 200 | 4 | 10 | 502 |
| UNIPD/PASPORT | 83 | 0 | 0 | 83 | — (assente) | 0 | — (assente) |
| UNIPD/PSP | 168 | 0 | 0 | 14 | 73 | 3 | 5 |
| UNIPD/WashU | 202 | 1 | 0 | 3 | 36 | 56 | 42 |

## Sostituzioni di colonna applicate

Assunzioni di equivalenza clinica registrate in `VARIABLE_SOURCE_OVERRIDES`, non dedotte:

- **UNIPD/PASPORT**: `NIHSS` letta da `NIHSS_at_presentation`
