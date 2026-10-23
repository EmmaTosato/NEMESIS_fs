# enrich_metadata — 28-09-26 23:53:09

file: `assets/metadata/participants.csv` · fill: False · variables: age, sex, education, lesion_side, NIHSS, clinical_date
lesion_volume_config: config/pipelines/build_lesion_matrix.json
notes: lesion_volume_voxels ora ricalcolato fresco dalle maschere (config/pipelines/build_lesion_matrix.json, griglia 2mm) invece di essere copiato da un artefatto build_lesion_matrix.py specifico - vedi .claude/history/methods_changelog.md, 28-09-26. Aggiunto anche il fallback geometrico per lesion_side (soglia 0.20, calibrata su 1445 soggetti con etichetta clinica, 97.4% di accordo - vedi knowledge/neuroimaging/lesion_laterality.md). build_matrix_config condivide lo stesso build_lesion_matrix.json di lesion_volume_config, la cui lista 'datasets' non copre ancora UKE/SFB936_ses01/UNIPD/NEMESIS_T0 - per quei due il fallback resta silenziosamente disattivo (WARNING nel log) finché quella lista non viene estesa.

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
