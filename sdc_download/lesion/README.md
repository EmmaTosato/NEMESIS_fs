# sdc_download/lesion/

Copia locale delle maschere di lesione (`label-lesion_mask.nii.gz`) ricampionate
da BCBToolKit come input al proprio calcolo SDC — sorgente:
`Clinical_connectome/features/Clinical_connectome_stroke/<dataset>/lesion/{subject_id}/...`
sul server (stesso `project_root` di `sdc`, vedi `docs/dev/retrieval.md`).

Struttura: `<dataset>/<sub-ID>/<sub-ID>_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`.

Copertura: 1602 soggetti su 5 dataset (168 UNIPD/PSP, 195 UNIPD/WashU, 83
UNIPD/PASPORT, 705 UKLFR/stroke_UKLFR, 451 UKE/WAKEUP_acute), 0 mancanti.
UCL-UK escluso: nessuna cartella `lesion` per UCL-UK esiste sul server sotto
`Clinical_connectome/features/Clinical_connectome_stroke`.

## Re-naming (04/09/26)

Alla copia, ogni file aveva il segmento `res-1` nel nome
(`..._res-1_label-lesion_mask.nii.gz`), come nel leaf `sdc.dwi.lesion-map` di
`file_patterns_local.json`. È stato rimosso da tutti i 1602 file
(`..._label-lesion_mask.nii.gz`) per uniformare il naming a quello già usato
in `data/clinical_connectome/derivatives/<dataset>/manual_masks/<sub-ID>/anat/`.

**Solo il nome del file è cambiato — il contenuto (voxel, affine, shape) non è
stato toccato.** Questi file restano a 1mm isotropico (182×218×182) per tutti
e 5 i dataset, non ancora ricampionati/uniformati alla risoluzione nativa di
`manual_masks/`, che varia per dataset (1mm per UKE/PASPORT/PSP, 1.5mm per
UKLFR, 2mm per WashU — vedi la conversazione che ha portato a questo
re-naming per il dettaglio). Nessuna sostituzione dei file in `manual_masks/`
è stata fatta: questa cartella resta una copia separata, non ancora unita a
`data/`.

## Confronto con `data/clinical_connectome/derivatives/<dataset>/manual_masks/` (04/09/26)

Dopo il re-naming sopra, i filename combaciano esattamente tra le due
cartelle. Confronto soggetto-per-soggetto e voxel-per-voxel (tutti i
soggetti, non un campione):

| Dataset | `manual_masks/` | qui | Solo in `manual_masks` | Solo qui | Contenuto |
|---|---|---|---|---|---|
| UKE/WAKEUP_acute | 451 | 451 | 0 | 0 | **451/451 identici** (voxel+affine, 1mm) |
| UNIPD/PASPORT | 83 | 83 | 0 | 0 | **83/83 identici** |
| UNIPD/PSP | 168 | 168 | 0 | 0 | **168/168 identici** |
| UKLFR/stroke_UKLFR | 697 | 705 | 24 | 32 | **Diversi**: `manual_masks` a 1.5mm (121×145×121) vs qui a 1mm (182×218×182) |
| UNIPD/WashU | 202 | 195 | 7 | 0 | **Diversi**: `manual_masks` a 2mm (91×109×91) vs qui a 1mm (182×218×182) |

- **UKE/PASPORT/PSP**: stessa identica maschera (verificato array voxel + affine
  su tutti i soggetti) — solo il checksum SHA256 del file grezzo differisce
  (metadati header/contenitore gzip, non i dati).
- **UKLFR (24 solo in `manual_masks`) e WashU (7 solo in `manual_masks`)**:
  soggetti ST con maschera manuale ma nessun dato SDC — lacuna nota, non
  introdotta da questo download.
- **UKLFR (32 solo qui)**: soggetti con dati in `sdc/` ma senza voce in
  `manual_masks/` — tra questi `sub-STUKLFR0005`, già noto (`docs/dev/sdc_matrix.md`)
  come assente dal registro `participants.tsv`, non solo "non recuperato
  localmente".
- **UKLFR e WashU**: qui la risoluzione è più fine (1mm) di quella nativa già
  in `manual_masks/` (1.5mm/2mm) — nessuna sostituzione fatta, vedi sopra.
