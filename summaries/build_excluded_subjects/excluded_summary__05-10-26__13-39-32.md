# build_excluded_subjects — 05-10-26 13:39:32

file: `assets/metadata/excluded_subjects.csv` · rows: 15 · lesion measures: `assets/metadata/lesion_metadata.csv`

notes: La lista dei soggetti tenuti fuori dalle matrici di produzione: e' qui la decisione, il csv e' derivato e non si modifica a mano. Ogni soggetto e' elencato esplicitamente (nessuna soglia: i dati non hanno un salto naturale). empty_mask: value dal conteggio nativo a 1 mm di lesion_metadata.csv, che deve valere 0. all_zero_features: la riga di feature e' tutta zero nella rappresentazione dello scope, quindi value 0 per definizione (numero di feature non nulle).

## Righe per motivo, scope e dataset

| reason | scope | dataset | n soggetti |
|---|---|---|---|
| all_zero_features | sdc-streamline | UCL-UK/UCLStrokeData | 13 |
| all_zero_features | sdc-streamline | UNIPD/WashU | 1 |
| empty_mask | all | UKLFR/stroke_UKLFR | 1 |

## Cambiamenti rispetto al file attuale

- assets/metadata/excluded_subjects.csv has columns ['subject_id', 'dataset', 'reason', 'value'] instead of ['subject_id', 'dataset', 'reason', 'scope', 'value']: replaced as a whole by 15 row(s)
