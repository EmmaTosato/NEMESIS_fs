# Sede della lesione: atlanti, categorie, allineamento

Come il repo dice dove sta ogni lesione: sette categorie anatomiche esclusive per voxel, costruite da tre atlanti FSL, e per ogni lesione la quota in ciascuna. Codice: `src/features/lesion_location.py` (`build_location_categories`, `location_metrics`, `_load_atlas`), chiamato da `src/features/lesion.py::_metrics_on_grid`. Colonne: `location_dominant_2mm` e `location_<categoria>_2mm` in `assets/metadata/lesion_metadata.csv`. Notazione e passaggi comuni (allineamento, binarizzazione, correzione): [`lesion_metrics.md`](lesion_metrics.md) §1. Schema del csv: `docs/dev/metadata.md`, sezione "La sede della lesione". Decisioni e alternative: `.claude/history/methods_changelog.md`; punti aperti: `.claude/open_problems.md`.

## 1. Gli atlanti

In `assets/atlases/fsl/` (provenienza nel suo `README.md`: pacchetto FSL 5.0.7, file copiati senza modifiche), versione `maxprob-thr25`, a 1 mm e 2 mm. In produzione si usano i file a 2 mm.

| Atlante | Etichette | Come è costruito | Fonte |
|---|---|---|---|
| Harvard-Oxford corticale | 48 | segmentazione semi-automatica di 37 soggetti sani (21 M, 16 F, 18-50 anni) del Center for Morphometric Analysis di Harvard, registrati in MNI152 con FLIRT (affine) e combinati in mappe di probabilità | [1-5] |
| Harvard-Oxford sotto-corticale | 21 | come sopra | [1-5] |
| Cerebellum-MNIfnirt | 28 | maschere dei lobuli cerebellari di 20 soggetti, mediate dopo registrazione non lineare in MNI152 | [1, 6] |

- **`maxprob-thr25`**: secondo il `README.md` della cartella, ogni voxel porta l'etichetta più probabile purché la sua probabilità sia almeno il 25%, altrimenti 0. Una descrizione ufficiale FSL di questa definizione: **fonte non trovata** (la pagina "Standard templates and atlases" [1] descrive le mappe di probabilità, non le versioni a soglia).
- **Indici**: il valore del voxel è l'attributo `index` dell'XML + 1, 0 = nessuna etichetta (`_read_labels`). Gli indici si leggono dall'XML, mai per offset (`.claude/lessons_learned.md` #11).
- **Etichette non anatomiche dell'atlante sotto-corticale**: oltre alle 14 strutture grigie e al tronco, contiene `Left/Right Cerebral White Matter`, `Left/Right Cerebral Cortex` e `Left/Right Lateral Ventricle` (l'XML scrive "Left Lateral **Ventrical**").

**Atlanti non usati.** Il codice non usa gli atlanti JHU di sostanza bianca [7, 8], né l'atlante strutturale MNI, né altri. JHU è stato considerato e rinviato: Harvard-Oxford separa già la sostanza bianca dalla grigia (`.claude/history/methods_changelog.md`, voce del 06-10-26 "Sede della lesione: atlanti FSL e sei categorie esclusive"; lì anche le altre alternative scartate: AAL3, SUIT, Schaefer/Tian, Arterial Territories Atlas).

## 2. Le sette categorie

### 2.1 Regole

Siano, sulla griglia di sede (2 mm), $C(v)$ l'etichetta dell'atlante corticale, $S(v)$ quella del sotto-corticale, $K(v)$ quella del cervelletto, $B(v)$ la maschera cerebrale. Le regole (`build_location_categories`) sono insiemi di voxel:

| Insieme | Definizione | Etichette attese |
|---|---|---|
| $\text{cortex}$ | $C(v) > 0$ | tutte e 48 |
| $\text{white}$ | $S(v) \in$ {`Left/Right Cerebral White Matter`} | 2 |
| $\text{gray}$ | $S(v) \in$ {talamo, caudato, putamen, pallido, ippocampo, amigdala, accumbens}, sinistri e destri | 14 |
| $\text{infra}$ | $S(v) =$ `Brain-Stem` oppure $K(v) > 0$ | 1 + tutte e 28 |
| $\text{vent}$ | $S(v) \in$ {etichette che contengono `Lateral Vent`} | 2 |

Il numero di etichette che ogni regola riconosce è controllato (`_values_where`): un'etichetta rinominata o aggiunta solleva invece di spostare voxel in silenzio.

Ogni voxel dentro il cervello riceve **una sola** categoria. Le assegnazioni vanno dalla precedenza più bassa alla più alta, ognuna sovrascrive le precedenti:

$$c(v) = \begin{cases}
0 & B(v) = 0 \\
\text{infratentorial} & v \in \text{infra} \\
\text{subcortical\_gray} & v \in \text{gray} \setminus \text{infra} \\
\text{cortex\_white\_boundary} & v \in (\text{cortex} \cap \text{white}) \setminus (\text{gray} \cup \text{infra}) \\
\text{cortex\_only} & v \in (\text{cortex} \setminus \text{white}) \setminus (\text{gray} \cup \text{infra}) \\
\text{white\_matter\_only} & v \in (\text{white} \setminus \text{cortex}) \setminus (\text{gray} \cup \text{infra}) \\
\text{ventricle} & v \in \text{vent} \setminus (\text{cortex} \cup \text{white} \cup \text{gray} \cup \text{infra}) \\
\text{unlabeled} & \text{altrimenti, con } B(v) = 1
\end{cases}$$

Due conseguenze da conoscere:

- un voxel che l'atlante sotto-corticale chiama ventricolo e il corticale chiama corteccia va in `cortex_only`;
- le etichette `Cerebral Cortex` dell'atlante **sotto-corticale** non entrano in nessuna regola: un voxel con quella etichetta e nessuna etichetta corticale è `unlabeled`.

### 2.2 Dimensione delle categorie sulla griglia a 2 mm

| Categoria | Voxel | Quota del cervello |
|---|---:|---:|
| `infratentorial` | 25.423 | 11,1% |
| `subcortical_gray` | 7.958 | 3,5% |
| `cortex_only` | 115.623 | 50,6% |
| `cortex_white_boundary` | 12.875 | 5,6% |
| `white_matter_only` | 49.841 | 21,8% |
| `ventricle` | 1.354 | 0,6% |
| `unlabeled` | 15.409 | 6,7% |
| totale (maschera cerebrale) | 228.483 | 100% |

Dei 15.409 voxel `unlabeled`, 7.862 hanno l'etichetta `Cerebral Cortex` dell'atlante sotto-corticale senza un'etichetta corticale. 6.722 voxel etichettati da uno dei tre atlanti (6.182 dai due Harvard-Oxford, 540 dal cervelletto) stanno fuori dalla maschera cerebrale e non entrano in nessuna categoria.

### 2.3 Perché queste categorie

- **Precedente nel laboratorio.** Corbetta et al. 2015 classificano ogni lesione dalla quota dei suoi voxel che cade in maschere di grigia, bianca e nuclei sotto-corticali ("number voxels in the lesion overlapping with each mask/total number of voxels in the lesion"), con maschere costruite da segmentazioni FreeSurfer di 38 soggetti sani, e poi raggruppano con K-means in tronco, cervelletto, corticale, cortico-sottocorticale, sottocorticale, sola sostanza bianca [9]. Bisogno et al. 2021 descrivono la topografia proiettando le lesioni sulle maschere corticali e sotto-corticali di Harvard-Oxford [10].
- **ATLAS** definisce sottocorticale una lesione "contained completely in the white matter and subcortical structures", corticale qualunque lesione che si estende nella corteccia, e mette tronco e cervelletto in "Other" [11].
- **Le sette categorie, la loro precedenza e il tronco intero come infratentoriale** sono **scelte del progetto** ([`.claude/history/methods_changelog.md`](../../../.claude/history/methods_changelog.md), voci del 06-10-26 "Sede della lesione: atlanti FSL e sei categorie esclusive" e del 07-10-26 "Sede della lesione: sovrapposizione corticale/bianca come categoria a parte (opzione C)"). La differenza da Corbetta 2015 è voluta: qui si salvano le quote continue per categoria, non un'etichetta per lesione; le etichette a soglia ("coinvolta", "pura") si derivano alla lettura e le soglie non sono decise (`.claude/open_problems.md`).
- **`cortex_white_boundary`.** I due atlanti Harvard-Oxford sono file distinti e i loro bordi non sono garantiti coerenti; i voxel che l'uno chiama corteccia e l'altro sostanza bianca formano una categoria a sé invece di essere assegnati d'ufficio a uno dei due lati (**scelta del progetto**, voce del 07-10-26 citata sopra: dare la precedenza alla bianca cambia la categoria dominante nel 7,8% delle lesioni).

## 3. Quote per lesione e categoria dominante

Sia $\ell^{*}$ la maschera corretta sulla griglia a 2 mm ([`lesion_metrics.md`](lesion_metrics.md) §1.2). Per ogni categoria $k$:

$$n_k = \sum_{v} \ell^{*}(v)\,\mathbb{1}[c(v) = k], \qquad p_k = \frac{n_k}{\sum_{j=1}^{7} n_j}$$

$$\text{dominante} = \arg\max_k \; n_k$$

Codice: `location_metrics`, con `np.bincount(categories[lesion])` (la categoria 0, fuori dal cervello, è scartata) e `np.argmax`.

- **Denominatore**: i voxel di lesione dentro la maschera cerebrale. Con `correct_out_of_brain: true` (produzione) è esattamente `lesion_volume_voxels_2mm`, quindi $p_k \times V$ dà i voxel. Le sette quote sommano a 1. La quota fuori dal cervello è `out_of_brain_fraction_2mm`.
- **Parità**: a pari $n_k$ vince la categoria che viene prima nell'ordine `infratentorial`, `subcortical_gray`, `cortex_only`, `cortex_white_boundary`, `white_matter_only`, `ventricle`, `unlabeled` (`LOCATION_CATEGORIES`; `np.argmax` restituisce il primo massimo). È deterministica ma è una convenzione, frequente per lesioni di pochi voxel.
- **Lesione senza voxel nel cervello** (maschera vuota, o tutta fuori): tutte le otto colonne `NaN`, mai quote a 0. Nel csv attuale: 4 soggetti.
- **Solo 2 mm**: a 2 mm le maschere ricostruiscono l'originale; a 1 mm alcune sono ricampionamenti e quelle PSP perdono voxel (voce del 07-10-26 "Sede della lesione: classificazione sulla griglia a 2 mm, 1 mm come controllo"). Gli atlanti devono essere alla risoluzione della griglia: non sono ricampionati a un'altra risoluzione.

Categoria dominante nel csv attuale (5853 soggetti): `white_matter_only` 2746, `cortex_only` 1903, `infratentorial` 645, `subcortical_gray` 507, `unlabeled` 27, `cortex_white_boundary` 21, `ventricle` 0, vuota 4.

## 4. Allineamento

- Gli atlanti sono **LAS**, i template in `assets/templates/` **RAS**, le maschere hanno 3 header (LAS +90, RAS −90, RAS −91). Tutto passa dall'**affine** (`resample_to_img`, `nearest`), mai da un flip dell'array.
- Atlante e template coincidono a meno di un'inversione dell'asse x con offset intero (181 voxel a 1 mm, 90 a 2 mm): il ricampionamento non perde voxel.
- `_load_atlas` solleva se uno di quattro controlli fallisce: (1) l'atlante è una mappa intera esatta sulla griglia (permutazione di assi con segno e offset intero, `_check_integer_voxel_map`); (2) il numero di voxel per etichetta non cambia col ricampionamento; (3) i valori presenti sono esattamente gli indici dell'XML + 1; (4) il baricentro in coordinate mondo di ogni etichetta `Left` ha $x < 0$, di ogni `Right` $x > 0$, di ogni `Vermis` $|x| < 8$ mm (`_check_hemisphere_signs`).
- Questi controlli possono fallire: un flip naive dell'array produce 20 violazioni per atlante, e scambiando L/R l'accordo tra lato dell'atlante e `lesion_side_2mm` crolla da 5465/5483 a 18/5483 (voci del 06-10-26 e 07-10-26 citate sopra).

## 5. Limiti

- **Fascia corticale generosa.** A 1 mm 109.621 voxel sono sia corticali per HO corticale sia `Cerebral White Matter` per HO sotto-corticale; a 2 mm sono i 12.875 voxel di `cortex_white_boundary`. "Corticale" va quindi dichiarato in due versioni: stretta (`cortex_only`) e larga (`cortex_only` + `cortex_white_boundary`).
- **Atlanti di popolazione.** Le etichette vengono da 37 (HO) e 20 (cervelletto) soggetti sani giovani registrati in MNI152 [1]; la sede di una lesione è quella dell'atlante nel punto in cui la normalizzazione l'ha portata, non l'anatomia del singolo paziente.
- **Mesencefalo.** Il tentorio lo taglia, ma HO ha un'unica etichetta `Brain-Stem`: il tronco intero conta infratentoriale.
- **Tronco senza lato.** `Brain-Stem` non ha etichette sinistra/destra: per una lesione solo di tronco il lato viene solo dall'indice di lateralità ([`lesion_laterality.md`](lesion_laterality.md)).
- **PSP a 1 mm.** Le maschere PSP sono frazionarie e a 1 mm la binarizzazione `> 0,5` ne perde voxel; la sede è calcolata a 2 mm, dove la maschera è esatta.
- **`unlabeled`** raccoglie soprattutto voxel che solo l'etichetta `Cerebral Cortex` dell'atlante sotto-corticale riconosce (§2.2): non è "fuori da ogni struttura".

## Fonti

1. FSL, documentazione ufficiale, "Standard templates and atlases": https://fsl.fmrib.ox.ac.uk/fsl/docs/other/datasets.html — e Jenkinson M, Beckmann CF, Behrens TE, Woolrich MW, Smith SM (2012). FSL. *NeuroImage* 62:782-790. https://doi.org/10.1016/j.neuroimage.2011.09.015
2. Desikan RS, Ségonne F, Fischl B, et al. (2006). An automated labeling system for subdividing the human cerebral cortex on MRI scans into gyral based regions of interest. *NeuroImage* 31:968-980. https://doi.org/10.1016/j.neuroimage.2006.01.021
3. Makris N, Goldstein JM, Kennedy D, et al. (2006). Decreased volume of left and total anterior insular lobule in schizophrenia. *Schizophrenia Research* 83:155-171. https://doi.org/10.1016/j.schres.2005.11.020
4. Frazier JA, Chiu S, Breeze JL, et al. (2005). Structural brain magnetic resonance imaging of limbic and thalamic volumes in pediatric bipolar disorder. *American Journal of Psychiatry* 162:1256-1265. https://doi.org/10.1176/appi.ajp.162.7.1256
5. Goldstein JM, Seidman LJ, Makris N, et al. (2007). Hypothalamic abnormalities in schizophrenia: sex effects and genetic vulnerability. *Biological Psychiatry* 61:935-945. https://doi.org/10.1016/j.biopsych.2006.06.027
6. Diedrichsen J, Balsters JH, Flavell J, Cussans E, Ramnani N (2009). A probabilistic MR atlas of the human cerebellum. *NeuroImage* 46:39-46. https://doi.org/10.1016/j.neuroimage.2009.01.045
7. Mori S, Oishi K, Jiang H, et al. (2008). Stereotaxic white matter atlas based on diffusion tensor imaging in an ICBM template. *NeuroImage* 40:570-582. https://doi.org/10.1016/j.neuroimage.2007.12.035
8. Hua K, Zhang J, Wakana S, et al. (2008). Tract probability maps in stereotaxic spaces: analyses of white matter anatomy and tract-specific quantification. *NeuroImage* 39:336-347. https://doi.org/10.1016/j.neuroimage.2007.07.053
9. Corbetta M, Ramsey L, Callejas A, et al. (2015). Common behavioral clusters and subcortical anatomy in stroke. *Neuron* 85:927-941. https://doi.org/10.1016/j.neuron.2015.02.027
10. Bisogno AL, Favaretto C, Zangrossi A, et al. (2021). A low-dimensional structure of neurological impairment in stroke. *Brain Communications* 3:fcab119. https://doi.org/10.1093/braincomms/fcab119
11. Liew SL, Anglin JM, Banks NW, et al. (2018). A large, open source dataset of stroke anatomical brain images and manual lesion segmentations. *Scientific Data* 5:180011. https://doi.org/10.1038/sdata.2018.11
