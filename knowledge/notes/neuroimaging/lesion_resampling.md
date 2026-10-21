# Ricampionamento e binarizzazione delle maschere di lesione — regola, sfumature, stato in NEMESIS

Come una maschera di lesione arriva sulla griglia di una matrice e diventa 0/1. Implementazione: `src/features/lesion.py` (`_needs_resample`, `_binarize_on_grid`, `load_brain_mask`), `src/features/sdc.py` (`_disconnectome_values`, caso continuo), `src/features/functional.py` (`resample_lesion_to_atlas`, maschera sulla griglia dell'atlante FC). Template, griglie e differenza tra 1 e 2 mm: [`template_and_grids.md`](template_and_grids.md). Le metriche per soggetto calcolate dopo questo passaggio: [`lesion_metrics.md`](lesion_metrics.md).

Il documento è in quattro parti:

- **[Parte 1 — La regola](#parte-1--la-regola)**: quale interpolazione per quale tipo di dato, e perché.
- **[Parte 2 — Il downsampling](#parte-2--il-downsampling)**: cosa fa davvero l'interpolazione quando si riduce la risoluzione, e perché sulle griglie del repo `nearest` e `linear` coincidono.
- **[Parte 3 — Lo stato in NEMESIS](#parte-3--lo-stato-in-nemesis)**: le griglie delle maschere reali, quanto pesa il downsampling, la decisione in vigore.
- **[Parte 4 — La binarizzazione a 0,5](#parte-4--la-binarizzazione-a-05)**: come, quando e dove si soglia, quando la soglia conta, cosa raccomanda la letteratura.

---

# Parte 1 — La regola

## 1. Perché serve un ricampionamento

Le maschere arrivano tutte in MNI152NLin6Asym, $182 \times 218 \times 182$ con voxel di 1 mm, ma con **tre header diversi** (LAS con origine x $+90$, RAS $-90$, RAS $-91$; censimento su tutte e 5853, `docs/guides/datasets.md`). La matrice di produzione è sulla griglia a 2 mm del template, fissata esplicitamente da `reference_template_path` (`assets/templates/tpl-MNI152NLin6Asym_res-2_T1w.nii.gz`). Per impilare le maschere in una matrice soggetti × voxel, ogni colonna deve indicare lo stesso punto fisico per tutti: serve la stessa griglia, non solo lo stesso spazio.

### Griglia, risoluzione e spazio: tre cose diverse

- **Shape** (es. $91 \times 109 \times 91$): quanti voxel ci sono lungo i tre assi.
- **Dimensione del voxel** (es. 2 mm): quanti millimetri misura ogni voxel. Shape, dimensione, origine e orientamento stanno insieme nell'*affine* del file e formano la **griglia**.
- **Spazio** (es. MNI152NLin6Asym): il sistema di coordinate in cui il cervello è stato normalizzato. Due maschere nello stesso spazio possono stare su griglie diverse.

Per questo `_needs_resample` confronta shape **e** affine (tolleranza `_AFFINE_ATOL = 1e-3`), mai la shape da sola: a parità di shape, una maschera LAS letta per indice su una griglia RAS è specchiata sull'asse x, e una RAS $-90$ è traslata di un voxel (`.claude/lessons_learned.md` #40).

## 2. La regola va per tipo di dato, non per direzione

Non conta se si ingrandisce o si riduce la risoluzione: conta **cosa rappresentano i valori**.

| Tipo di dato | Interpolazione | Perché |
|---|---|---|
| Maschere binarie, atlanti, segmentazioni | **`nearest`** | I valori sono etichette, non quantità: un'altra interpolazione produce valori fuori dall'insieme delle etichette |
| T1, BOLD, mappe di probabilità, disconnettoma | `linear` o `continuous` | Il dato è continuo, la media tra due valori vicini è un valore valido |

Il caso che rende la regola evidente è l'**atlante**: interpolare linearmente tra l'etichetta `12` e l'etichetta `47` produce `~30`, una regione che non c'entra con nessuna delle due. Per una maschera binaria il danno è della stessa natura ma più contenuto: valori in $(0, 1)$ che vanno risogliati (Parte 4).

## 3. Riscontro in letteratura e nella documentazione

- Bisogno et al. 2025, sulla stessa coorte UNIPD: *"The normalization matrix was then applied to the lesion mask through a nearest neighbour interpolation function"* [1].
- nilearn, chiamato con `linear` o `continuous` su un'immagine binaria, emette l'avviso *"Resampling binary images with continuous or linear interpolation. This might lead to unexpected results. You might consider using nearest interpolation instead."* (sorgente nilearn 0.14, verificato eseguendo `resample_to_img`) [2].
- FSL descrive per le maschere la ricetta alternativa a due passi, trasformazione e poi nuova soglia (§ 6) [3].

Lo stesso criterio è applicato al riallineamento lesione → griglia dell'atlante FC ([`fc_lesion_masking.md`](fc_lesion_masking.md)).

## 4. Come il repo applica la regola

- `src/features/lesion.py::_binarize_on_grid` — maschera di lesione, interpolazione configurabile (`resample_interpolation`), `nearest` in produzione (`build_lesion_matrix.json`, `compute_lesion_metadata.json`). Una sola funzione per la matrice e per i metadati.
- `src/features/lesion.py::load_brain_mask` — maschera cerebrale, `nearest` **fisso** qualunque sia `resample_interpolation`.
- `src/features/functional.py::resample_lesion_to_atlas` — maschera di lesione sulla griglia dell'atlante FC, ricampionata sempre (anche a parità di shape), `nearest` in produzione (`mask_fc.json`).
- `src/features/sdc.py::_disconnectome_values` — disconnettoma, campo continuo, **mai binarizzato**; `nearest` in produzione per coerenza (`docs/dev/sdc_matrix.md`).

---

# Parte 2 — Il downsampling

## 5. `nearest` in downsampling campiona, non media

Da 1 a 2 mm ogni voxel di destinazione copre il volume di 8 voxel sorgente. `nearest` prende il valore di **uno**, quello più vicino al centro del voxel di destinazione: è un **campionamento**, non un'aggregazione. Per una lesione grande l'effetto è piccolo e non sistematico (§ 9); una lesione più piccola dei punti di campionamento può sparire del tutto.

## 6. L'alternativa classica: interpolazione più soglia

La documentazione FSL indica per trasformare una maschera due passi: (i) trasformarla nel nuovo spazio, ottenendo un'immagine in virgola mobile anche da un input intero; (ii) risogliarla con `fslmaths` per renderla di nuovo binaria [3]. Sulla soglia:

- una soglia vicina a 1 (0,9) è conservativa: entra solo un voxel che si sovrappone per il 90% alla maschera originale;
- una vicina a 0 (0,1) è liberale;
- **0,5 "conserva (approssimativamente) la dimensione della maschera originale"**: entra ogni voxel che si sovrappone alla maschera per il 50% o più;
- la scelta migliore dipende dall'uso: alta per quantificare dentro una ROI senza contaminazione, bassa per una ROI di esclusione con bordo largo [3].

La lettura "valore interpolato = frazione di sovrapposizione" è esatta per una media pesata per area. Per un interpolatore puntuale (che valuta l'interpolante nel centro del voxel di destinazione) è un'approssimazione, che FSL stesso qualifica con "approximately" [3]. Se `flirt`/`applywarp` facciano una media in downsampling **non è verificato**.

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

Il builder solleva solo se **tutti** i soggetti si azzerano: un singolo soggetto a zero è un caso di dominio. La decisione è per soggetto: i primi tre sono in `assets/metadata/excluded_subjects.csv` con `reason=empty_mask`, il quarto con `out_of_brain_fraction_too_high`. Una riga tutta a zero non è innocua: con Jaccard/Dice la distanza tra due vettori nulli è indefinita, e scikit-learn la restituisce come 0.

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

Formalmente, se $m$ è la maschera sorgente e $R_g$ il ricampionamento sulla griglia $g$ (l'identità se la griglia coincide),

$$\ell_g(v) = \mathbb{1}\!\left[(R_g\, m)(v) > \tau_b\right], \qquad \tau_b = 0{,}5 .$$

**Parametri.** `binarize_threshold` (0,5 in produzione) è validato in $[0, 1]$ al caricamento del config (`src/analysis/build_config.py`); il builder solleva se con la soglia scelta tutti i soggetti risultano vuoti (ad esempio $\tau_b = 1$, che con `>` non passa mai). La disuguaglianza è **stretta**: un voxel che vale esattamente 0,5 è scartato.

## 13. Quando la soglia conta

Con `nearest` su una sorgente binaria i valori restano 0 o 1 e `> 0,5` non scarta nulla: la soglia è un controllo che non cambia niente. Conta in due casi:

- **Sorgente frazionaria (PSP).** Le 168 maschere PSP valgono multipli di $1/8$ a 1 mm. Sulla griglia a 1 mm non c'è ricampionamento, e la soglia stretta tiene solo i voxel $> 0{,}5$: `lesion_volume_voxels_1mm` di PSP è in mediana 0,83 volte il volume vero (`docs/dev/metadata.md`). Sulla griglia a 2 mm `nearest` campiona proprio i voxel che coincidono con i centri della griglia originale a 2 mm, che valgono 0 o 1: la matrice e la colonna a 2 mm sono esatte.
- **Un'interpolazione non puntuale su un'altra coppia di griglie.** Con `linear` su griglie i cui centri non coincidono, i valori diventano frazioni e $\tau_b$ diventa la soglia di decisione del § 6.

## 14. Cosa raccomandano letteratura e documentazione

- **Interpolazione `nearest`** per una maschera binaria: Bisogno et al. 2025 [1]; l'avviso di nilearn [2].
- **Trasformazione più soglia, 0,5 per conservare il volume**: FSL [3], con un'avvertenza sul criterio: per FSL entra il voxel che si sovrappone **per il 50% o più**, cioè $\ge 0{,}5$; il repo usa $> 0{,}5$. Le due regole differiscono solo per i voxel che valgono esattamente 0,5, cioè, nei dati attuali, i voxel PSP a $4/8$ sulla griglia a 1 mm.
- **Maschere binarie dopo la normalizzazione** sono la norma nel lesion-symptom mapping [4, 5]; Bisogno et al. 2025 ricampiona a 2 mm e binarizza le lesioni prima di usarle come seme per la disconnessione funzionale [1], senza dichiarare la soglia.
- **BCBToolKit**: il paper non dichiara interpolazione né soglia per le maschere normalizzate [6]. Quale soglia BCBToolKit applichi a una maschera frazionaria come quelle PSP (che riceve con `map_min_nonzero = 0,125`): **fonte non trovata** (`.claude/open_problems.md`).

**Scelta del progetto**: soglia 0,5 con disuguaglianza stretta, dopo il ricampionamento. Allinearsi a FSL ($\ge$) cambierebbe solo le colonne a 1 mm di PSP, già marcate come non affidabili.

## 15. Riferimento rapido

- Config: `config/pipelines/build_lesion_matrix.json`, `compute_lesion_metadata.json`, `mask_fc.json` → `resample_interpolation`, `binarize_threshold`, `reference_template_path`.
- Codice: `src/features/lesion.py` (`_needs_resample`, `_binarize_on_grid`, `load_brain_mask`, `_AFFINE_ATOL`), `src/analysis/build_config.py` (validazione).
- Guida: `docs/guides/matrix_building.md`. Architettura: `docs/dev/lesion_matrix.md`. Caso continuo: `docs/dev/sdc_matrix.md`.

## Fonti

1. Bisogno AL, Pini L, Raccanello S, et al. (2025). Large-scale network topography of stroke predicts functional outcome after mechanical thrombectomy. *Brain Communications*. https://doi.org/10.1093/braincomms/fcaf285 — copia estratta in `knowledge/papers/stroke_core/`.
2. nilearn 0.14, `nilearn.image.resample_to_img` (documentazione: https://nilearn.github.io/stable/modules/generated/nilearn.image.resample_to_img.html) e sorgente `nilearn/image/resampling.py` (avviso su immagini binarie, mappatura `continuous`/`linear`/`nearest` → ordine 3/1/0).
3. FSL, documentazione ufficiale, FLIRT FAQ, "How do I transform a mask with FLIRT from one space to another?". https://fsl.fmrib.ox.ac.uk/fsl/docs/registration/flirt/faq.html (consultato il 21-10-26).
4. Karnath HO, Sperber C, Rorden C (2018). Mapping human brain lesions and their functional consequences. *NeuroImage* 165:180-189. https://doi.org/10.1016/j.neuroimage.2017.10.028
5. Sperber C, Karnath HO (2017). Impact of correction factors in human brain lesion-behavior inference. *Human Brain Mapping* 38:1692-1701. https://doi.org/10.1002/hbm.23490
6. Foulon C, Cerliani L, Kinkingnéhun S, et al. (2018). Advanced lesion symptom mapping analyses and implementation as BCBtoolkit. *GigaScience* 7(3):1-17. https://doi.org/10.1093/gigascience/giy004
