# build_excluded_subjects — 06-10-26 18:14:55

file: `assets/metadata/excluded_subjects.csv` · rows: 22 · overwrite: False · lesion measures: `assets/metadata/lesion_metadata.csv`

notes: I soggetti da tenere fuori dalle matrici di produzione, elencati esplicitamente (nessuna soglia: i dati non hanno un salto naturale). Con overwrite false il csv esistente resta com'e' (anche le righe tolte o aggiunte a mano) e le righe di questo config vengono aggiunte; con overwrite true il csv viene ricostruito da questo config soltanto. empty_mask: value dal conteggio sulla griglia di produzione a 2 mm di lesion_metadata.csv (maschera vuota in produzione: nulla a 1 mm o lesione persa nel ricampionamento), che deve valere 0. sub-STUNIPD0558 e' vuota a 2 mm per lo stesso motivo (100% fuori dal brain) ma e' classificata sotto out_of_brain_fraction_too_high, non qui, perche' quel reason ne spiega la causa. all_zero_features: la riga di feature e' tutta zero nella rappresentazione dello scope, quindi value 0 per definizione (numero di feature non nulle). out_of_brain_fraction_too_high: value da out_of_brain_fraction_2mm (griglia di produzione), soglia di esclusione > 30% (notebooks/exploration/lesion_analysis.ipynb, sezione 'Lesione fuori dal brain').

## Righe per motivo, scope e dataset

| reason | scope | dataset | n soggetti |
|---|---|---|---|
| all_zero_features | sdc-streamline | UCL-UK/UCLStrokeData | 13 |
| all_zero_features | sdc-streamline | UNIPD/WashU | 1 |
| empty_mask | all | UKE/WAKEUP_acute | 2 |
| empty_mask | all | UKLFR/stroke_UKLFR | 1 |
| out_of_brain_fraction_too_high | all | UKE/WAKEUP_acute | 1 |
| out_of_brain_fraction_too_high | all | UKLFR/stroke_UKLFR | 1 |
| out_of_brain_fraction_too_high | all | UNIPD/PASPORT | 3 |

## Cambiamenti rispetto al file attuale

- 15 of the config's 22 row(s) were already in the file
- 15 unchanged, 7 added, 0 removed
- + sub-STUKE0146,UKE/WAKEUP_acute,empty_mask,all,0
- + sub-STUKE0201,UKE/WAKEUP_acute,empty_mask,all,0
- + sub-STUKE0329,UKE/WAKEUP_acute,out_of_brain_fraction_too_high,all,0.4761904761904761
- + sub-STUKLFR0227,UKLFR/stroke_UKLFR,out_of_brain_fraction_too_high,all,0.7631379962192817
- + sub-STUNIPD0516,UNIPD/PASPORT,out_of_brain_fraction_too_high,all,0.9432913765399036
- + sub-STUNIPD0552,UNIPD/PASPORT,out_of_brain_fraction_too_high,all,0.4102254428341385
- + sub-STUNIPD0558,UNIPD/PASPORT,out_of_brain_fraction_too_high,all,1
