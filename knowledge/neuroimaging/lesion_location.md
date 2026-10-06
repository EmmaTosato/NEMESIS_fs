# Sede della lesione (corticale / sotto-corticale / infratentoriale) — atlanti, categorie, regola

Stato: prototipo in `tmp/lesion_location/` (locale, gitignored), non ancora in `src/`. Le decisioni e le alternative scartate stanno in `.claude/history/methods_changelog.md` (06-10-26), i punti aperti in `.claude/open_problems.md`.

## Atlanti

In `assets/atlases/fsl/` (fonte, versione e licenza nel suo `README.md`), versione `maxprob-thr25`, 1mm e 2mm:

| Atlante | Etichette | Contributo |
|---|---|---|
| Harvard-Oxford corticale | 48 | corticale |
| Harvard-Oxford sotto-corticale | 21 | sotto-corticale grigia, tronco, sostanza bianca, ventricoli |
| Cerebellum-MNIfnirt | 28 | cervelletto |

Il valore del voxel è l'indice dell'XML + 1; gli indici si leggono dall'XML, mai per offset.

## Categorie

Sei categorie esclusive per voxel dentro il brain mask, in ordine di precedenza (la prima che reclama il voxel vince):

1. **infratentoriale**: `Brain-Stem` (HO) + cervelletto. Il tronco intero conta infratentoriale, mesencefalo compreso (il tentorio lo taglia, HO non permette di dividerlo).
2. **sotto-corticale grigia**: talamo, caudato, putamen, pallido, ippocampo, amigdala, accumbens (14 etichette HO, sinistra e destra).
3. **corticale**: HO corticale.
4. **sostanza bianca**: `Cerebral White Matter` di HO.
5. **ventricolo**: `Lateral Ventricle` di HO.
6. **non etichettato**: dentro il brain mask ma senza etichetta in nessun atlante.

Per ogni lesione si tengono le frazioni per categoria (quota dei voxel lesionali dentro il brain mask, somma 1) e la quota fuori dal brain mask a parte. Le etichette discrete (coinvolto / puro / misto) si derivano dalle frazioni a soglie esplicite; le soglie non sono ancora fissate (`open_problems.md`).

Anteriore/posteriore non fa parte di questa classificazione.

## Allineamento

- Gli atlanti sono **LAS**, i template in `assets/templates/` **RAS**; le maschere hanno 3 header diversi (LAS +90, RAS −91, RAS −90, vedi `open_problems.md`). Tutto passa dall'**affine** (`resample_to_img`, `nearest`, come `src/features/lesion.py::_binarize_on_grid`), mai da un flip dell'array.
- Atlante e template a 1mm coincidono con un flip x e offset intero (181 a 1mm, 90 a 2mm): il ricampionamento non perde voxel.
- I controlli di allineamento devono poter fallire: il segno in coordinate mondo del centroide di ogni etichetta Left/Right, verificato con un flip naive come controllo negativo, e il lato dell'atlante contro `lesion_side` di `lesion_metadata.csv`.
- Il volume di `lesion_metadata.csv` è dopo la correzione fuori-brain: il confronto va fatto sui voxel dentro il brain mask.

## Limiti noti

- La fascia corticale di HO è generosa: 109.621 voxel a 1mm sono sia corticali sia `Cerebral White Matter`; con la precedenza contano corticali.
- Le maschere PSP sono frazionarie: a 1mm la binarizzazione `> 0,5` ne perde voxel, quindi le frazioni di PSP a 1mm sono indicative.
- Una lesione solo di tronco non ha etichette sinistra/destra nell'atlante.
