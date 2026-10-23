# enrich_metadata — 29-09-26 11:13:59

file: `assets/metadata/participants.csv` · fill: False · variables: age, sex, education, lesion_side, NIHSS, clinical_date

lesion_metrics:
```json
{
  "build_matrix_config": "config/pipelines/build_lesion_matrix.json",
  "correct_out_of_brain": false,
  "compute_volume": true,
  "compute_side": true,
  "side_threshold": 0.2
}
```

notes: lesion_volume_config e lesion_side_geometric unificati in un unico blocco lesion_metrics (29-09-26, .claude/history/project_changelog.md) - due flag indipendenti (compute_volume/compute_side) invece di due config separati con lo stesso build_matrix_config duplicato. correct_out_of_brain a false per coerenza con build_lesion_matrix.json (anch'esso a false oggi) - i due vanno accesi insieme, mai uno solo, altrimenti lesion_volume_voxels/lesion_side qui e la matrice di produzione tornerebbero a divergere sullo stesso soggetto. Rimossa la lista excluded_subjects (side_threshold=0.20 calibrato su 1445 soggetti, 97.4% di accordo, vedi knowledge/neuroimaging/lesion_laterality.md): un valore che risultasse inaffidabile in analisi si corregge a mano direttamente in participants.csv, non editando questo config.

## Celle vuote per dataset e variabile

| dataset | soggetti | age | sex | education | lesion_side | NIHSS | clinical_date |
|---|---|---|---|---|---|---|---|
| UCL-UK/UCLStrokeData | 4119 | 632 | 641 | — (assente) | — (assente) | — (assente) | — (assente) |
| UKE/SFB936_ses01 | 56 | 4 | 3 | 56 | 3 | 6 | — (assente) |
| UKE/WAKEUP_acute | 451 | 0 | 0 | 451 | 14 | 0 | — (assente) |
| UKLFR/stroke_UKLFR | 705 | 3 | 3 | 193 | 4 | 10 | 489 |
| UNIPD/NEMESIS_T0 | 76 | 4 | 4 | — (assente) | — (assente) | — (assente) | — (assente) |
| UNIPD/PASPORT | 83 | 0 | 0 | 83 | — (assente) | 0 | — (assente) |
| UNIPD/PSP | 168 | 0 | 0 | 14 | 73 | 3 | 5 |
| UNIPD/WashU | 195 | 1 | 0 | 3 | 33 | 52 | 39 |

## Sostituzioni di colonna applicate

Assunzioni di equivalenza clinica registrate in `VARIABLE_SOURCE_OVERRIDES`, non dedotte:

- **UNIPD/PASPORT**: `NIHSS` letta da `NIHSS_at_presentation`
