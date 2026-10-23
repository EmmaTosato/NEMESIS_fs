# compute_lesion_metadata — 07-10-26 12:08:14

output: `assets/metadata/lesion_metadata.csv` (5853 righe)
griglie: 1mm, 2mm · correct_out_of_brain: True · side_threshold: 0.2 · sede misurata su: 2mm
group_filter: ['ST']

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
  "location": {
    "grid": "2mm",
    "atlases": {
      "cortical": {
        "image_path": "assets/atlases/fsl/HarvardOxford/HarvardOxford-cort-maxprob-thr25-2mm.nii.gz",
        "labels_path": "assets/atlases/fsl/HarvardOxford/HarvardOxford-Cortical.xml"
      },
      "subcortical": {
        "image_path": "assets/atlases/fsl/HarvardOxford/HarvardOxford-sub-maxprob-thr25-2mm.nii.gz",
        "labels_path": "assets/atlases/fsl/HarvardOxford/HarvardOxford-Subcortical.xml"
      },
      "cerebellum": {
        "image_path": "assets/atlases/fsl/Cerebellum/Cerebellum-MNIfnirt-maxprob-thr25-2mm.nii.gz",
        "labels_path": "assets/atlases/fsl/Cerebellum/Cerebellum_MNIfnirt.xml"
      }
    }
  },
  "run_notes": "Tutte le metriche derivate dalle maschere, su due griglie. Le maschere sono a 1 mm nativo (verificato: tutte e 5853, 182x218x182), quindi la griglia 1mm non ricampiona nulla e il suo conteggio e' esatto, mentre la 2mm e' un sottocampionamento nearest in cui una lesione minuscola puo' sparire: confrontare i due volumi distingue una maschera davvero vuota da una lesione persa nel ricampionamento. correct_out_of_brain true: i voxel fuori dalla maschera cerebrale non sono lesione, quindi non vanno contati ne' devono influenzare il lato. out_of_brain_fraction resta misurata sulla maschera grezza, prima dell'azzeramento, perche' serve a decidere chi escludere. side_threshold=0.20 calibrato sulla griglia 2mm su 1445 soggetti con lato clinico (97.4% di accordo, vedi knowledge/neuroimaging/lesion_laterality.md): la stessa soglia e' applicata anche a 1mm, dove non e' ancora stata verificata. location: la sede della lesione (dominante + frazione in sette categorie anatomiche, docs/dev/metadata.md) e' misurata solo sulla griglia 2mm perche' a 1mm non serve; gli atlanti devono essere alla risoluzione di quella griglia."
}
```

notes: Tutte le metriche derivate dalle maschere, su due griglie. Le maschere sono a 1 mm nativo (verificato: tutte e 5853, 182x218x182), quindi la griglia 1mm non ricampiona nulla e il suo conteggio e' esatto, mentre la 2mm e' un sottocampionamento nearest in cui una lesione minuscola puo' sparire: confrontare i due volumi distingue una maschera davvero vuota da una lesione persa nel ricampionamento. correct_out_of_brain true: i voxel fuori dalla maschera cerebrale non sono lesione, quindi non vanno contati ne' devono influenzare il lato. out_of_brain_fraction resta misurata sulla maschera grezza, prima dell'azzeramento, perche' serve a decidere chi escludere. side_threshold=0.20 calibrato sulla griglia 2mm su 1445 soggetti con lato clinico (97.4% di accordo, vedi knowledge/neuroimaging/lesion_laterality.md): la stessa soglia e' applicata anche a 1mm, dove non e' ancora stata verificata. location: la sede della lesione (dominante + frazione in sette categorie anatomiche, docs/dev/metadata.md) e' misurata solo sulla griglia 2mm perche' a 1mm non serve; gli atlanti devono essere alla risoluzione di quella griglia.

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

## Metriche per griglia

### 1mm

- volume (voxel): min=0 · mediana=3445 · max=338044
- maschere vuote (volume = 0): 1
- frazione fuori dal brain: min=0.0000 · mediana=0.0000 · max=0.9994 (calcolata sulla maschera grezza, prima dell'eventuale azzeramento)
- lato: both=75, left=3110, right=2667 · senza lato (indice indefinito): 1

### 2mm

- volume (voxel): min=0 · mediana=434 · max=42279
- maschere vuote (volume = 0): 4
- frazione fuori dal brain: min=0.0000 · mediana=0.0000 · max=1.0000 (calcolata sulla maschera grezza, prima dell'eventuale azzeramento)
- lato: both=68, left=3117, right=2661 · senza lato (indice indefinito): 7

## Sede della lesione (2mm)

senza sede (maschera vuota o tutta fuori dal brain): 4

| categoria | dominante per | frazione media |
|---|---|---|
| infratentorial | 645 | 0.103 |
| subcortical_gray | 507 | 0.114 |
| cortex_only | 1903 | 0.263 |
| cortex_white_boundary | 21 | 0.046 |
| white_matter_only | 2746 | 0.444 |
| ventricle | 0 | 0.004 |
| unlabeled | 27 | 0.026 |

## Esclusi da group_filter

Nessuno.
