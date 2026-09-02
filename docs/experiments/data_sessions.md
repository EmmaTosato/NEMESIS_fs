

Narrativa su cosa significa ogni sessione  scritta a mano.

## Vocabolario tag di formato

Tag chiuso, condiviso tra track (mai un `_` al suo interno - vedi `src/utils/run_log.py::append_run_log_entry`, che deriva `session` splittando `run_id` sul primo `_`).

| Tag | Significato |
|---|---|
| `vol` | Lesione in matrice 2D volumetrica (voxel-wise, non parcellata) |
| `schaefer-200-tian-s2` | Parcellato sull'atlante Schaefer-200 + Tian S2 |
| `Yan100TianS1Buckner7N` … `Yan400TianS3Buckner7N` (12 combo) | FC parcellata su uno dei 12 atlas_combo Yan/Tian/Buckner - un tag per combo, vedi Session 3 sotto |

# Session 1

### Session 1.1-vol

- Starting date: 21-07
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR
- Modality: Lesion in 2D matrix volumetric

### Session 1.2-vol

- Starting date: 27-07
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UCL-UK StrokeData
- Modality: Lesion in 2D matrix volumetric
- Notes: one dataset more (UCL-UK StrokeData)

---

# Session 2

### Session 2.1-schaefer-200-tian-s2

- Starting date: 26-08
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR
- Modality: SDC, parcellata (atlante schaefer_200_tian_s2)

---

# Session 3

FC, un'entry per atlas_combo (`mask_fc.py`/`build_fc_matrix.py` processano tutti e 12 i combo in un solo run, ognuno nella sua sottocartella - vedi `docs/dev/fc_matrix.md`). Stessa coorte/datasets per tutti e 12.

### Session 3.1-Yan100TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan100TianS1Buckner7N)

### Session 3.1-Yan100TianS2Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan100TianS2Buckner7N)

### Session 3.1-Yan100TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan100TianS3Buckner7N)

### Session 3.1-Yan200TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan200TianS1Buckner7N)

### Session 3.1-Yan200TianS2Buckner7N

- Starting date: 24-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan200TianS2Buckner7N)
- Notes: prima combo processata (data reale diversa dalle altre 11, mai riconciliata)

### Session 3.1-Yan200TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan200TianS3Buckner7N)

### Session 3.1-Yan300TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan300TianS1Buckner7N)

### Session 3.1-Yan300TianS2Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan300TianS2Buckner7N)

### Session 3.1-Yan300TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan300TianS3Buckner7N)

### Session 3.1-Yan400TianS1Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan400TianS1Buckner7N)

### Session 3.1-Yan400TianS2Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan400TianS2Buckner7N)

### Session 3.1-Yan400TianS3Buckner7N

- Starting date: 27-07
- Datasets: UNIPD/WashU
- Modality: FC, parcellata (atlas_combo Yan400TianS3Buckner7N)
