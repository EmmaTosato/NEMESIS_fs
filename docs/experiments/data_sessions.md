

Narrativa su cosa significa ogni sessione  scritta a mano.

`Soggetti` = righe effettive della matrice prodotta (soggetti **ammessi**), non quanti ne esistono su disco: le due cose non coincidono per l'SDC, dove un soggetto entra solo se ha *sia* la maschera registrata nel registro *sia* l'output SDC richiesto. Conteggi verificati sui `metadata.csv` degli artefatti.

## Vocabolario tag di formato

Tag chiuso, condiviso tra track (mai un `_` al suo interno - vedi `src/utils/run_log.py::append_run_log_entry`, che deriva `session` splittando `run_id` sul primo `_`).

| Tag | Significato |
|---|---|
| `vol` | Matrice 2D volumetrica (voxel-wise, non parcellata) — vale per qualunque track: lesione (s1.x) o disconnettoma (s2.x) |
| `schaefer-200-tian-s2` | Parcellato sull'atlante Schaefer-200 + Tian S2 |
| `Yan100TianS1Buckner7N` … `Yan400TianS3Buckner7N` (12 combo) | FC parcellata su uno dei 12 atlas_combo Yan/Tian/Buckner - un tag per combo, vedi Session 3 sotto |

# Session 1

### Session 1.1-vol

- Starting date: 21-07
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR
- Modality: Lesionm voxel-wise
- Soggetti: 1150

### Session 1.2-vol

- Starting date: 27-07
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UCL-UK StrokeData
- Modality: Lesion, voxel-wise
- Soggetti: 5269
- Notes: one dataset more (UCL-UK StrokeData)

### Session 1.3-vol

- Starting date: 06-09
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UCL-UK StrokeData, UKE/WAKEUP_acute
- Modality: Lesion, voxel-wise
- Soggetti: 5720
- Notes: one dataset more (UKE/WAKEUP_acute, 451 soggetti)

---

# Session 2

### Session 2.1-schaefer-200-tian-s2

- Starting date: 26-08
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR
- Modality: SDC, parcellata (atlante schaefer_200_tian_s2)
- Soggetti: 1119

### Session 2.2-vol

- Starting date: 07-09
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UKE/WAKEUP_acute
- Modality: SDC, voxel-wise (mappe `disconnectome-map` non parcellate, valori continui 0-1)
- Soggetti: 1570
- Notes: primo SDC non parcellato; un dataset in più rispetto a s2.1 (UKE/WAKEUP_acute). Stessa griglia 2mm della track lesionale, quindi allineata voxel per voxel a s1.3-vol

---

# Session 3

FC, un'entry per atlas_combo (`mask_fc.py`/`build_fc_matrix.py` processano tutti e 12 i combo in un solo run, ognuno nella sua sottocartella - vedi `docs/dev/fc_matrix.md`). Stessa coorte/datasets per tutti e 12.

### Session 3.1-Yan100TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan100TianS1Buckner7N)
- Soggetti: 169

### Session 3.1-Yan100TianS2Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan100TianS2Buckner7N)
- Soggetti: 169

### Session 3.1-Yan100TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan100TianS3Buckner7N)
- Soggetti: 169

### Session 3.1-Yan200TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan200TianS1Buckner7N)
- Soggetti: 169

### Session 3.1-Yan200TianS2Buckner7N

- Starting date: 24-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan200TianS2Buckner7N)
- Soggetti: 169
- Notes: prima combo processata (data reale diversa dalle altre 11, mai riconciliata)

### Session 3.1-Yan200TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan200TianS3Buckner7N)
- Soggetti: 169

### Session 3.1-Yan300TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan300TianS1Buckner7N)
- Soggetti: 169

### Session 3.1-Yan300TianS2Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan300TianS2Buckner7N)
- Soggetti: 169

### Session 3.1-Yan300TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan300TianS3Buckner7N)
- Soggetti: 169

### Session 3.1-Yan400TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan400TianS1Buckner7N)
- Soggetti: 169

### Session 3.1-Yan400TianS2Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan400TianS2Buckner7N)
- Soggetti: 169

### Session 3.1-Yan400TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan400TianS3Buckner7N)
- Soggetti: 169
