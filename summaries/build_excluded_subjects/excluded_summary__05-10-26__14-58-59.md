# build_excluded_subjects — 05-10-26 14:58:59

file: `assets/metadata/excluded_subjects.csv` · rows: 15 · overwrite: False · lesion measures: `assets/metadata/lesion_metadata.csv`

notes: I soggetti da tenere fuori dalle matrici di produzione, elencati esplicitamente (nessuna soglia: i dati non hanno un salto naturale). Con overwrite false il csv esistente resta com'e' (anche le righe tolte o aggiunte a mano) e le righe di questo config vengono aggiunte; con overwrite true il csv viene ricostruito da questo config soltanto. empty_mask: value dal conteggio nativo a 1 mm di lesion_metadata.csv, che deve valere 0. all_zero_features: la riga di feature e' tutta zero nella rappresentazione dello scope, quindi value 0 per definizione (numero di feature non nulle).

## Righe per motivo, scope e dataset

| reason | scope | dataset | n soggetti |
|---|---|---|---|
| all_zero_features | sdc-streamline | UCL-UK/UCLStrokeData | 13 |
| all_zero_features | sdc-streamline | UNIPD/WashU | 1 |
| empty_mask | all | UKLFR/stroke_UKLFR | 1 |

## Cambiamenti rispetto al file attuale

- 15 of the config's 15 row(s) were already in the file
- 15 unchanged, 0 added, 0 removed
