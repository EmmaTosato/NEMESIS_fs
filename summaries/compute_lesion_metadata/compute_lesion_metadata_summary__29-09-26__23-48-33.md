# compute_lesion_metadata — 29-09-26 23:48:33

output: `/private/tmp/claude-501/-Users-emmatosato-Local-Projects-Local-PhD-Projects-NEMESIS-fs/0a384f54-25d4-4167-af98-8cc8b07d32c7/scratchpad/lesion_metadata_washu.csv` (195 righe)
griglie: 1mm, 2mm · correct_out_of_brain: True · side_threshold: 0.2
group_filter: ['ST']

config:
```json
{
  "project": "clinical_connectome",
  "data_root": "data/clinical_connectome/derivatives",
  "datasets": [
    "UNIPD/WashU"
  ],
  "group_filter": [
    "ST"
  ],
  "lesion_glob": "manual_masks/*/anat/*_label-lesion_mask.nii.gz",
  "binarize_threshold": 0.5,
  "resample_interpolation": "nearest",
  "grids": {
    "1mm": {
      "reference_template_path": "assets/templates/tpl-MNI152NLin6Asym_res-1_T1w.nii.gz",
      "brain_mask_path": "assets/templates/tpl-MNI152NLin6Asym_res-1_desc-brain_mask.nii.gz"
    },
    "2mm": {
      "reference_template_path": "assets/templates/tpl-MNI152NLin6Asym_res-2_T1w.nii.gz",
      "brain_mask_path": "assets/templates/tpl-MNI152NLin6Asym_res-2_desc-brain_mask.nii.gz"
    }
  },
  "correct_out_of_brain": true,
  "side_threshold": 0.2,
  "run_notes": "Prova di timing su UNIPD/WashU, output nella cartella temporanea: non tocca assets/metadata/lesion_metadata.csv."
}
```

notes: Prova di timing su UNIPD/WashU, output nella cartella temporanea: non tocca assets/metadata/lesion_metadata.csv.

## Soggetti per dataset

| dataset | soggetti |
|---|---|
| UNIPD/WashU | 195 |

## Metriche per griglia

### 1mm

- volume (voxel): min=16 · mediana=15166 · max=267912
- maschere vuote (volume = 0): 0
- frazione fuori dal brain: min=0.0000 · mediana=0.0125 · max=0.3024 (calcolata sulla maschera grezza, prima dell'eventuale azzeramento)
- lato: both=1, left=98, right=96 · senza lato (indice indefinito): 0

### 2mm

- volume (voxel): min=2 · mediana=1863 · max=33113
- maschere vuote (volume = 0): 0
- frazione fuori dal brain: min=0.0000 · mediana=0.0113 · max=0.2794 (calcolata sulla maschera grezza, prima dell'eventuale azzeramento)
- lato: left=98, right=97 · senza lato (indice indefinito): 0

## Esclusi da group_filter

Nessuno.
