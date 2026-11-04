# Template MNI152NLin6Asym, griglie a 1 e 2 mm, colonne costanti

> Teoria: [Template MNI152NLin6Asym, griglie a 1 e 2 mm, colonne costanti](../../../knowledge/concepts/Neuroimaging_Connectivity/template_and_grids.md) (second brain). Questa nota contiene solo la parte specifica di NEMESIS.

Teoria e letteratura dietro tre scelte che valgono per tutte le matrici voxel-wise del repo: lo spazio di riferimento, la griglia su cui si costruiscono le matrici, la rimozione dei voxel costanti. Come lo calcola il codice: `docs/dev/lesion_matrix.md` e `docs/dev/sdc_matrix.md`. Come una maschera arriva sulla griglia e come viene binarizzata: [`lesion_resampling.md`](lesion_resampling.md). Le metriche per soggetto (volume, frazione fuori dal cervello): [`lesion_metrics.md`](lesion_metrics.md). Il disconnettoma: [`disconnectome_bcbtoolkit.md`](disconnectome_bcbtoolkit.md).

Il documento è in tre parti:

- **[Parte 1 — Il template](#parte-1--il-template-mni152nlin6asym)**: cos'è MNI152NLin6Asym, da dove viene, come si distingue dalle altre varianti MNI152.
- **[Parte 2 — 1 mm contro 2 mm](#parte-2--griglia-a-1-mm-contro-griglia-a-2-mm)**: discretizzazione, volume parziale, effetto su volumi e dimensionalità, perché la produzione usa 2 mm.
- **[Parte 3 — Colonne costanti](#parte-3--rimozione-delle-colonne-costanti)**: perché si tolgono i voxel che non variano tra soggetti, e cosa ne dicono documentazione e letteratura.

---

## 6. Cosa conta per il nostro uso

- **Lo spazio è uno solo.** Maschere (`*_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`) e disconnettomi BCBToolKit sono in MNI152NLin6Asym; i template di riferimento delle matrici e le maschere cerebrali sono quelli TemplateFlow dello stesso spazio. Non si introduce nessuna trasformazione tra template.
- **Lo spazio non fissa la griglia.** Le maschere hanno tre header diversi a parità di shape (LAS +90, RAS −90, RAS −91; `docs/guides/datasets.md`): solo il terzo coincide con `res-1`. Per questo il codice confronta shape **e** affine e ricampiona attraverso gli affine ([`lesion_resampling.md`](lesion_resampling.md) § 1).
- **Un'eccezione dentro BCBToolKit.** Le feature `yeh_hcp1065_streamline` sono calcolate da BCBlib dopo aver portato la maschera in MNI152NLin2009cAsym, lo spazio delle trattografie Yeh ([`disconnectome_bcbtoolkit.md`](disconnectome_bcbtoolkit.md) § 11). Nel repo arrivano come CSV per tratto, quindi nessuna griglia NLin2009cAsym entra in una matrice voxel-wise.
- **Gli atlanti devono stare nello stesso spazio.** La sede della lesione usa gli atlanti distribuiti con FSL (Harvard-Oxford, cervelletto); la documentazione FSL descrive ad esempio l'atlante cerebellare come allineato al template MNI152 [7]. Il repo non si affida a questa dichiarazione: i controlli all'avvio sulla griglia degli atlanti sono in `docs/dev/metadata.md`.

---

## 10. L'effetto sui volumi, misurato

`assets/metadata/lesion_metadata.csv` misura ogni maschera su entrambe le griglie. Rapporto $N_{1\text{mm}} / (8\, N_{2\text{mm}})$ sui soggetti con lesione interamente dentro la maschera cerebrale su entrambe le griglie (così la correzione fuori dal cervello, che usa maschere diverse per griglia, non entra nel confronto):

| Dataset | Soggetti | Mediana | Min – max | Dettaglio nativo (`docs/guides/datasets.md`) |
|---|---|---|---|---|
| UCL-UK | 3284 | 1,000 | 1,000 – 1,000 | reticolo 2 mm |
| UKLFR | 134 | 1,000 | 1,000 – 1,000 | reticolo 2 mm |
| WashU | 40 | 1,000 | 1,000 – 1,000 | reticolo 2 mm |
| NEMESIS_T0 | 22 | 1,000 | 1,000 – 1,000 | reticolo 2 mm |
| SFB936 | 20 | 1,000 | 1,000 – 1,000 | reticolo 2 mm |
| PASPORT | 30 | 0,999 | 0,942 – 1,082 | 1 mm |
| WAKEUP | 330 | 0,999 | 0,667 – 3,375 | 1 mm |
| PSP | 109 | 0,793 | 0,343 – 0,917 | 2 mm interpolata |

Misura del progetto (21-10-26). Lettura:

- **Reticolo 2 mm**: la maschera a 1 mm è un blocco $2 \times 2 \times 2$ costante per ogni voxel originale, e il campionamento ne legge uno: la griglia a 2 mm ricostruisce esattamente l'originale, e $N_{1\text{mm}} = 8 N_{2\text{mm}}$.
- **1 mm genuino**: il campionamento è uno stimatore (§ 9), centrato su 1 ma con dispersione che cresce al calare della lesione. Due lesioni WAKEUP di 8 e 3 voxel a 1 mm spariscono a 2 mm ([`lesion_metrics.md`](lesion_metrics.md) § 2.3).
- **PSP**: non è un effetto della griglia a 2 mm ma della soglia a 1 mm sui valori frazionari ([`lesion_resampling.md`](lesion_resampling.md) § 13).

## 11. L'effetto sulla dimensionalità delle matrici

Una matrice voxel-wise ha una colonna per voxel della griglia, prima della rimozione delle colonne costanti (Parte 3). Con $n = 5845$ soggetti (sessioni `s1.4-vol`, `s2.4-vol`):

| | 2 mm | 1 mm |
|---|---|---|
| Colonne prima della rimozione | 902.629 | 7.221.032 |
| Lesione, `uint8`, matrice piena | 5,3 GB | 42 GB |
| Disconnettoma, `float32`, matrice piena | 21 GB | 169 GB |
| Colonne dopo la rimozione | 221.955 (lesione), 227.235 (SDC) | non costruita |

Le colonne dopo la rimozione sono quelle di `docs/experiments/s1.4-vol.md`/`s2.4-vol.md`. A 1 mm il numero di colonne non costanti non è stato misurato. Per i 5150 soggetti a reticolo 2 mm le 8 colonne di ogni blocco $2 \times 2 \times 2$ avrebbero lo stesso valore, quindi la dimensionalità crescerebbe di circa 8 volte senza aggiungere informazione per quei soggetti; la differenza tra le 8 colonne verrebbe solo dai 702 soggetti con dettaglio a 1 mm (534) o interpolato (168).

## 12. Perché la produzione usa 2 mm

**Scelta del progetto**, motivata da:

1. **Il dettaglio nativo.** 5150 soggetti su 5853 hanno maschere il cui dettaglio è un reticolo a 2 mm (`docs/guides/datasets.md`): per loro la griglia a 2 mm è esatta (§ 10) e quella a 1 mm non aggiunge nulla.
2. **Memoria e calcolo.** La matrice piena a 1 mm non è costruibile su nessuna macchina disponibile (§ 11); la documentazione di nilearn indica il sottocampionamento come modo per aumentare la velocità e ridurre la memoria [20].
3. **Pratica della letteratura sul disconnettoma.** Thiebaut de Schotten et al. 2020 registrano le lesioni nello spazio MNI a $2 \times 2 \times 2$ mm prima della PCA [21]; Talozzi et al. 2023 normalizzano le lesioni in MNI152 a 2 mm con BCBToolKit prima di UMAP [22]; Bisogno et al. 2025 ricampionano le lesioni a 2 mm isotropi per la disconnessione funzionale [16].

**Il costo** è limitato ai soggetti a 1 mm genuino (534: PASPORT, WAKEUP) e riguarda le lesioni più piccole. È il motivo per cui `lesion_metadata.csv` conserva entrambe le griglie: distingue una maschera vuota da una lesione persa nel campionamento. I tre gruppi di dettaglio nativo (5150, 534 e 168 di PSP) sommano 5852 soggetti: il 5853° ha la maschera vuota e non è classificabile.

---

## Riferimento rapido

- Template: `assets/templates/tpl-MNI152NLin6Asym_res-{1,2}_{T1w,desc-brain_mask}.nii.gz`.
- Config: `reference_template_path`, `brain_mask_path` in `config/pipelines/build_lesion_matrix.json`, `build_sdc_matrix.json`, `compute_lesion_metadata.json` (`grids`).
- Codice: `src/features/lesion.py` (`load_reference_image`, `_drop_constant_features`), `src/features/sdc.py` (`_non_constant_voxel_mask`, `_stack_voxelwise_matrix`).

## Righe tolte dalla nota teorica (parti di progetto e rimandi a file)

- **Anatomia.** Che le due medie mettano le stesse strutture in coordinate leggermente diverse è riportato solo da fonti non approvate (vedi la nota finale); una quantificazione peer-reviewed dello scarto in millimetri: **fonte non trovata**. La regola pratica che se ne ricava, e che il repo segue, è non mescolare dati in NLin6Asym e NLin2009cAsym senza una trasformazione esplicita tra i due.

Un template **simmetrico** è costruito in modo che i due emisferi siano rappresentati allo stesso modo, così che confronti sinistra-destra non dipendano da un'asimmetria della media [6]. Un template **asimmetrico** conserva l'asimmetria emisferica media della coorte; l'asimmetria è uno dei fattori che, secondo [1], condiziona la scelta del template. Per l'uso di questo repo l'asimmetria conta in un punto: l'indice di lateralità usa il piano $x = 0$ come confine tra gli emisferi ([`lesion_laterality.md`](lesion_laterality.md)), e in un template asimmetrico quel piano non è per costruzione un piano di simmetria anatomica. È una conseguenza della definizione, non verificata sul template; quanto pesi sull'attribuzione del lato non è stato misurato.

Nei dati del repo, maschere e disconnettomi sono tutti $182 \times 218 \times 182$ a 1 mm, la shape di MNI152NLin6Asym `res-1` (`docs/guides/datasets.md`). Che il `MNI152.nii.gz` incluso in BCBToolKit sia byte per byte il template FSL **non è verificato**.

TemplateFlow distribuisce MNI152NLin6Asym in sei risoluzioni; il repo usa le prime due [8], sotto `assets/templates/`:

Shape e origini sono quelle del descrittore TemplateFlow [8], verificate sui file di `assets/templates/`; i conteggi della maschera cerebrale sono misurati sui file (`> 0,5`). Come TemplateFlow abbia derivato quella maschera: **fonte non trovata** (lo stesso è segnalato in [`lesion_metrics.md`](lesion_metrics.md) §1.1).

Sulla coppia `res-1` → `res-2` di MNI152NLin6Asym i centri a 2 mm coincidono con centri a 1 mm (§ 5). Il campionamento puntuale legge quindi esattamente un voxel a 1 mm, e l'interpolazione **lineare dà lo stesso risultato di `nearest`**: un interpolante lineare valutato in un centro di voxel sorgente restituisce il valore di quel voxel. Verificato nel repo con `resample_to_img` su una maschera sintetica e i tre header delle maschere reali (LAS +90, RAS −90, RAS −91): output identici, valori solo 0 e 1. Per un header RAS −91 il risultato è esattamente `mask[1::2, 0::2, 0::2]`. La media pesata per area non è disponibile in `resample_to_img`.

Il campionamento puntuale su un reticolo sistematico è lo stimatore del volume per conteggio di punti della stereologia (principio di Cavalieri), non distorto quando la posizione del reticolo rispetto all'oggetto è casuale [19]. Le lesioni hanno posizioni varie rispetto alla griglia, e questo spiega perché sulla coorte il rapporto tra i volumi resti centrato su 1 (§ 10), pur con una varianza alta per le lesioni piccole.

è zero. Per una colonna binaria con frequenza di lesione $\hat p_j = \bar x_j$ la varianza (non corretta) è $\hat p_j(1-\hat p_j)$ [23], nulla se e solo se $\hat p_j \in \{0, 1\}$: voxel mai lesionato o lesionato in tutti i soggetti. In una matrice di lesioni ictali il secondo caso non si presenta; il primo riguarda la maggior parte della griglia (fuori dal cervello, e dentro il cervello i voxel mai colpiti nella coorte). In `s1.4-vol` sopravvivono 221.955 colonne su 902.629.

- **Standardizzazione.** La standardizzazione $z_{ij} = (x_{ij} - \bar x_j)/s_j$ non è definita per $s_j = 0$. `StandardScaler` di scikit-learn in quel caso lascia la colonna invariata con fattore di scala 1 [24], una scelta silenziosa; `src/analysis/covariance_pca.py` invece solleva un errore se `standardize=True` incontra una colonna costante.

- **Costo.** Le colonne passano da 902.629 a circa 222.000 (§ 11), un fattore 4 su memoria e tempo di ogni passo successivo.

**La differenza con il repo.** Il criterio di lesion-symptom mapping serve a test statistici massivamente univariati, voxel per voxel. Il repo costruisce un embedding multivariato, e toglie **solo** le colonne esattamente costanti ($\hat p_j \in \{0, 1\}$): nessuna soglia minima di frequenza. **Scelta del progetto**: una soglia di frequenza sarebbe un parametro in più da giustificare e cambierebbe la distanza tra soggetti con lesioni in zone rare. Una variante con soglia non è stata provata.

**Per il disconnettoma voxel-wise** la definizione è la stessa ($\min = \max$ esatto), su valori continui: un rumore di arrotondamento (interpolazione `continuous`) basta a rendere non costante un voxel che vale zero per tutti, ed è uno dei motivi per cui la produzione non usa quell'interpolazione (`docs/dev/sdc_matrix.md`).

7. FSL, documentazione ufficiale, "Standard templates and atlases". https://fsl.fmrib.ox.ac.uk/fsl/docs/other/datasets.html (consultato il 21-10-26).
