# compute_sdc_metadata — 06-10-26 19:29:25

output: `assets/metadata/sdc_metadata.csv` (5853 righe)
griglie: 2mm, 1mm · interpolazione: nearest · group_filter: ['ST']

config:
```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome/derivatives",
  "datasets": [
    "UNIPD/WashU",
    "UNIPD/PASPORT",
    "UNIPD/PSP",
    "UKLFR/stroke_UKLFR",
    "UCL-UK/UCLStrokeData",
    "UKE/WAKEUP_acute",
    "UNIPD/NEMESIS_T0",
    "UKE/SFB936_ses01"
  ],
  "group_filter": [
    "ST"
  ],
  "disconnectome_glob": "sdc/*/*_res-1_desc-disconnectome.nii.gz",
  "resample_interpolation": "nearest",
  "grids": {
    "2mm": {
      "reference_template_path": "assets/templates/tpl-MNI152NLin6Asym_res-2_T1w.nii.gz",
      "brain_mask_path": "assets/templates/tpl-MNI152NLin6Asym_res-2_desc-brain_mask.nii.gz"
    },
    "1mm": {
      "reference_template_path": "assets/templates/tpl-MNI152NLin6Asym_res-1_T1w.nii.gz",
      "brain_mask_path": "assets/templates/tpl-MNI152NLin6Asym_res-1_desc-brain_mask.nii.gz"
    }
  },
  "run_notes": "Quanto e' disconnesso ciascun soggetto, in totale: somma delle probabilita' di disconnessione dentro la maschera cerebrale (carico, in voxel pesati per probabilita') e la stessa somma divisa per il numero di voxel cerebrali (media 0-1). Le mappe disconnettoma (res-1) non stanno tutte sullo stesso reticolo: 3 header distinti tra gli 8 dataset (LAS con offset x +90, RAS con -90, RAS con -91 come il template MNI), quindi ogni mappa e' portata sulla griglia col SUO header e non con un flip fisso; a 1mm con nearest ciascun caso e' una rimappatura intera esatta e la somma non cambia; a 2mm nearest e' un sottocampionamento, quindi il carico somma voxel da 8 mm3 e non e' il carico a 1mm diviso 8 (la media sul cervello e' invece confrontabile). Due griglie come per le lesioni, cosi' l'app offre la stessa scelta 1mm/2mm per volume e disconnessione. I voxel fuori dal cervello sono esclusi (mediana 0.80% della massa totale, fino all'8.9% in un caso, misurato su 400 soggetti casuali, e' tractografia che esce dal cervello, non disconnessione): la stessa scelta di correct_out_of_brain per le lesioni. Nessuna esclusione di soggetti: chi scartare lo decide excluded_subjects.csv a valle."
}
```

notes: Quanto e' disconnesso ciascun soggetto, in totale: somma delle probabilita' di disconnessione dentro la maschera cerebrale (carico, in voxel pesati per probabilita') e la stessa somma divisa per il numero di voxel cerebrali (media 0-1). Le mappe disconnettoma (res-1) non stanno tutte sullo stesso reticolo: 3 header distinti tra gli 8 dataset (LAS con offset x +90, RAS con -90, RAS con -91 come il template MNI), quindi ogni mappa e' portata sulla griglia col SUO header e non con un flip fisso; a 1mm con nearest ciascun caso e' una rimappatura intera esatta e la somma non cambia; a 2mm nearest e' un sottocampionamento, quindi il carico somma voxel da 8 mm3 e non e' il carico a 1mm diviso 8 (la media sul cervello e' invece confrontabile). Due griglie come per le lesioni, cosi' l'app offre la stessa scelta 1mm/2mm per volume e disconnessione. I voxel fuori dal cervello sono esclusi (mediana 0.80% della massa totale, fino all'8.9% in un caso, misurato su 400 soggetti casuali, e' tractografia che esce dal cervello, non disconnessione): la stessa scelta di correct_out_of_brain per le lesioni. Nessuna esclusione di soggetti: chi scartare lo decide excluded_subjects.csv a valle.

## Soggetti per dataset

| dataset | soggetti |
|---|---|
| UCL-UK/UCLStrokeData | 4119 |
| UKE/SFB936_ses01 | 56 |
| UKE/WAKEUP_acute | 451 |
| UKLFR/stroke_UKLFR | 705 |
| UNIPD/NEMESIS_T0 | 76 |
| UNIPD/PASPORT | 83 |
| UNIPD/PSP | 168 |
| UNIPD/WashU | 195 |

## Distribuzione (2mm)

- carico (somma delle probabilità, voxel): min=0 · mediana=7538 · max=57916
- media sul cervello (0-1): min=0.0000 · mediana=0.0330 · max=0.2530
- soggetti con carico = 0: 1

## Distribuzione (1mm)

- carico (somma delle probabilità, voxel): min=0 · mediana=60265 · max=463052
- media sul cervello (0-1): min=0.0000 · mediana=0.0330 · max=0.2530
- soggetti con carico = 0: 1

## Esclusi da group_filter

Nessuno.
