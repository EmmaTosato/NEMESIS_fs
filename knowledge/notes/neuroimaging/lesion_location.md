# Sede della lesione — atlanti e allineamento

Atlanti usati per classificare la sede della lesione e come allinearli alle maschere. Le categorie, le colonne di `lesion_metadata.csv`, la griglia e la popolazione sono del progetto e stanno in `docs/dev/metadata.md` (sezione "La sede della lesione"); decisioni e alternative in `.claude/history/methods_changelog.md`, punti aperti in `.claude/open_problems.md`.

## Atlanti

In `assets/atlases/fsl/` (fonte, versione e licenza nel suo `README.md`), versione `maxprob-thr25`, 1mm e 2mm:

| Atlante | Etichette | Contributo |
|---|---|---|
| Harvard-Oxford corticale | 48 | corticale |
| Harvard-Oxford sotto-corticale | 21 | sotto-corticale grigia, tronco, sostanza bianca, ventricoli |
| Cerebellum-MNIfnirt | 28 | cervelletto |

Il valore del voxel è l'indice dell'XML + 1; gli indici si leggono dall'XML, mai per offset.

## Allineamento

- Gli atlanti sono **LAS**, i template in `assets/templates/` **RAS**; le maschere hanno 3 header diversi (LAS +90, RAS −91, RAS −90, vedi `open_problems.md`). Tutto passa dall'**affine** (`resample_to_img`, `nearest`, come `src/features/lesion.py::_binarize_on_grid`), mai da un flip dell'array.
- Atlante e template a 1mm coincidono con un flip x e offset intero (181 a 1mm, 90 a 2mm): il ricampionamento non perde voxel.
- I controlli di allineamento devono poter fallire: il segno in coordinate mondo del centroide di ogni etichetta Left/Right, verificato con un flip naive come controllo negativo, e il lato dell'atlante contro `lesion_side` di `lesion_metadata.csv`.
- Il volume di `lesion_metadata.csv` è dopo la correzione fuori-brain: il confronto va fatto sui voxel dentro il brain mask.

## Limiti noti

- La fascia corticale di HO è generosa: 109.621 voxel a 1mm sono sia corticali sia `Cerebral White Matter`; il progetto li tiene come categoria a parte, senza assegnarli (`docs/dev/metadata.md`).
- Le maschere PSP sono frazionarie: a 1mm la binarizzazione `> 0,5` ne perde voxel, quindi le frazioni di PSP a 1mm sono indicative.
- Una lesione solo di tronco non ha etichette sinistra/destra nell'atlante.
