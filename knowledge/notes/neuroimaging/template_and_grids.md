# Template MNI152NLin6Asym, griglie a 1 e 2 mm, colonne costanti

Teoria e letteratura dietro tre scelte che valgono per tutte le matrici voxel-wise del repo: lo spazio di riferimento, la griglia su cui si costruiscono le matrici, la rimozione dei voxel costanti. Come lo calcola il codice: `docs/dev/lesion_matrix.md` e `docs/dev/sdc_matrix.md`. Come una maschera arriva sulla griglia e come viene binarizzata: [`lesion_resampling.md`](lesion_resampling.md). Le metriche per soggetto (volume, frazione fuori dal cervello): [`lesion_metrics.md`](lesion_metrics.md). Il disconnettoma: [`disconnectome_bcbtoolkit.md`](disconnectome_bcbtoolkit.md).

Il documento è in tre parti:

- **[Parte 1 — Il template](#parte-1--il-template-mni152nlin6asym)**: cos'è MNI152NLin6Asym, da dove viene, come si distingue dalle altre varianti MNI152.
- **[Parte 2 — 1 mm contro 2 mm](#parte-2--griglia-a-1-mm-contro-griglia-a-2-mm)**: discretizzazione, volume parziale, effetto su volumi e dimensionalità, perché la produzione usa 2 mm.
- **[Parte 3 — Colonne costanti](#parte-3--rimozione-delle-colonne-costanti)**: perché si tolgono i voxel che non variano tra soggetti, e cosa ne dicono documentazione e letteratura.

---

# Parte 1 — Il template MNI152NLin6Asym

## 1. "Spazio MNI" non identifica un oggetto unico

Uno spazio stereotassico ha due componenti: un sistema di coordinate 3D, di solito incarnato da un'immagine di riferimento (il *template*), e una funzione che porta l'immagine di un soggetto dal suo spazio nativo a quel sistema [1]. La scelta del template dipende da età, sesso, asimmetria emisferica, metodo di normalizzazione e patologia, e questo ha prodotto molti template tra loro incompatibili [1].

"MNI" è quindi un'etichetta ambigua. SPM96 e precedenti riferiscono i risultati al template a soggetto singolo "Colin 27"; SPM99 e successivi a medie lineari o non lineari di 152 soggetti; FreeSurfer a una media lineare di 305 soggetti [2]. Anche il template distribuito con FSL "non fa parte del portafoglio ufficiale distribuito dall'MNI" [2]. TemplateFlow risolve l'ambiguità dando a ogni template un identificatore persistente (`tpl-<nome>`), con risoluzioni e metadati dichiarati in un file di descrizione [2].

## 2. La genealogia delle medie MNI152

| Template | Costruzione | Soggetti | Chi | Fonte |
|---|---|---|---|---|
| **MNI305** | media lineare, predecessore di MNI152 | 305 | MNI | [3] |
| **MNI152 lineare** (`MNI152Lin`) | ogni soggetto della coorte ICBM registrato **linearmente** su MNI305, poi mediato | 152 | ICBM / MNI | [3, 4] |
| **ICBM 152 non lineare, 6ª generazione, simmetrico** (`MNI152NLin6Sym`) | registrazione lineare e **non lineare (6 iterazioni)**, modello **simmetrico** | 152 | Grabner, Janke, Collins et al. | [5, 6] |
| **ICBM 152 non lineare, 6ª generazione, asimmetrico** (`MNI152NLin6Asym`) | media di 152 immagini strutturali dopo registrazione non lineare ad alta dimensionalità nello spazio MNI152; controparte **asimmetrica** del precedente | 152 | Andrew Janke, distribuito con FSL | [7, 8] |
| **ICBM 2009a/b/c non lineare** (`MNI152NLin2009{a,b,c}{Sym,Asym}`) | iterazioni successive di registrazione non lineare di ogni MRI nativa sulla media precedente, partendo da MNI152 lineare | 152 | Fonov, Evans, Collins et al. | [9, 10, 11] |

La coorte ICBM152 sono 152 adulti giovani sani raccolti da tre siti (MNI, UCLA, UTHSCSA): 86 maschi e 66 femmine, 18-44 anni (media 25,02, DS 4,90), 129 caucasici [3]. La pagina MNI delle medie 2009 dichiara la stessa demografia [11]. Per MNI152NLin6Asym, FSL dichiara "152 immagini strutturali" [7] senza nominare la coorte: che siano esattamente gli stessi 152 soggetti di MNI152 lineare **non è verificato** in una fonte primaria.

Il numero di iterazioni (6) è dichiarato dall'MNI per il modello **simmetrico** [5]. Che la versione asimmetrica di FSL sia stata costruita con lo stesso numero di iterazioni **non è verificato**: la documentazione FSL parla solo di "high-dimensional nonlinear registration" [7]. Il descrittore TemplateFlow di MNI152NLin6Asym ha come nome "FSL's MNI ICBM 152 non-linear 6th Generation Asymmetric Average Brain Stereotaxic Registration Model", autore Janke AL, e come riferimento bibliografico Evans et al. 2012 [8, 1]. Il testo completo di [1] non è stato letto (accesso a pagamento): ciò che la nota gli attribuisce viene dall'abstract.

### Le differenze rispetto alle altre varianti

- **Lineare contro non lineare.** MNI152 lineare è una media dopo sole trasformazioni affini, quindi più sfumata; le medie non lineari allineano anche la forma locale [3, 5, 11].
- **6ª generazione contro 2009.** Sono due costruzioni diverse dello stesso insieme di soggetti: NLin2009 usa la procedura iterativa di Fonov et al. [9, 10], con correzione di intensità N3 (v1.10.1 per 2009a, v1.11 per 2009c) e campionamento diverso tra 2009a e 2009c [11]. Le griglie non coincidono: NLin6Asym a 1 mm è $182 \times 218 \times 182$, NLin2009cAsym a 1 mm è $193 \times 229 \times 193$ [8, 12]. Un array di uno non si può leggere sulla griglia dell'altro per posizione.
- **Anatomia.** Che le due medie mettano le stesse strutture in coordinate leggermente diverse è riportato solo da fonti non approvate (vedi la nota finale); una quantificazione peer-reviewed dello scarto in millimetri: **fonte non trovata**. La regola pratica che se ne ricava, e che il repo segue, è non mescolare dati in NLin6Asym e NLin2009cAsym senza una trasformazione esplicita tra i due.
- **Default diversi.** fMRIPrep usa per default MNI152NLin2009cAsym; per usare il template di FSL bisogna chiedere `MNI152NLin6Asym` [13].

## 3. Simmetrico e asimmetrico

Un template **simmetrico** è costruito in modo che i due emisferi siano rappresentati allo stesso modo, così che confronti sinistra-destra non dipendano da un'asimmetria della media [6]. Un template **asimmetrico** conserva l'asimmetria emisferica media della coorte; l'asimmetria è uno dei fattori che, secondo [1], condiziona la scelta del template. Per l'uso di questo repo l'asimmetria conta in un punto: l'indice di lateralità usa il piano $x = 0$ come confine tra gli emisferi ([`lesion_laterality.md`](lesion_laterality.md)), e in un template asimmetrico quel piano non è per costruzione un piano di simmetria anatomica. È una conseguenza della definizione, non verificata sul template; quanto pesi sull'attribuzione del lato non è stato misurato.

## 4. Perché è il template di FSL e di BCBToolKit

- **FSL** distribuisce MNI152NLin6Asym come proprio template standard (`MNI152_T1_1mm`, `MNI152_T1_2mm`): "fornito da Andrew Janke" [7, 8]. TemplateFlow lo indica esplicitamente come "il template distribuito con FSL" [8, 13].
- **BCBToolKit dipende da FSL** e registra le lesioni "nello spazio MNI152" con deformazioni affini e diffeomorfe [14]. Il paper non dice quale variante MNI152, né la risoluzione delle mappe di disconnessione [14].
- **BCBlib**, la libreria Python dello stesso laboratorio che orchestra BCBToolKit, dichiara che lo Stage 1 "normalizza le lesioni in MNI152NLin6Asym 1mm e calcola i disconnettomi", con trattografie normative a 1 mm (`tracks_1mm`) [15].
- Bisogno et al. 2025, sulla stessa coorte UNIPD, riporta lesioni normalizzate nello spazio MNI e ricampionate a $1 \times 1 \times 1$ mm "per corrispondere allo spazio dei tratti inclusi nel BCB toolkit" [16].

Nei dati del repo, maschere e disconnettomi sono tutti $182 \times 218 \times 182$ a 1 mm, la shape di MNI152NLin6Asym `res-1` (`docs/guides/datasets.md`). Che il `MNI152.nii.gz` incluso in BCBToolKit sia byte per byte il template FSL **non è verificato**.

## 5. Le griglie TemplateFlow `res-1` e `res-2`

TemplateFlow distribuisce MNI152NLin6Asym in sei risoluzioni; il repo usa le prime due [8], sotto `assets/templates/`:

| | `res-1` | `res-2` |
|---|---|---|
| Lato del voxel $h$ | 1 mm | 2 mm |
| Shape | $182 \times 218 \times 182$ | $91 \times 109 \times 91$ |
| Voxel della griglia | 7.221.032 | 902.629 |
| Origine (centro del primo voxel) | $(-91, -126, -72)$ mm | $(-90, -126, -72)$ mm |
| Orientamento | RAS | RAS |
| Voxel nella `desc-brain_mask` | 1.827.243 | 228.483 |

Shape e origini sono quelle del descrittore TemplateFlow [8], verificate sui file di `assets/templates/`; i conteggi della maschera cerebrale sono misurati sui file (`> 0,5`). Come TemplateFlow abbia derivato quella maschera: **fonte non trovata** (lo stesso è segnalato in [`lesion_metrics.md`](lesion_metrics.md) §1.1).

**Le due griglie non sono annidate a blocchi.** I centri dei voxel a 2 mm cadono esattamente su centri di voxel a 1 mm (asse x: $-90 = -91 + 1$; assi y e z: stessa origine), un voxel ogni due per asse. Il voxel a 2 mm centrato in $c$ copre l'intervallo $[c-1, c+1]$: per asse contiene per intero il voxel a 1 mm centrato in $c$ e metà dei due vicini. In 3D un voxel a 2 mm si sovrappone quindi a 27 voxel a 1 mm, con pesi $\prod_{k} w_k$, $w_k \in \{\tfrac12, 1, \tfrac12\}$, che sommano a 8: non è l'unione di un blocco $2 \times 2 \times 2$. È una conseguenza geometrica delle origini dichiarate in [8]; le conseguenze per il ricampionamento sono al § 9.

## 6. Cosa conta per il nostro uso

- **Lo spazio è uno solo.** Maschere (`*_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`) e disconnettomi BCBToolKit sono in MNI152NLin6Asym; i template di riferimento delle matrici e le maschere cerebrali sono quelli TemplateFlow dello stesso spazio. Non si introduce nessuna trasformazione tra template.
- **Lo spazio non fissa la griglia.** Le maschere hanno tre header diversi a parità di shape (LAS +90, RAS −90, RAS −91; `docs/guides/datasets.md`): solo il terzo coincide con `res-1`. Per questo il codice confronta shape **e** affine e ricampiona attraverso gli affine ([`lesion_resampling.md`](lesion_resampling.md) § 1).
- **Un'eccezione dentro BCBToolKit.** Le feature `yeh_hcp1065_streamline` sono calcolate da BCBlib dopo aver portato la maschera in MNI152NLin2009cAsym, lo spazio delle trattografie Yeh ([`disconnectome_bcbtoolkit.md`](disconnectome_bcbtoolkit.md) § 11). Nel repo arrivano come CSV per tratto, quindi nessuna griglia NLin2009cAsym entra in una matrice voxel-wise.
- **Gli atlanti devono stare nello stesso spazio.** La sede della lesione usa gli atlanti distribuiti con FSL (Harvard-Oxford, cervelletto); la documentazione FSL descrive ad esempio l'atlante cerebellare come allineato al template MNI152 [7]. Il repo non si affida a questa dichiarazione: i controlli all'avvio sulla griglia degli atlanti sono in `docs/dev/metadata.md`.

---

# Parte 2 — Griglia a 1 mm contro griglia a 2 mm

## 7. Discretizzazione

Su una griglia di lato $h$ una maschera binaria è un insieme di $N_h$ voxel, e il volume stimato è

$$\hat V_h = N_h \, h^3 .$$

Un voxel vale $1\ \text{mm}^3$ a 1 mm e $8\ \text{mm}^3 = 0{,}008\ \text{ml}$ a 2 mm. A parità di campo visivo la griglia a 2 mm ha $8$ volte meno voxel ($902.629 \times 8 = 7.221.032$, § 5). Ogni struttura più piccola di un voxel, o ogni bordo che lo attraversa, viene ridotta a una decisione 0/1.

## 8. Effetto di volume parziale

L'effetto di volume parziale nasce quando un voxel contiene più di un tessuto: il valore del voxel dipende dalle proporzioni dei tessuti, e una segmentazione binaria voxel per voxel che lo ignora introduce errori significativi nelle stime di volume [17, 18]. Per una maschera di lesione i voxel "misti" sono quelli attraversati dal bordo.

Una stima d'ordine di grandezza (derivazione elementare, non presa da una fonte): i voxel attraversati da un bordo di superficie $S$ sono circa $S/h^2$, ciascuno può essere sbagliato al più di $h^3$, quindi

$$|\hat V_h - V| \lesssim \frac{S}{h^2}\, h^3 = S\,h, \qquad \frac{|\hat V_h - V|}{V} \lesssim \frac{3h}{r} \ \text{per una sfera di raggio } r .$$

È un limite superiore: gli errori di bordo hanno segno variabile e in parte si compensano. Il limite cresce con $h$ e pesa di più sulle lesioni piccole: una lesione di raggio 3 mm ha un rapporto superficie/volume che a 2 mm la rende instabile, una di raggio 20 mm no.

## 9. Ridurre la risoluzione: campionare o mediare

Portare una maschera da 1 a 2 mm si può fare in due modi concettualmente diversi:

- **Campionamento puntuale.** Si valuta l'interpolante nel centro di ogni voxel di destinazione. È ciò che fa `nilearn.image.resample_to_img`, che delega a `scipy.ndimage.affine_transform` con ordine 0 (`nearest`), 1 (`linear`) o 3 (`continuous`) (sorgente nilearn 0.14, `nilearn/image/resampling.py`).
- **Media pesata per area.** Ogni voxel di destinazione riceve la frazione del suo volume occupata dalla lesione (il volume parziale esatto, § 8), da risogliare poi.

Sulla coppia `res-1` → `res-2` di MNI152NLin6Asym i centri a 2 mm coincidono con centri a 1 mm (§ 5). Il campionamento puntuale legge quindi esattamente un voxel a 1 mm, e l'interpolazione **lineare dà lo stesso risultato di `nearest`**: un interpolante lineare valutato in un centro di voxel sorgente restituisce il valore di quel voxel. Verificato nel repo con `resample_to_img` su una maschera sintetica e i tre header delle maschere reali (LAS +90, RAS −90, RAS −91): output identici, valori solo 0 e 1. Per un header RAS −91 il risultato è esattamente `mask[1::2, 0::2, 0::2]`. La media pesata per area non è disponibile in `resample_to_img`.

Il campionamento puntuale su un reticolo sistematico è lo stimatore del volume per conteggio di punti della stereologia (principio di Cavalieri), non distorto quando la posizione del reticolo rispetto all'oggetto è casuale [19]. Le lesioni hanno posizioni varie rispetto alla griglia, e questo spiega perché sulla coorte il rapporto tra i volumi resti centrato su 1 (§ 10), pur con una varianza alta per le lesioni piccole.

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

**Il costo** è limitato ai soggetti a 1 mm genuino (534: PASPORT, WAKEUP) e riguarda le lesioni più piccole. È il motivo per cui `lesion_metadata.csv` conserva entrambe le griglie: distingue una maschera vuota da una lesione persa nel campionamento.

---

# Parte 3 — Rimozione delle colonne costanti

## 13. Definizione

Sia $X \in \mathbb{R}^{n \times p}$ la matrice soggetti × voxel e $x_{\cdot j}$ la sua colonna $j$. La colonna è **costante** se $\min_i x_{ij} = \max_i x_{ij}$, cioè se la sua varianza campionaria

$$s_j^2 = \frac{1}{n-1}\sum_{i=1}^{n}\left(x_{ij} - \bar x_j\right)^2$$

è zero. Per una colonna binaria con frequenza di lesione $\hat p_j = \bar x_j$ la varianza (non corretta) è $\hat p_j(1-\hat p_j)$ [23], nulla se e solo se $\hat p_j \in \{0, 1\}$: voxel mai lesionato o lesionato in tutti i soggetti. In una matrice di lesioni ictali il secondo caso non si presenta; il primo riguarda la maggior parte della griglia (fuori dal cervello, e dentro il cervello i voxel mai colpiti nella coorte). In `s1.4-vol` sopravvivono 221.955 colonne su 902.629.

## 14. Perché si tolgono

- **Nessuna informazione.** Una colonna costante ha lo stesso valore per tutti i soggetti: non può distinguerne due. Rimuovere le feature a varianza nulla è la selezione di base che scikit-learn offre come default di `VarianceThreshold` [23].
- **Standardizzazione.** La standardizzazione $z_{ij} = (x_{ij} - \bar x_j)/s_j$ non è definita per $s_j = 0$. `StandardScaler` di scikit-learn in quel caso lascia la colonna invariata con fattore di scala 1 [24], una scelta silenziosa; `src/analysis/covariance_pca.py` invece solleva un errore se `standardize=True` incontra una colonna costante.
- **PCA.** Una colonna costante, centrata, è tutta zero: ha riga e colonna nulle nella matrice di covarianza e non contribuisce a nessuna componente. Toglierla non cambia gli autovalori né i punteggi.
- **Distanze.** Una colonna costante contribuisce $0$ alla distanza euclidea, e una colonna tutta zero non entra né nell'intersezione né nell'unione di Jaccard/Dice e non cambia prodotti scalari e norme del coseno. **Una colonna tutta uno, invece, non è neutra** per Jaccard, Dice e coseno: aggiunge 1 sia all'intersezione sia all'unione (o al prodotto scalare e alle norme) e cambia il rapporto. Nella matrice di lesioni non esiste (§ 13), quindi la rimozione è neutra di fatto, non per costruzione.
- **Costo.** Le colonne passano da 902.629 a circa 222.000 (§ 11), un fattore 4 su memoria e tempo di ogni passo successivo.

## 15. Cosa dicono documentazione e letteratura

- **scikit-learn**: `VarianceThreshold` rimuove per default le feature a varianza nulla, "che hanno lo stesso valore in tutti i campioni"; con una soglia $> 0$ rimuove anche feature binarie quasi costanti, ad esempio con soglia $0{,}8 \times (1 - 0{,}8)$ quelle uguali in più dell'80% dei campioni [23].
- **Lesion-symptom mapping**: gli studi voxel-wise limitano l'analisi ai voxel colpiti da una quota minima di lesioni, per evitare che i risultati siano dominati da regioni colpite raramente [25, 26]. Valori riportati: 5% del campione [26], tipicamente $5 \le n \le 10$ pazienti [26], $\ge 5$ lesioni su 100 [25], almeno 3 pazienti in Griffis et al. 2020 [27]. Il criterio "è spesso scelto arbitrariamente, perché non esiste uno standard" [25], e scambia estensione spaziale dell'analisi con validità del test [26].

**La differenza con il repo.** Il criterio di lesion-symptom mapping serve a test statistici massivamente univariati, voxel per voxel. Il repo costruisce un embedding multivariato, e toglie **solo** le colonne esattamente costanti ($\hat p_j \in \{0, 1\}$): nessuna soglia minima di frequenza. **Scelta del progetto**: una soglia di frequenza sarebbe un parametro in più da giustificare e cambierebbe la distanza tra soggetti con lesioni in zone rare. Una variante con soglia non è stata provata.

**Per il disconnettoma voxel-wise** la definizione è la stessa ($\min = \max$ esatto), su valori continui: un rumore di arrotondamento (interpolazione `continuous`) basta a rendere non costante un voxel che vale zero per tutti, ed è uno dei motivi per cui la produzione non usa quell'interpolazione (`docs/dev/sdc_matrix.md`).

---

## Riferimento rapido

- Template: `assets/templates/tpl-MNI152NLin6Asym_res-{1,2}_{T1w,desc-brain_mask}.nii.gz`.
- Config: `reference_template_path`, `brain_mask_path` in `config/pipelines/build_lesion_matrix.json`, `build_sdc_matrix.json`, `compute_lesion_metadata.json` (`grids`).
- Codice: `src/features/lesion.py` (`load_reference_image`, `_drop_constant_features`), `src/features/sdc.py` (`_non_constant_voxel_mask`, `_stack_voxelwise_matrix`).

## Fonti

1. Evans AC, Janke AL, Collins DL, Baillet S (2012). Brain templates and atlases. *NeuroImage* 62:911-922. https://doi.org/10.1016/j.neuroimage.2012.01.024 — letto solo l'abstract.
2. Ciric R, Thompson WH, Lorenz R, et al. (2022). TemplateFlow: FAIR-sharing of multi-scale, multi-species brain models. *Nature Methods* 19:1568-1571. https://doi.org/10.1038/s41592-022-01681-2
3. McConnell Brain Imaging Centre (MNI), "MNI ICBM152 linear". https://nist.mni.mcgill.ca/?p=798 (consultato il 21-10-26).
4. Mazziotta J, Toga A, Evans A, et al. (2001). A probabilistic atlas and reference system for the human brain: International Consortium for Brain Mapping (ICBM). *Philosophical Transactions of the Royal Society B* 356:1293-1322. https://doi.org/10.1098/rstb.2001.0915
5. McConnell Brain Imaging Centre (MNI), "ICBM 152 Nonlinear 6th Generation". https://nist.mni.mcgill.ca/?p=858 (consultato il 21-10-26).
6. Grabner G, Janke AL, Budge MM, Smith D, Pruessner J, Collins DL (2006). Symmetric atlasing and model based segmentation: an application to the hippocampus in older adults. *MICCAI 2006*, LNCS 4191:58-66. https://doi.org/10.1007/11866763_8 — letto solo l'abstract.
7. FSL, documentazione ufficiale, "Standard templates and atlases". https://fsl.fmrib.ox.ac.uk/fsl/docs/other/datasets.html (consultato il 21-10-26).
8. TemplateFlow, `tpl-MNI152NLin6Asym/template_description.json`. https://github.com/templateflow/tpl-MNI152NLin6Asym/blob/master/template_description.json (consultato il 21-10-26).
9. Fonov VS, Evans AC, McKinstry RC, Almli CR, Collins DL (2009). Unbiased nonlinear average age-appropriate brain templates from birth to adulthood. *NeuroImage* 47(S1):S102 (abstract OHBM). https://doi.org/10.1016/S1053-8119(09)70884-5 — citato come indicato dall'MNI [11], non letto.
10. Fonov V, Evans AC, Botteron K, Almli CR, McKinstry RC, Collins DL (2011). Unbiased average age-appropriate atlases for pediatric studies. *NeuroImage* 54:313-327. https://doi.org/10.1016/j.neuroimage.2010.07.033
11. McConnell Brain Imaging Centre (MNI), "ICBM 2009 Nonlinear". https://nist.mni.mcgill.ca/?p=904 (consultato il 21-10-26).
12. TemplateFlow, `tpl-MNI152NLin2009cAsym/template_description.json`. https://github.com/templateflow/tpl-MNI152NLin2009cAsym/blob/master/template_description.json (consultato il 21-10-26).
13. fMRIPrep, documentazione ufficiale, "Defining standard and nonstandard spaces". https://fmriprep.org/en/stable/spaces.html (consultato il 21-10-26).
14. Foulon C, Cerliani L, Kinkingnéhun S, et al. (2018). Advanced lesion symptom mapping analyses and implementation as BCBtoolkit. *GigaScience* 7(3):1-17. https://doi.org/10.1093/gigascience/giy004
15. Foulon C. BCBlib, README del repository ufficiale. https://github.com/chrisfoulon/BCBlib (consultato il 21-10-26).
16. Bisogno AL, Pini L, Raccanello S, et al. (2025). Large-scale network topography of stroke predicts functional outcome after mechanical thrombectomy. *Brain Communications*. https://doi.org/10.1093/braincomms/fcaf285
17. González Ballester MA, Zisserman AP, Brady M (2002). Estimation of the partial volume effect in MRI. *Medical Image Analysis* 6:389-405. https://doi.org/10.1016/S1361-8415(02)00061-0
18. Tohka J (2014). Partial volume effect modeling for segmentation and tissue classification of brain magnetic resonance images: A review. *World Journal of Radiology* 6:855-864. https://doi.org/10.4329/wjr.v6.i11.855
19. Gundersen HJ, Jensen EB (1987). The efficiency of systematic sampling in stereology and its prediction. *Journal of Microscopy* 147:229-263. https://doi.org/10.1111/j.1365-2818.1987.tb02837.x — letto solo l'abstract.
20. nilearn, documentazione ufficiale, "Manipulating images: resampling" (§ 9.2.2.2). https://nilearn.github.io/stable/manipulating_images/manipulating_images.html (consultato il 21-10-26).
21. Thiebaut de Schotten M, Foulon C, Nachev P (2020). Brain disconnections link structural connectivity with function and behaviour. *Nature Communications* 11:5094. https://doi.org/10.1038/s41467-020-18920-9
22. Talozzi L, Forkel SJ, Pacella V, et al. (2023). Latent disconnectome prediction of long-term cognitive-behavioural symptoms in stroke. *Brain* 146:1963-1978. https://doi.org/10.1093/brain/awad013
23. scikit-learn, documentazione ufficiale, "Feature selection — Removing features with low variance". https://scikit-learn.org/stable/modules/feature_selection.html (versione 1.8, consultato il 21-10-26).
24. scikit-learn, documentazione ufficiale, `sklearn.preprocessing.StandardScaler` (attributo `scale_`). https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html (consultato il 21-10-26).
25. Karnath HO, Sperber C, Rorden C (2018). Mapping human brain lesions and their functional consequences. *NeuroImage* 165:180-189. https://doi.org/10.1016/j.neuroimage.2017.10.028
26. Sperber C, Karnath HO (2017). Impact of correction factors in human brain lesion-behavior inference. *Human Brain Mapping* 38:1692-1701. https://doi.org/10.1002/hbm.23490
27. Griffis JC, Metcalf NV, Corbetta M, Shulman GL (2020). Damage to the shortest structural paths between brain regions is associated with disruptions of resting-state functional connectivity after stroke. *NeuroImage* 210:116589. https://doi.org/10.1016/j.neuroimage.2020.116589
