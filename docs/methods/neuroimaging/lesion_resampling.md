# Ricampionamento e binarizzazione delle maschere di lesione — regola, sfumature, stato in NEMESIS

> Teoria: [Ricampionamento e binarizzazione delle maschere di lesione — regola, sfumature, stato in NEMESIS](../../../knowledge/concepts/Neuroimaging_Connectivity/lesion_resampling.md) (second brain). Questa nota contiene solo la parte specifica di NEMESIS.

Come una maschera di lesione arriva sulla griglia di una matrice e diventa 0/1. Implementazione: `src/features/lesion.py` (`_needs_resample`, `_binarize_on_grid`, `load_brain_mask`), `src/features/sdc.py` (`_disconnectome_values`, caso continuo), `src/features/functional.py` (`resample_lesion_to_atlas`, maschera sulla griglia dell'atlante FC). Template, griglie e differenza tra 1 e 2 mm: [`template_and_grids.md`](template_and_grids.md). Le metriche per soggetto calcolate dopo questo passaggio: [`lesion_metrics.md`](lesion_metrics.md).

Il documento è in quattro parti:

- **[Parte 1 — La regola](#parte-1--la-regola)**: quale interpolazione per quale tipo di dato, e perché.
- **[Parte 2 — Il downsampling](#parte-2--il-downsampling)**: cosa fa davvero l'interpolazione quando si riduce la risoluzione, e perché sulle griglie del repo `nearest` e `linear` coincidono.
- **[Parte 3 — Lo stato in NEMESIS](#parte-3--lo-stato-in-nemesis)**: le griglie delle maschere reali, quanto pesa il downsampling, la decisione in vigore.
- **[Parte 4 — La binarizzazione a 0,5](#parte-4--la-binarizzazione-a-05)**: come, quando e dove si soglia, quando la soglia conta, cosa raccomanda la letteratura.

---

## 4. Come il repo applica la regola

- `src/features/lesion.py::_binarize_on_grid` — maschera di lesione, interpolazione configurabile (`resample_interpolation`), `nearest` in produzione (`build_lesion_matrix.json`, `compute_lesion_metadata.json`). Una sola funzione per la matrice e per i metadati.
- `src/features/lesion.py::load_brain_mask` — maschera cerebrale, `nearest` **fisso** qualunque sia `resample_interpolation`.
- `src/features/functional.py::resample_lesion_to_atlas` — maschera di lesione sulla griglia dell'atlante FC, ricampionata sempre (anche a parità di shape), `nearest` in produzione (`mask_fc.json`).
- `src/features/sdc.py::_disconnectome_values` — disconnettoma, campo continuo, **mai binarizzato**; `nearest` in produzione per coerenza (`docs/dev/sdc_matrix.md`).

---

## 7. Sulle griglie del repo `nearest` e `linear` coincidono

`nilearn.image.resample_to_img` è un interpolatore **puntuale**: delega a `scipy.ndimage.affine_transform` con ordine 0 (`nearest`), 1 (`linear`) o 3 (`continuous`) (sorgente nilearn 0.14, `nilearn/image/resampling.py`). Nella coppia `res-1` → `res-2` di MNI152NLin6Asym i centri dei voxel a 2 mm cadono esattamente su centri di voxel a 1 mm ([`template_and_grids.md`](template_and_grids.md) § 5). Un interpolante lineare valutato su un centro sorgente restituisce il valore di quel voxel, quindi:

- `linear` produce solo 0 e 1, e coincide con `nearest` voxel per voxel;
- per un header RAS $-91$ il risultato è esattamente `mask[1::2, 0::2, 0::2]`.

Verificato con `resample_to_img` su una maschera sintetica con ciascuno dei tre header reali (LAS $+90$, RAS $-90$, RAS $-91$): output identici. La ricetta "lineare più soglia 0,5" del § 6, eseguita con `resample_to_img`, **non** realizza qui la soglia di maggioranza sul volume parziale: dà lo stesso risultato di `nearest`. Una vera soglia di maggioranza richiederebbe una media pesata per area (ad esempio la media dei 27 voxel a 1 mm con pesi di sovrapposizione), che il repo non implementa.

> `continuous` (spline cubica) può produrre overshoot ai bordi, cioè valori leggermente $< 0$ o $> 1$; sul disconnettoma lascia rumore di arrotondamento nel fondo, ed è il motivo per cui la produzione non la usa (`docs/dev/sdc_matrix.md`).

---

# Parte 3 — Lo stato in NEMESIS

## 8. Le griglie delle maschere reali

Tutte le maschere sono a 1 mm, ma il **dettaglio** non è lo stesso (`docs/guides/datasets.md`, verificato su tutti i 5853 soggetti):

| Dettaglio nativo | Dataset | Soggetti | Valori |
|---|---|---|---|
| reticolo 2 mm (blocchi $2 \times 2 \times 2$ costanti) | UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936 | 5150 | 0/1 |
| 1 mm genuino | PASPORT, WAKEUP | 534 | 0/1 |
| 2 mm interpolata linearmente a 1 mm | PSP | 168 | multipli di $1/8$ |

Le righe sommano 5852: il 5853° soggetto, `sub-STUKLFR0671`, ha la maschera vuota e non è classificabile (`docs/guides/datasets.md`).

Sulla griglia a 2 mm ogni maschera è ricampionata (la shape è diversa). Sulla griglia a 1 mm le maschere RAS $-91$ sono usate così come sono, mentre le LAS $+90$ e RAS $-90$ sono rimappate attraverso l'affine: con `nearest` è una permutazione intera esatta, senza interpolazione di valori ([`lesion_metrics.md`](lesion_metrics.md) § 1.3).

## 9. Quanto pesa il downsampling

Rapporto $N_{1\text{mm}} / (8 N_{2\text{mm}})$, misurato su `assets/metadata/lesion_metadata.csv` (tabella per dataset in [`template_and_grids.md`](template_and_grids.md) § 10):

- **reticolo 2 mm**: esattamente 1 per ogni soggetto con lesione dentro il cervello. Il campionamento legge un voxel per blocco costante e ricostruisce l'originale: nessuna lesione può sparire.
- **1 mm genuino**: mediana 0,999 sia per PASPORT sia per WAKEUP, con dispersione che cresce al calare del volume (WAKEUP da 0,667 a 3,375). Nessun bias sistematico, come atteso da uno stimatore per conteggio di punti ([`template_and_grids.md`](template_and_grids.md) § 9).
- **PSP**: mediana 0,79, ma per un effetto della soglia a 1 mm, non del downsampling (§ 13).

## 10. Le righe tutte a zero

Sulla griglia a 2 mm 4 soggetti su 5853 hanno volume 0 ([`lesion_metrics.md`](lesion_metrics.md) § 2.3):

- `sub-STUKLFR0671`: maschera vuota anche a 1 mm;
- `sub-STUKE0146`, `sub-STUKE0201` (WAKEUP, 1 mm genuino): lesioni reali di 8 e 3 voxel a 1 mm dentro il cervello (la prima ha 16 voxel nel file grezzo, metà fuori dal cervello), perse nel campionamento;
- `sub-STUNIPD0558`: lesione quasi tutta fuori dal cervello.

Il builder solleva solo se **tutti** i soggetti si azzerano: un singolo soggetto a zero è un caso di dominio. La decisione è per soggetto: i primi tre sono in `assets/metadata/excluded_subjects.csv` con `reason=empty_mask`, il quarto con `out_of_brain_fraction_too_high`. Una riga tutta a zero non è innocua: con Jaccard/Dice la distanza tra due vettori nulli è indefinita: scikit-learn/scipy la restituiscono come 0 per Jaccard e come NaN per Dice, mentre `binary_pairwise_distance` del repo (`src/analysis/distances.py`) rifiuta del tutto una riga tutta a zero.

## 11. Decisione in vigore

**`nearest` per ogni maschera binaria.** È lo standard per il tipo di dato (§ 2-3); sulle griglie del repo coincide con `linear` (§ 7), quindi passare a `linear` non cambierebbe nessuna matrice; non introduce bias di volume (§ 9); il costo noto sono due lesioni di pochi voxel a 1 mm genuino. Una soglia di maggioranza vera richiederebbe una media pesata per area, non presente nel repo e non valutata.

---

# Parte 4 — La binarizzazione a 0,5

## 12. Come, quando, dove

**Dove.** `src/features/lesion.py::_binarize_on_grid`, chiamata da `_load_and_binarize_lesion` (matrice, `build_lesion_matrix`) e da `_metrics_on_grid` (metadati, `compute_lesion_metadata`). La maschera cerebrale ha la propria in `load_brain_mask`, con soglia fissa 0,5. L'FC ha la sua in `src/features/functional.py::resample_lesion_to_atlas`, stessa forma.

**Quando e come.** **Dopo** il ricampionamento, sempre, anche quando la maschera non viene ricampionata:

```python
# src/features/lesion.py::_binarize_on_grid
if _needs_resample(img, reference_img):
    img = resample_to_img(img, reference_img, interpolation=resample_interpolation,
                          force_resample=True, copy_header=True)
return (img.get_fdata() > binarize_threshold).ravel()
```

**Parametri.** `binarize_threshold` (0,5 in produzione) è validato in $[0, 1]$ al caricamento del config (`src/analysis/build_config.py`); il builder solleva se con la soglia scelta tutti i soggetti risultano vuoti (ad esempio $\tau_b = 1$, che con `>` non passa mai). La disuguaglianza è **stretta**: un voxel che vale esattamente 0,5 è scartato.

## 15. Riferimento rapido

- Config: `config/pipelines/build_lesion_matrix.json`, `compute_lesion_metadata.json`, `mask_fc.json` → `resample_interpolation`, `binarize_threshold`, `reference_template_path`.
- Codice: `src/features/lesion.py` (`_needs_resample`, `_binarize_on_grid`, `load_brain_mask`, `_AFFINE_ATOL`), `src/analysis/build_config.py` (validazione).
- Guida: `docs/guides/matrix_building.md`. Architettura: `docs/dev/lesion_matrix.md`. Caso continuo: `docs/dev/sdc_matrix.md`.

## Righe tolte dalla nota teorica (rimandi, dati e confronti del progetto)

Le maschere arrivano tutte in MNI152NLin6Asym, $182 \times 218 \times 182$ con voxel di 1 mm, ma con **tre header diversi** (LAS con origine x $+90$, RAS $-90$, RAS $-91$; censimento su tutte e 5853, `docs/guides/datasets.md`). La matrice di produzione è sulla griglia a 2 mm del template, fissata esplicitamente da `reference_template_path` (`assets/templates/tpl-MNI152NLin6Asym_res-2_T1w.nii.gz`). Per impilare le maschere in una matrice soggetti × voxel, ogni colonna deve indicare lo stesso punto fisico per tutti: serve la stessa griglia, non solo lo stesso spazio.

Per questo `_needs_resample` confronta shape **e** affine (tolleranza `_AFFINE_ATOL = 1e-3`), mai la shape da sola: a parità di shape, una maschera LAS letta per indice su una griglia RAS è specchiata sull'asse x, e una RAS $-90$ è traslata di un voxel (`.claude/lessons_learned.md` #40).

- Bisogno et al. 2025, sulla stessa coorte UNIPD: *"The normalization matrix was then applied to the lesion mask through a nearest neighbour interpolation function"* [1].

Lo stesso criterio è applicato al riallineamento lesione → griglia dell'atlante FC ([`fc_lesion_masking.md`](fc_lesion_masking.md)).

Da 1 a 2 mm ogni voxel di destinazione copre il volume di 8 voxel sorgente. `nearest` prende il valore di **uno**, quello più vicino al centro del voxel di destinazione: è un **campionamento**, non un'aggregazione. Per una lesione grande l'effetto è piccolo e non sistematico (§ 9); una lesione più piccola dei punti di campionamento può sparire del tutto.

Con `nearest` su una sorgente binaria i valori restano 0 o 1 e `> 0,5` non scarta nulla: la soglia è un controllo che non cambia niente. Conta in due casi:

- **Sorgente frazionaria (PSP).** Le 168 maschere PSP valgono multipli di $1/8$ a 1 mm. Sulla griglia a 1 mm non c'è ricampionamento, e la soglia stretta tiene solo i voxel $> 0{,}5$: `lesion_volume_voxels_1mm` di PSP è in mediana 0,83 volte il volume vero (`docs/dev/metadata.md`). Sulla griglia a 2 mm `nearest` campiona proprio i voxel che coincidono con i centri della griglia originale a 2 mm, che valgono 0 o 1: la matrice e la colonna a 2 mm sono esatte.

- **Trasformazione più soglia, 0,5 per conservare il volume**: FSL [3], con un'avvertenza sul criterio: per FSL entra il voxel che si sovrappone **per il 50% o più**, cioè $\ge 0{,}5$; il repo usa $> 0{,}5$. Le due regole differiscono solo per i voxel che valgono esattamente 0,5, cioè, nei dati attuali, i voxel PSP a $4/8$ sulla griglia a 1 mm.

- **BCBToolKit**: il paper non dichiara interpolazione né soglia per le maschere normalizzate [6]. Quale soglia BCBToolKit applichi a una maschera frazionaria come quelle PSP (che riceve con `map_min_nonzero = 0,125`): **fonte non trovata** (`.claude/open_problems.md`).

**Scelta del progetto**: soglia 0,5 con disuguaglianza stretta, dopo il ricampionamento. Allinearsi a FSL ($\ge$) cambierebbe solo le colonne a 1 mm di PSP, già marcate come non affidabili.

1. Bisogno AL, Pini L, Raccanello S, et al. (2025). Large-scale network topography of stroke predicts functional outcome after mechanical thrombectomy. *Brain Communications*. https://doi.org/10.1093/braincomms/fcaf285 — copia estratta in `knowledge/papers/stroke_core/`.

3. FSL, documentazione ufficiale, FLIRT FAQ, "How do I transform a mask with FLIRT from one space to another?". https://fsl.fmrib.ox.ac.uk/fsl/docs/registration/flirt/faq.html (consultato il 21-10-26).
