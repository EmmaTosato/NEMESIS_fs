# Metriche per soggetto dalle maschere di lesione

Come il repo misura ogni maschera di lesione, a livello di sezione Metodi: definizione, formula, algoritmo, casi limite, giustificazione e limiti. Tutte le metriche sono calcolate da `src/pipeline/compute_lesion_metadata.py` e scritte in `assets/metadata/lesion_metadata.csv`, una riga per soggetto con maschera, nessuna esclusione applicata.

## Indice delle metriche

| Metrica | Colonne | Nota |
|---|---|---|
| Volume | `lesion_volume_voxels_<g>` | questa nota, [§2](#2-volume) |
| Frazione fuori dal cervello | `out_of_brain_fraction_<g>` | questa nota, [§3](#3-frazione-fuori-dal-cervello) |
| Lato | `laterality_index_<g>`, `lesion_side_<g>` | [`lesion_laterality.md`](lesion_laterality.md) |
| Sede | `location_dominant_2mm`, `location_<categoria>_2mm` | [`lesion_location.md`](lesion_location.md) |

`<g>` è il nome della griglia: `1mm` e `2mm` in produzione. Come le maschere arrivano sulla griglia a 2 mm è in [`lesion_resampling.md`](lesion_resampling.md). Schema del csv e ruolo nel registro: `docs/dev/metadata.md`.

---

## 1. Passaggi comuni a tutte le metriche

### 1.1 Notazione

| Simbolo | Significato |
|---|---|
| $g$ | una griglia di `grids` in `config/pipelines/compute_lesion_metadata.json` |
| $\Omega_g$ | l'insieme dei voxel della griglia: $182 \times 218 \times 182$ a 1 mm, $91 \times 109 \times 91$ a 2 mm |
| $\Delta_g$ | il lato del voxel: 1 mm oppure 2 mm |
| $A_g$ | l'affine del template di riferimento della griglia (`reference_template_path`) |
| $B_g(v) \in \{0,1\}$ | la maschera cerebrale della griglia (`brain_mask_path`) |
| $M$ | la maschera di lesione così come è su disco, con il proprio affine $A_M$ |
| $\tau_b$ | `binarize_threshold`, 0,5 in produzione |

Le due griglie sono quelle del template `MNI152NLin6Asym` di TemplateFlow [1], cioè il template MNI ICBM 152 non lineare di 6ª generazione asimmetrico distribuito con FSL [2, 3]: `tpl-MNI152NLin6Asym_res-1_T1w.nii.gz` (origine x = −91 mm) e `res-2` (origine x = −90 mm), entrambi RAS. La maschera cerebrale è il file `desc-brain_mask` di TemplateFlow sulla stessa griglia del template (stesso affine, valori 0/1): 1.827.243 voxel a 1 mm, 228.483 a 2 mm. Come TemplateFlow abbia derivato quella maschera: **fonte non trovata**.

### 1.2 Algoritmo, per ogni soggetto e ogni griglia

Codice: `src/features/lesion.py::compute_lesion_metadata` → `_metrics_on_grid`.

1. **Lettura.** La maschera è letta da disco una volta sola e riusata per tutte le griglie.
2. **Allineamento** (`_binarize_on_grid`, `_needs_resample`). Se shape **o** affine della maschera differiscono da quelli della griglia, la maschera è ricampionata sulla griglia attraverso gli affine con `nilearn.image.resample_to_img`, interpolazione `resample_interpolation` (`nearest` in produzione). Altrimenti è usata così com'è.
3. **Binarizzazione.**
   $$\ell_g(v) = \mathbb{1}\left[\tilde M_g(v) > \tau_b\right], \quad v \in \Omega_g$$
   dove $\tilde M_g$ è la maschera dopo il passo 2. La disuguaglianza è stretta: un voxel che vale esattamente 0,5 è scartato.
4. **Frazione fuori dal cervello** misurata su $\ell_g$, la maschera **prima** della correzione (§3).
5. **Correzione** (`correct_out_of_brain: true` in produzione; `src/features/lesion_correction.py::zero_out_of_brain_voxels`):
   $$\ell^{*}_g(v) = \ell_g(v)\, B_g(v)$$
   Con `correct_out_of_brain: false`, $\ell^{*}_g = \ell_g$.
6. **Volume, lato e sede** contati su $\ell^{*}_g$, la maschera **dopo** la correzione.

L'ordine dei passi 4-6 è una **scelta del progetto** ([`.claude/history/methods_changelog.md`](../../../.claude/history/methods_changelog.md), voce del 29-09-26 "Metriche dalle maschere: quattro per griglia, su due griglie, con la correzione applicata prima del conteggio"): misurata dopo la correzione, la frazione varrebbe 0 per costruzione; un voxel fuori dal cervello non è tessuto cerebrale lesionato, quindi non entra nel volume né decide il lato.

### 1.3 Le maschere non sono tutte sullo stesso reticolo

Tutte le 5853 maschere sono $182 \times 218 \times 182$ con voxel di 1 mm, ma con tre header diversi: LAS con origine x = +90, RAS con origine −90, RAS con origine −91 (censimento su tutta la coorte, `.claude/lessons_learned.md` #40). Solo il terzo coincide con il template a 1 mm. Gli altri due differiscono per un'inversione dell'asse x o per una traslazione di un voxel. Il passo 2 li porta sulla griglia attraverso l'affine: con `nearest` è una rimappatura intera esatta, nessun valore è interpolato. Una sola fetta può cadere fuori dal campo: per l'header RAS −90 la fetta a x = +91 mm, che la griglia a 1 mm (x da −91 a +90) non contiene.

---

## 2. Volume

### 2.1 Definizione

Il numero di voxel di lesione dentro la maschera cerebrale, sulla griglia $g$. Colonna `lesion_volume_voxels_<g>`, intero.

$$V_g = \sum_{v \in \Omega_g} \ell^{*}_g(v) \quad [\text{voxel}]$$

Codice: `int(lesion.sum())` in `src/features/lesion.py::_metrics_on_grid`, dopo la correzione.

Il csv conserva i voxel, non i mm³. La conversione è

$$V_g^{\text{mm}^3} = \Delta_g^{3}\, V_g, \qquad \Delta_{1\text{mm}}^3 = 1\ \text{mm}^3, \quad \Delta_{2\text{mm}}^3 = 8\ \text{mm}^3$$

e in ml si divide per 1000.

### 2.2 Perché due griglie

- **2 mm** è la griglia delle matrici di produzione. Con `nearest` ogni voxel a 2 mm prende il valore del **solo** voxel a 1 mm che ha il suo stesso centro (le origini, −90 e −91 mm, fanno coincidere i centri): è un campionamento di un punto ogni otto, non una media. Il voxel a 2 mm è sfasato di mezzo voxel rispetto ai blocchi 2×2×2, quindi si sovrappone parzialmente a 27 voxel a 1 mm, con pesi che sommano a 8 ([`template_and_grids.md`](template_and_grids.md)). Quindi $V_{2\text{mm}} \neq V_{1\text{mm}}/8$ in generale, e una lesione di pochi voxel può ridursi o sparire.
- **1 mm** è la risoluzione delle maschere su disco, quindi lì il conteggio non perde voxel per sottocampionamento.

Le due colonne insieme distinguono una maschera vuota nel file da una lesione persa nel ricampionamento. Numeri per dataset (per quali dataset le due griglie coincidono, il caso PSP): `docs/dev/metadata.md`, sezione "Perché due griglie, e perché il calcolo è in streaming".

### 2.3 Casi limite

| Caso | Valore |
|---|---|
| Maschera senza voxel sopra $\tau_b$ | $V_g = 0$, un valore vero, non un errore |
| Lesione tutta fuori dal cervello | $V_g = 0$ dopo la correzione |
| Ogni soggetto della coorte a 0 su una griglia | la run solleva `ValueError` (`_check_some_mask_is_non_empty`): indica una soglia o una maschera cerebrale sbagliate |

Nel csv attuale: 1 soggetto a 0 voxel a 1 mm, 4 a 2 mm. Dei 4, uno ha la maschera vuota, due hanno una lesione reale di 8 e 3 voxel a 1 mm persa a 2 mm, uno ha la lesione quasi tutta fuori dal cervello.

### 2.4 Giustificazione

- Contare i voxel della maschera segmentata è la pratica degli studi del laboratorio: Corbetta et al. 2015 usano il numero di voxel della lesione anche come denominatore delle quote di sede, "number voxels in the lesion overlapping with each mask/total number of voxels in the lesion" [4]; Salvalaggio et al. 2020 riportano il volume medio in cm³ [5]. ATLAS riporta il volume in mm³ [6].
- Il volume dopo la correzione è una **scelta del progetto** (§1.2).

### 2.5 Limiti

- Il volume è misurato nello spazio MNI, sulle maschere già normalizzate a monte del repo (`manual_masks/`, `docs/guides/datasets.md`), non nello spazio nativo del paziente. La normalizzazione deforma i volumi, quindi $V_g$ è un volume in spazio standard, non il volume anatomico della lesione.
- Le maschere PSP sono frazionarie a 1 mm (multipli di 1/8): con $\tau_b = 0{,}5$ la colonna a 1 mm di PSP sottostima il volume, quella a 2 mm è esatta (`docs/dev/metadata.md`).
- Con `correct_out_of_brain` attivo il volume dipende dalla maschera cerebrale scelta: una maschera più stretta toglie più voxel di bordo.

---

## 3. Frazione fuori dal cervello

### 3.1 Definizione

La quota dei voxel di lesione che cadono fuori dalla maschera cerebrale del template, misurata **prima** della correzione. Colonna `out_of_brain_fraction_<g>`, adimensionale in $[0, 1]$.

$$f_g = \frac{\sum_{v \in \Omega_g} \ell_g(v)\,\bigl(1 - B_g(v)\bigr)}{\sum_{v \in \Omega_g} \ell_g(v)}, \qquad f_g = \text{NaN se } \sum_v \ell_g(v) = 0$$

Codice: `src/features/lesion.py::_out_of_brain_fraction`, chiamata in `_metrics_on_grid` su `lesion` prima di `zero_out_of_brain_voxels`.

Con quale maschera e su quale griglia: la `desc-brain_mask` di TemplateFlow della griglia stessa (§1.1), una per griglia. La maschera cerebrale è caricata da `load_brain_mask`: è ricampionata sulla griglia con `nearest` solo se shape o affine differiscono (in produzione coincidono) e binarizzata con `> 0,5`.

### 3.2 Casi limite

| Caso | Valore | Motivo |
|---|---|---|
| Lesione tutta dentro il cervello | $f_g = 0$ | |
| Lesione tutta fuori | $f_g = 1$; dopo la correzione $V_g = 0$ e lato e sede sono `NaN` | |
| Maschera vuota | `NaN`, mai 0 | "nessun voxel fuori" e "nessun voxel" sono fatti diversi: 0 metterebbe una maschera vuota tra i soggetti più puliti della distribuzione usata per scegliere le esclusioni (**scelta del progetto**, voce del 29-09-26 citata sopra) |

### 3.3 A cosa serve

Una maschera di lesione in spazio MNI che esce dal cervello del template è un segnale di qualità. Il numero non dice da dove venga l'errore; le cause possibili sono tre e la metrica non le distingue:

- **normalizzazione**: il cervello del paziente non è stato portato bene sul template. La normalizzazione di un cervello lesionato è un passo delicato: per questo il tessuto lesionato viene mascherato o sostituito con quello controlaterale sano (approccio enantiomorfico) prima di stimare la trasformazione [5, 7], e le guide di lesion-behaviour mapping la trattano come uno dei passi da curare [8];
- **segmentazione**: la maschera disegnata include tessuto extracerebrale o liquor;
- **maschera cerebrale**: la `desc-brain_mask` del template è più stretta del cervello del singolo paziente al bordo corticale.

I dataset di riferimento per le lesioni ictali controllano l'allineamento a occhio: ATLAS v1.2 esclude le immagini la cui registrazione è fallita [6] e ATLAS v2.0 ispeziona ogni soggetto "to ensure correct lesion mask alignment" [9]. Una misura quantitativa come $f_g$ come criterio di esclusione: **fonte non trovata**. Nel progetto $f_g$ sostituisce l'ispezione visiva di 5853 maschere come primo filtro, e la lista dei candidati si apre poi a occhio (`docs/guides/metadata.md`).

### 3.4 L'esclusione oltre il 30%

**Scelta del progetto**, non un valore di letteratura ([`.claude/history/methods_changelog.md`](../../../.claude/history/methods_changelog.md), voce del 06-10-26 "Criteri di esclusione dalle matrici: nessuna esclusione per lesione piccola, soglia > 30% fuori dal brain").

- **Regola**: si esclude un soggetto se $f_{2\text{mm}} > 0{,}30$ (stretta: chi vale esattamente 0,30 resta). Motivo `out_of_brain_fraction_too_high` in `assets/metadata/excluded_subjects.csv`.
- **Chi la applica**: nessuna pipeline. La soglia è un criterio di analisi; i soggetti sono elencati a mano in `config/pipelines/build_excluded_subjects.json`.
- **Perché 30%**: oltre questa quota la parte di maschera che resta dopo la correzione non rappresenta più in modo credibile la lesione. La distribuzione non ha un salto naturale su cui fissare una soglia.
- **Cosa succede sotto la soglia**: il soggetto resta, e i suoi voxel fuori dal cervello sono azzerati se la matrice è costruita con `correct_out_of_brain: true`.

Nel csv attuale, sulla griglia a 2 mm: 1506 soggetti su 5853 hanno almeno un voxel fuori dal cervello; mediana di $f$ pari a 0, 95° percentile 0,041; 234 soggetti sopra il 5%, 73 sopra il 10%, 5 sopra il 30% (frazioni 0,41 / 0,48 / 0,76 / 0,94 / 1,00). La quota di soggetti con almeno un voxel fuori varia molto per dataset (dal 13% di UCL-UK al 76% di WashU e UKLFR). Che la differenza venga dalle pipeline di normalizzazione dei centri è un'ipotesi, non verificata.

### 3.5 Limiti

- La soglia è calcolata sulla griglia a 2 mm; a 1 mm la frazione è diversa per lo stesso soggetto (9 soggetti sopra il 30% a 1 mm), perché le due maschere cerebrali non coincidono voxel per voxel.
- Un voxel di lesione dentro la maschera cerebrale ma nel posto sbagliato (una normalizzazione traslata che resta dentro il cervello) non è rilevato: $f_g$ vede solo l'errore che esce dal cervello.

---

## Fonti

1. Ciric R, Thompson WH, Lorenz R, et al. (2022). TemplateFlow: FAIR-sharing of multi-scale, multi-species brain models. *Nature Methods* 19:1568-1571. https://doi.org/10.1038/s41592-022-01681-2 — descrizione del template `MNI152NLin6Asym` (origini e shape delle risoluzioni 1 e 2): https://github.com/templateflow/tpl-MNI152NLin6Asym/blob/master/template_description.json
2. Evans AC, Janke AL, Collins DL, Baillet S (2012). Brain templates and atlases. *NeuroImage* 62:911-922. https://doi.org/10.1016/j.neuroimage.2012.01.024
3. FSL, documentazione ufficiale, "Standard templates and atlases": https://fsl.fmrib.ox.ac.uk/fsl/docs/other/datasets.html — e Jenkinson M, Beckmann CF, Behrens TE, Woolrich MW, Smith SM (2012). FSL. *NeuroImage* 62:782-790. https://doi.org/10.1016/j.neuroimage.2011.09.015
4. Corbetta M, Ramsey L, Callejas A, et al. (2015). Common behavioral clusters and subcortical anatomy in stroke. *Neuron* 85:927-941. https://doi.org/10.1016/j.neuron.2015.02.027
5. Salvalaggio A, De Filippo De Grazia M, Zorzi M, Thiebaut de Schotten M, Corbetta M (2020). Post-stroke deficit prediction from lesion and indirect structural and functional disconnection. *Brain* 143:2173-2188. https://doi.org/10.1093/brain/awaa156
6. Liew SL, Anglin JM, Banks NW, et al. (2018). A large, open source dataset of stroke anatomical brain images and manual lesion segmentations. *Scientific Data* 5:180011. https://doi.org/10.1038/sdata.2018.11
7. Talozzi L, Forkel SJ, Pacella V, et al. (2023). Latent disconnectome prediction of long-term cognitive-behavioural symptoms in stroke. *Brain* 146:1963-1978. https://doi.org/10.1093/brain/awad013
8. de Haan B, Karnath HO (2018). A hitchhiker's guide to lesion-behaviour mapping. *Neuropsychologia* 115:5-16. https://doi.org/10.1016/j.neuropsychologia.2017.10.021
9. Liew SL, Tavenner BP, Donnelly MR, et al. (2022). A large, curated, open-source stroke neuroimaging dataset to improve lesion segmentation algorithms. *Scientific Data* 9:320. https://doi.org/10.1038/s41597-022-01401-7
