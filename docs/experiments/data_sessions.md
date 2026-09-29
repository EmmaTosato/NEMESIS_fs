# Sessioni dati

Narrativa su cosa significa ogni sessione, scritta a mano.

`Soggetti` = righe effettive della matrice prodotta (soggetti **ammessi**), non quanti ne esistono su disco: le due cose non coincidono per l'SDC, dove un soggetto entra solo se ha *sia* la maschera registrata nel registro *sia* l'output SDC richiesto. Conteggi verificati sui `metadata.csv` degli artefatti.

## Vocabolario tag di formato

Tag chiuso, condiviso tra track (mai un `_` al suo interno - vedi `src/utils/run_log.py::append_run_log_entry`, che deriva `session` splittando `run_id` sul primo `_`).

| Tag | Significato |
|---|---|
| `vol` | Matrice 2D volumetrica (voxel-wise, non parcellata) — vale per qualunque track: lesione (s1.x) o disconnettoma (s2.x) |
| `stream` | Streamline per tratto (`LF-lesion_atlas-yeh_hcp1065_streamline.csv`), un valore per tratto |
| `schaefer-200-tian-s2` | Parcellato sull'atlante Schaefer-200 + Tian S2 |
| `Yan100TianS1Buckner7N` … `Yan400TianS3Buckner7N` (12 combo) | FC parcellata su uno dei 12 atlas_combo Yan/Tian/Buckner - un tag per combo |

# Session 1

### Session 1.1-vol

- Starting date: 21-07
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR
- Modality: Lesion, voxel-wise
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

### Session 1.4-vol

- Starting date: TBD (data della build)
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UCL-UK StrokeData, UKE/WAKEUP_acute, UNIPD/NEMESIS_T0, UKE/SFB936_ses01
- Modality: Lesion, voxel-wise, griglia 2mm
- Soggetti: 5853
- Notes: rispetto a s1.3-vol, dati mancanti recuperati e due dataset in più (NEMESIS_T0, SFB936_ses01)

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
- Modality: SDC, voxel-wise (mappe `disconnectome-map`, valori continui 0-1)
- Soggetti: 1570
- Notes: primo SDC non parcellato; un dataset in più rispetto a s2.1 (UKE/WAKEUP_acute). Stessa griglia 2mm della track lesionale, quindi allineata voxel per voxel a s1.3-vol

### Session 2.3-stream

- Starting date: TBD (data della build)
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UKE/WAKEUP_acute, UNIPD/NEMESIS_T0, UKE/SFB936_ses01
- Modality: SDC, streamline per tratto (atlante `yeh_hcp1065_streamline`, famiglia `LF-lesion`)
- Soggetti: TBD (dalla matrice prodotta)
- Notes: dati non ancora completi per tutti i soggetti (UCL-UK non ha il CSV streamline), da cui il numero 2.3, che precede 2.4 nell'ordine di lavoro, non nella completezza

### Session 2.4-vol

- Starting date: TBD (data della build)
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UCL-UK StrokeData, UKE/WAKEUP_acute, UNIPD/NEMESIS_T0, UKE/SFB936_ses01
- Modality: SDC, voxel-wise (mappe `disconnectome-map`, valori continui 0-1), griglia 2mm
- Soggetti: 5853
- Notes: speculare a s1.4-vol (stessi 8 dataset, lato disconnettoma); allineata voxel per voxel a s1.4-vol

---

# Session 3
