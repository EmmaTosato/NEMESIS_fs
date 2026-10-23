# enrich_metadata — 06-10-26 19:50:02

file: `assets/metadata/participants.csv` · fill: False · variables: age, sex, education, lesion_side, NIHSS, clinical_date

lesion_metadata:
```json
{
  "path": "assets/metadata/lesion_metadata.csv",
  "copy_columns": [
    "lesion_volume_voxels_2mm",
    "lesion_volume_voxels_1mm"
  ],
  "lesion_side_from": "lesion_side_2mm",
  "geometric_override_datasets": []
}
```

sdc_metadata:
```json
{
  "path": "assets/metadata/sdc_metadata.csv",
  "copy_columns": [
    "disconnection_load_voxels_2mm",
    "disconnection_mean_2mm",
    "disconnection_load_voxels_1mm",
    "disconnection_mean_1mm"
  ]
}
```

notes: enrich_metadata e' un join, non calcola nulla dalle maschere: i valori derivati dalle maschere arrivano da assets/metadata/lesion_metadata.csv (src.pipeline.compute_lesion_metadata), che possiede ogni scelta su COME una maschera e' misurata (griglie, azzeramento fuori dal brain, soglia del lato). copy_columns copia con lo stesso nome per tutti i soggetti in scope, sovrascrivendo. lesion_side_from riempie lesion_side solo dove la risoluzione clinica ha lasciato la cella vuota, scrivendo lesion_side_source=geometric, e registra da quale griglia viene il lato del registro (il csv ne ha uno per griglia). Un valore clinico non viene sovrascritto: geometric_override_datasets e' vuoto (la forzatura del lato geometrico sui dataset elencati resta disponibile ma e' spenta: per WashU i test indipendenti dal lato indicano che l'etichetta clinica e' piu' spesso quella giusta, docs/guides/metadata.md). Le colonne derivate dalle maschere non si correggono a mano: ogni run le ricopia, un valore inaffidabile si sistema sulla maschera o il soggetto va in assets/metadata/excluded_subjects.csv. sdc_metadata e' lo stesso tipo di join per la disconnessione: copia carico e media sul cervello da assets/metadata/sdc_metadata.csv (src.pipeline.compute_sdc_metadata), contro il flag has_sdc invece di has_lesion.

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
