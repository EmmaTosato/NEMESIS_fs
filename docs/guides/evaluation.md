# Guida ai notebook di valutazione del clustering

Due notebook sotto `notebooks/post-results_analysis/` (evaluation e comparison) lavorano su run di clustering già **prodotte** (`fine_tuning: false`, lette da `results/<lesion|sdc>/clustering/production/<metodo>/<embedding>/<run_name>/`). La scelta di `k`/iperparametri è fatta altrove (`clustering.py --fine_tuning true`, `tuning_results.csv`/`tuning_plot.png`): qui non si sceglie niente in automatico (`code_standards.md` §0), si leggono tabelle e grafici.

| Notebook | Domanda | Unità di analisi |
|---|---|---|
| `clustering_evaluation.ipynb` | com'è fatta questa run? | una run alla volta |
| `clustering_comparison.ipynb` | in cosa differiscono queste run? | due o più run |

## Scope: dove vive ogni analisi

Il criterio (empirica contro interpretativa) è in [`exploration.md`](exploration.md). Evaluation e comparison sono **empirici**, con una sola eccezione: la sezione 4 di evaluation descrive i cluster con le variabili cliniche, senza test. L'interpretazione (mappe, soggetti rappresentativi, composizione dei cluster) è nell'app Dash.

| Analisi | Notebook |
|---|---|
| Metriche geometriche e del modello di una run | `clustering_evaluation` (tutte le sezioni da 2 a 3.2 anche nell'app Dash: pannello "Valutazione del clustering"; la 4 è nel pannello "Descrizione del cluster") |
| Accordo tra partizioni (ARI/NMI/VI), contingency, abbinamento e Jaccard tra cluster di run diverse | `clustering_comparison` |
| Distanze tra cluster **nello spazio dell'embedding** (centroidi, Mahalanobis, linkage) | `clustering_comparison` |
| Tabelle descrittive per cluster su età, sesso, NIHSS, volume, dataset, lato, sede dominante (nessun test) | `clustering_evaluation`, sezione 4 |
| Mappe di overlap e disconnessione, soggetti rappresentativi | app Dash |
| Distanze tra cluster **nello spazio delle mappe o del profilo clinico** | nessun notebook (non implementato) |
| Perché due cluster abbinati differiscono (A∩B, A\B, B\A descritti con le variabili esterne) | nessun notebook (non implementato) |

I casi di confine seguono il criterio: una distanza calcolata sulle coordinate dell'embedding è empirica; una calcolata su mappe anatomiche o variabili cliniche descrive i cluster ed è interpretativa. Un'analisi che serve a entrambi i notebook (l'abbinamento dei cluster) vive come funzione in `src/analysis/`, perché i notebook non si importano tra loro.

**Stato attuale.** `clustering_evaluation` non contiene più l'associazione con le variabili cliniche, i centroidi, i soggetti rappresentativi né i grafici (i plot di `clustering.py` si guardano direttamente in `results/`). L'associazione è sostituita dalla descrizione per cluster della sezione 4, senza test; centroidi e soggetti rappresentativi sono nell'app Dash. `clustering_comparison` ha ancora le sezioni della versione unica, con la vecchia numerazione e il profilo clinico per cluster della Parte 2 §3.

Sono notebook locali, non pipeline CLI:

```bash
conda activate nemesis
jupyter lab notebooks/post-results_analysis/clustering_evaluation.ipynb
```

Nessun dataset sintetico: le run si scelgono a mano in `SELECTED_RUNS` (path della colonna `output` di `list_production_runs`).

---

## `clustering_evaluation.ipynb` — una run alla volta

Ogni sezione è un **metodo di valutazione** (una metrica o un gruppo di metriche lette insieme) e riporta quattro cose: che metodo è, cosa fa, come si legge, a quali metodi di clustering si applica.

L'applicabilità è verificata dal codice: `src/analysis/clustering_evaluation.py` tiene il registro `EVALUATIONS` (valutazione → metodi) e `require_applicable`, che solleva `ValueError` per un metodo non previsto. Nel notebook `applicable_runs(valutazione)` salta le run non applicabili stampando il motivo (una riga per metodo); se non ne resta nessuna la sezione non produce niente, senza errore. Un test (`tests/unit/test_clustering_evaluation.py`) garantisce che il registro nomini solo metodi di `CLUSTERING_METHODS`.

| Sezione | Metodo di valutazione | Metodi di clustering | Codice |
|---|---|---|---|
| 2 | Metriche geometriche: Silhouette, Calinski-Harabasz, Davies-Bouldin, Dunn | tutti tranne adp | `clustering_tuning.compute_clustering_metrics`, `dunn_index` |
| 2.1 | Silhouette per cluster (micro, macro, minimo) | tutti tranne adp | `clustering_evaluation.per_cluster_silhouette` |
| 2.2 | Purezza dei k vicini, silhouette sulla distanza dice e quota di coppie a distanza 1 | adp | `clustering_evaluation.knn_purity`, `distance_matrix_silhouette`, `saturated_pair_share` |
| 3 | Metriche del modello: `inertia`, `bic`/`aic`, `cophenetic_correlation`/`dendrogram_jump`, `noise_fraction`/`n_clusters_found` | kmeans, gmm, agglomerative, hdbscan, hdbscan_soft | `clustering_evaluation.model_fit_metrics` |
| 3.1 | Posizione nel cluster: probabilità media e quota sotto soglia per cluster | hdbscan | `clustering_evaluation.membership_confidence` |
| 3.2 | Appartenenza ai cluster: per cluster, probabilità media nel proprio e cluster più vicino; vettori medi; soggetti più deboli | hdbscan_soft | `clustering_evaluation.soft_membership_summary` |
| 4 | Descrizione dei cluster con le variabili di `participants.csv`: soggetti con il dato, media ± deviazione standard, mediana [Q1–Q3], percentuali per categoria; nessun test | tutti | funzioni del notebook (`registry_frame`, `coverage_table`, `describe_clusters`) |

### Due modi di arrivare ai dati

Una run di clustering vive in uno di due spazi, e da questo dipende quali sezioni la riguardano:

- **Embedding** (UMAP a 2 o 10 componenti): `agglomerative`, `hdbscan`, `hdbscan_soft`, `kmeans`, `gmm`, `spectral`. `X` è l'embedding.
- **Dato grezzo** (`reduction_method == "raw"`): `adp` e le run `sdc` fatte sulla matrice non ridotta. `X` è la matrice delle feature, non un embedding.
  - `adp` sulla matrice delle lesioni (circa 220 mila voxel per soggetto) o sul disconnettoma voxelwise, distanza dice. Ha la sezione 2.2 al posto della 2 (vedi sotto).
  - Le run `sdc` su dato grezzo (la matrice `stream`, 87 colonne, una per tratto) sono euclidee e di poche colonne: valgono le stesse sezioni degli embedding.

### Parametri del notebook (evaluation)

Tutti si modificano a mano nelle celle indicate; i valori sono quelli di partenza.

| Parametro | Dove | Cosa fa |
|---|---|---|
| `OBJECT_TYPE` | sezione 1 | `"lesion"` o `"sdc"`: in quale albero `results/<tipo>/clustering/production/` cercare |
| `PREFIX` | sezione 1 | data della run, con cui inizia il nome della cartella (es. `"12-10_"`) |
| `METRIC` | sezione 1 | pezzo del nome della cartella che identifica la metrica dell'embedding a monte (es. `"_m_dice_"`). `None` per le run su dato grezzo (sdc), il cui nome non la contiene |
| `METHODS` | sezione 1 | metodi da cercare, per esempio `["kmeans", "hdbscan"]`; le run trovate hanno come nome `<metodo>_<resto del nome della cartella>` |
| `SELECTED_RUNS` | sezione 1 | dizionario nome leggibile -> path della colonna `output`. Lo riempie la cella di ricerca, ma si possono aggiungere run a mano, anche di tipo diverso (lesion e sdc insieme). Una cartella che `runs.csv` elenca ma che non esiste più viene saltata con un messaggio |
| `NOISE_WARNING_FRACTION` | sezione 2 | quota di rumore (0,10) sopra cui compare un avviso; non è un giudizio di qualità, dice solo che gli indici descrivono una parte dei soggetti |
| `K_NEIGHBORS` | sezione 2.2 | quanti vicini guarda la purezza (10) |
| `LOW_PROBABILITY` | sezione 3.1 | soglia di esempio (0,5) sotto cui un soggetto è periferico |
| `LOW_MEMBERSHIP`, `N_LOWEST` | sezione 3.2 | soglia di esempio (0,5) sotto cui un soggetto non sta chiaramente nel suo cluster; quanti soggetti più deboli mostrare per run (10) |
| `DESCRIBED_RUN` | sezione 4 | nome di una run di `SELECTED_RUNS`; `None` = la prima caricata |
| `MAX_MISSING_LISTED` | utils, sezione 4 | una variabile mancante a non più di tanti soggetti (10) non entra nella tabella di copertura |

`LOW_PROBABILITY` e `LOW_MEMBERSHIP` sono esempi, non valori della letteratura: si cambiano liberamente.

### Cose che non si vedono dal registro

- **Metriche geometriche**: assumono distanza euclidea e cluster compatti e convessi, quindi favoriscono kmeans/gmm. `compute_clustering_metrics(combo_params=...)` rifiuta una run con `metric`/`affinity` non euclideo. Valori di embedding diversi (lesion vs sdc) non sono confrontabili.
- **Metriche del modello**: kmeans, gmm e agglomerative vengono rifittati con i parametri della run e accettati solo se riproducono esattamente le etichette salvate (altrimenti `ValueError`, tipico di `random_state` non fissato). `inertia` e BIC/AIC non sono sulla stessa scala.
- **Posizione nel cluster**: `probabilities_` di HDBSCAN è normalizzata dentro ogni cluster (0 per il rumore), quindi dice quanto un soggetto sta nel nucleo **del suo** cluster. Non è la probabilità di stare in quel cluster invece che in un altro, e non è confrontabile tra cluster di densità diversa. Esiste solo sullo stimatore: la run viene rifittata con i suoi parametri e accettata solo se riproduce le etichette salvate. La soglia (`LOW_PROBABILITY`) non ha un riferimento in letteratura. È calcolata sulla densità dello spazio clusterizzato: su un embedding con `min_dist=0` descrive quanto UMAP ha impacchettato il cluster, non è un indice di validità.
- **Appartenenza ai cluster (hdbscan_soft)**: legge `membership.npy`, la matrice soggetti x cluster che una run di produzione di `hdbscan_soft` salva (`soft_membership_matrix`), senza rifittare; `membership_own` in `metadata.csv` è la probabilità del soggetto nel proprio cluster (NaN per il rumore, che non ha un cluster proprio). Le righe della matrice non sommano a 1: la parte mancante è la probabilità di essere rumore, quindi un soggetto con probabilità bassa ovunque è debole, non conteso. Una run senza `membership.npy` o con tutti i soggetti rumore solleva. Non è confrontabile con la 3.1: un'altra implementazione di HDBSCAN e un'altra grandezza.
- **Descrizione clinica (sezione 4)**: una run alla volta (`DESCRIBED_RUN`, `None` = la prima caricata), non passa dal registro `EVALUATIONS` perché vale per tutti i metodi e usa solo le etichette. Le variabili vengono da `participants.csv`, mai dal `metadata.csv` della run; un soggetto non registrato resta con valori mancanti e viene segnalato; il rumore di hdbscan è escluso. NIHSS e istruzione mancano per interi dataset (UCL-UK non li ha). La disconnessione media non è tra le variabili: è il carico diviso per una costante.
- **Silhouette e rumore**: se la quota di rumore supera `NOISE_WARNING_FRACTION` (10%) la cella della sezione 2 stampa un avviso: gli indici descrivono allora solo i soggetti non-rumore.
- **Rumore di hdbscan**: escluso dagli indici geometrici; la sua quota è sempre mostrata (`noise_fraction`).
- **adp**: clusterizza il dato grezzo, quindi `X` è la matrice delle feature (soggetti x voxel) e non un embedding: `load_run` la apre con `mmap` e la marca `is_raw`.
  - Sezione 2: le metriche geometriche non si applicano (il registro rifiuta adp): `compute_clustering_metrics` rifiuta `dice`/`jaccard`. Per adp la 2.2 dà due letture sulla distanza con cui ha clusterizzato, nella stessa tabella (i soggetti con riga vuota, etichettati `-1`, restano fuori). La purezza dei k vicini dipende solo dall'ordine dei vicini; un cluster con `K_NEIGHBORS` o meno soggetti non è valutabile. La silhouette sulla distanza dice è riportata con `pairs_at_distance_1`, la quota di coppie a distanza esattamente 1: sulle lesioni è l'84% e la silhouette è inutilizzabile (lettura: purezza), sulle mappe sdc è lo 0,0015% e la silhouette si legge normalmente.
  - Sezione 3: saltata (nessuna statistica propria).
- **DBCV** è escluso (già scartato nel tuning, `docs/guides/clustering.md`).

Lesion e sdc possono convivere nella stessa `SELECTED_RUNS`: ogni run è valutata da sola. Dopo la selezione una cella svuota `runs` e carica solo le run scelte: senza quella cella nessuna sezione produce niente.

### Come si leggono le sezioni

Nessuno degli indici sotto ha un valore di riferimento proprio per una run sola: si leggono per direzione e per confronto, mai come "buono/cattivo". Le uniche fasce citate in letteratura (solo per la silhouette, Kaufman & Rousseeuw) sono una convenzione, non un risultato, e il progetto non le usa: cosa sono e a cosa si riferiscono è in [`evaluation_metrics.md`](../../knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md), §2.

**Sezione 2, metriche geometriche** (spazio della run, rumore di hdbscan escluso)

| Indice | Direzione | Cosa misura |
|---|---|---|
| Silhouette | più alto è meglio, da -1 a 1 | per ogni soggetto, distanza media dal proprio cluster contro quella dal cluster più vicino. Vicino a 1: cluster netti. Vicino a 0: confini ambigui. Negativo: il soggetto è più vicino a un altro cluster che al proprio |
| Calinski-Harabasz (CH) | più alto è meglio | dispersione tra i cluster divisa per la dispersione dentro i cluster |
| Davies-Bouldin (DB) | più basso è meglio | per ogni cluster il caso peggiore del rapporto tra la sua dispersione e la vicinanza al cluster più simile, poi la media; 0 = cluster compatti e separati |
| Dunn | più alto è meglio | distanza minima tra due cluster divisa per il diametro massimo di un cluster; sensibile agli outlier |

- La tabella aggiunge: numero di cluster, quota del cluster più grande (`largest_cluster_share`), quota di rumore (`noise_fraction`) e `silhouette_min`, la silhouette media del **cluster peggiore** (il `minimum` della 2.1).
- Una nuvola senza cluster, divisa da un algoritmo, ha comunque una silhouette positiva: il valore da solo non dice se c'è struttura. CH, DB e Dunn di una run sola non hanno una scala. Embedding diversi (2 o 10 componenti, lesion o sdc) non sono confrontabili.
- Gli indici assumono cluster compatti e convessi: favoriscono `kmeans` e `gmm`, per gli altri metodi un valore basso non dimostra che i cluster siano sbagliati.

**Sezione 2.1, silhouette per cluster**

- Tre sintesi: **micro** (media sui soggetti, pesa di più i cluster grandi), **macro** (media delle medie dei cluster, ogni cluster pesa uguale), **minimum** (il cluster peggiore). Per cluster, `silhouette_mean` e `share_negative` (quota di soggetti con silhouette negativa).
- Un cluster con silhouette media bassa, o con molti soggetti negativi, ha confini ambigui anche se la media complessiva è buona. Se micro e macro sono molto diversi, cluster grandi e piccoli hanno qualità diversa.
- Il **minimum si legge insieme a `n`**: un cluster di un solo soggetto ha silhouette 0 per convenzione, uno di 2 o 3 soggetti può avere una media estrema per caso.

**Sezione 2.2, adp**

- **Purezza**: da 0 a 1, la quota dei `K_NEIGHBORS` vicini più prossimi (distanza dice) che sta nello stesso cluster del soggetto. Si legge accanto a `chance`, il valore atteso con etichette indipendenti dalla geometria: (n_c - 1)/(n - 1) per un cluster di n_c soggetti su n. Un cluster con `K_NEIGHBORS` soggetti o meno non può raggiungere 1: `evaluable` è False e resta fuori dal riassunto. `tied_share` è la quota di soggetti con vicini a pari distanza, dove la scelta tra i pari distanza è a caso.
- **`pairs_at_distance_1`**: la quota di coppie senza voxel in comune. Va guardata prima della silhouette.
  - **Alta** (lesioni: 84%): quasi tutte le distanze valgono 1, quindi la distanza media da un cluster intero è dominata da coppie a distanza 1 anche se il soggetto ha alcuni vicini veri. La silhouette sta vicino a 0 qualunque sia la struttura: si ignora e si usa la purezza.
  - **Bassa** (sdc: 0,0015%): le distanze sono varie e la silhouette si legge come nella 2.1. Può comunque restare bassa con una purezza alta: la purezza guarda i `K_NEIGHBORS` vicini più prossimi, la silhouette la distanza media da interi cluster, quindi i vicini possono essere coerenti senza che i cluster siano ben separati in media.
- La silhouette è quella della 2.1 (micro, macro, minimum, rumore escluso), ma sulla distanza dice: non è confrontabile con quella euclidea delle run su embedding.
- La purezza è in parte circolare: adp forma i cluster proprio su questi vicini, quindi una purezza alta dice che i cluster sono coerenti, non che siano "veri".
- La matrice delle distanze tra soggetti (`raw_distance`) si calcola una volta per coppia (`input_path`, metrica) e resta in memoria nel kernel: le run adp della stessa matrice la condividono. I soggetti con la riga tutta a zero hanno dice indefinita (denominatore 0): adp li etichetta `-1` e restano fuori. I tempi della matrice nell'app sono in `docs/guides/embedding_app.md` ("Run `adp`").

**Sezione 3, metriche del modello**

| Statistica | Metodo | Lettura |
|---|---|---|
| `inertia` | kmeans | somma delle distanze al quadrato dai centroidi; più bassa è meglio, ma cala sempre al crescere di k: utile solo guardando come cala (gomito) |
| `bic`, `aic` | gmm | verosimiglianza penalizzata per la complessità; più basso è meglio, il BIC penalizza di più |
| `cophenetic_correlation`, `dendrogram_jump` | agglomerative | cofenetica: correlazione tra le distanze vere e quelle dell'albero, più è alta più l'albero è fedele (non si confronta tra metriche diverse). Salto: altezza della fusione da k a k-1 divisa per quella da k+1 a k, vicino a 1 non c'è un taglio naturale a k, più è alto più è netto |
| `n_clusters` | agglomerative | il k della run (da `n_clusters` nei suoi parametri), non una misura: è il numero di cluster a cui è letto il salto del dendrogramma, riportato accanto per sapere a quale taglio si riferisce |
| `noise_fraction` | hdbscan, hdbscan_soft | quota di soggetti senza cluster: molto alta = parametri troppo restrittivi |
| `n_clusters_found` | hdbscan, hdbscan_soft | è un risultato, non un parametro: molti cluster piccoli = parametri troppo permissivi |

**Sezione 3.1, posizione nel cluster (hdbscan)**

- La probabilità (da 0 a 1) è calcolata **dentro ogni cluster**: vicino a 1 il soggetto sta nel cuore, vicino a 0 sta al margine (assegnato comunque a quel cluster, ma per poco non è rumore). Un soggetto con 0,2 non è incerto tra due cluster: è in periferia del suo.
- Per cluster: `n` (rumore escluso), `probability_mean` (vicino a 1 = cluster quasi tutto nucleo), `share_below_threshold` (quota sotto `LOW_PROBABILITY`). Un cluster con `share_below_threshold` alta è fatto soprattutto di soggetti al margine.
- `LOW_PROBABILITY` è un esempio: in letteratura non c'è una soglia di riferimento.

**Sezione 3.2, appartenenza ai cluster (hdbscan_soft)**

| Tabella | Lettura |
|---|---|
| per cluster | `n`, `own_mean` (media della probabilità dei suoi soggetti di stare in quel cluster), `share_below_threshold` (quota sotto `LOW_MEMBERSHIP`), `top_other` e `top_other_mean` (l'altro cluster a cui i suoi soggetti appartengono di più, in media, e quanto) |
| vettori medi | righe: cluster di appartenenza (e -1 per il rumore); colonne: tutti i cluster. La diagonale è `own_mean`; fuori diagonale si vede quali cluster si sovrappongono |
| soggetti più deboli | i `N_LOWEST` soggetti con la probabilità più bassa nel proprio cluster, con l'altro cluster più probabile e la sua probabilità (solo se i cluster sono più di uno) |

- Il rumore non ha un cluster proprio: è fuori da `own_mean` e dalla quota sotto soglia e ha una riga a parte nei vettori medi.
- Le righe della matrice non sommano a 1 (la parte mancante è la probabilità di essere rumore): un soggetto con 0,4 nel proprio cluster e 0,1 negli altri è debole, vicino al rumore; uno con 0,4 e 0,35 in un altro cluster è conteso tra i due.

**Sezione 4, descrizione clinica**

- **Tabella "soggetti con il dato"**: per cluster (e per tutti insieme nell'ultima riga), quanti soggetti hanno la variabile e che quota sono sul cluster. Una variabile che manca a non più di `MAX_MISSING_LISTED` soggetti non è nella tabella: una riga di avviso sopra dice che tutti ce l'hanno, oppure elenca chi manca e il suo cluster. Un valore vuoto conta come mancante, come NaN.
- **Media ± deviazione standard e mediana [Q1-Q3]**: sui soli soggetti che hanno il dato. Per le variabili asimmetriche, come il volume della lesione, la mediana descrive il cluster meglio della media.
- **Percentuali per categoria**: quota di ogni categoria nel cluster, sui soli soggetti che hanno il dato.
- **Nessun test**: le differenze tra cluster si leggono a occhio, tenendo il numero di soggetti accanto. Con pochi soggetti una mediana è instabile, e nessun numero dice se una differenza supera il caso.
- **Cautele**:
  - volume della lesione (run lesion) e carico di disconnessione (run sdc) derivano dai dati con cui è fatto il clustering: la differenza tra cluster è in parte per costruzione;
  - NIHSS e istruzione esistono solo per alcuni dataset: UCL-UK, il più grande, non ha nessuno dei due, quindi le loro righe poggiano solo sui dataset che li hanno e quanti soggetti sono lo dice la tabella di copertura;
  - se un cluster coincide quasi con un dataset, le altre differenze possono dipendere dal sito di provenienza e non dalla biologia: la tabella del dataset è il primo controllo da guardare.

---

## `clustering_comparison.ipynb` — due o più run

Contiene le analisi che mettono a confronto più run:

- Parte 1, **stessa pipeline** (stesso `object_type`; varia il metodo di clustering e/o `k`, mai la pipeline a monte): ARI/NMI a coppie (heatmap) e match matrix (contingency) tra due run sugli stessi soggetti, e distanza centroide-centroide tra run che condividono lo stesso embedding (`require_shared_embedding` solleva altrimenti);
- Parte 2, **cross-modalità** lesion vs sdc sull'intersezione dei `subject_id` (`aligned_labels_intersection` stampa N per lato, intersezione ed esclusi, mai un merge silenzioso): contingency grezza e normalizzata, ARI/NMI/homogeneity/completeness, chi-quadro con residui standardizzati, purezza per cluster, profilo clinico per cluster;
- Parte 3, **centroidi a selezione libera**: i centroidi di ogni run scelta, una alla volta (senza vincoli), e la distanza centroide-centroide solo per le coppie che condividono lo stesso embedding (le altre sono saltate stampando il perché, mai in silenzio);
- Parte 4, **due cluster della stessa run** (stesse funzioni di `src/analysis/cluster_pair.py`; la sezione corrispondente dell'app Dash non è montata, vedi `docs/dev/cluster_comparison.md`): profilo demografico e clinico (Mann-Whitney e Fisher, p corretto Benjamini-Hochberg), regressione logistica del cluster 1 contro il cluster 2 con grafico degli odds ratio, distanza tra i centroidi nell'embedding rapportata al raggio dei cluster, mappe di overlap della lesione dei due cluster e loro differenza. Si sceglie la run (`PAIR_RUN`) e i due cluster (`LABEL_1`, `LABEL_2`); il primo è il riferimento per il segno di `r`, degli odds ratio e della differenza. Le mappe leggono le maschere di tutti i soggetti dei due cluster (circa 1 minuto su ~900 soggetti) e richiedono i `.nii.gz` in `data/`. La disconnessione per le run sdc non è nel notebook.

Le Parti 1-3 sono ancora quelle della versione unica del notebook, in attesa di riorganizzazione.

### Come si leggono le sezioni

Le definizioni di ARI, NMI, homogeneity e completeness sono in `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md` (§6, indici esterni). Sono indici **esterni**: confrontano due partizioni tra loro, non misurano la qualità di una sola.

**Prima di confrontare**

- Le due run devono avere lo stesso ordine di `subject_id` (`aligned_labels` solleva altrimenti): run su soggetti diversi vanno allineate con un merge su `subject_id` prima di confrontare le etichette per posizione.
- Per run di pipeline diverse (lesion vs sdc) i soggetti sono diversi per costruzione: `lesion` include soggetti senza un disconnettoma SDC calcolato, e viceversa. Il confronto si fa quindi sull'**intersezione** dei `subject_id`, riportata esplicitamente.
- Si confrontano lesion e sdc con lo **stesso metodo e lo stesso k**, così l'unica cosa che varia è la pipeline a monte e non anche il criterio di clustering.

**Heatmap ARI/NMI** (una cella per coppia di run)

- La matrice è simmetrica (l'ordine delle due run non conta) e la diagonale vale sempre 1 (una run con se stessa): si ignora. Il notebook mostra solo il triangolo sotto la diagonale, diagonale esclusa.
- Scala viridis da 0 a 1: viola/blu scuro = accordo basso, verde = medio, giallo = alto.
- A parità di somiglianza reale NMI esce di solito più alto di ARI: i colori dei due pannelli non coincidono cella per cella.
- Scala di lettura del numero (`AGREEMENT_SCALE` in `src/analysis/cluster_comparison.py`): una **regola empirica** nostra, senza una fonte in letteratura.

  | ARI | NMI | Lettura |
  |---|---|---|
  | < 0,2 | < 0,3 | accordo debole/trascurabile |
  | 0,2-0,4 | 0,3-0,5 | moderato |
  | 0,4-0,6 | 0,5-0,7 | discreto |
  | 0,6-0,8 | 0,7-0,85 | forte |
  | > 0,8 | > 0,85 | quasi identiche |

**Match matrix** (contingency tra due run)

- Righe = cluster della run A, colonne = cluster della run B; la cella (i, j) è il numero di soggetti che stanno nel cluster i di A **e** nel cluster j di B. È sovrapposizione soggetto per soggetto ed è la base da cui derivano ARI e NMI.
- Le etichette numeriche sono assegnate arbitrariamente da ciascun algoritmo: "cluster 0 di A" non è "cluster 0 di B". Non si cerca una corrispondenza tra numeri: si guarda dove va la massa.
- Massa concentrata in una colonna: quel cluster di A corrisponde (quasi) per intero a un cluster di B, accordo. Massa sparsa su più colonne: i due metodi lo dividono diversamente, disaccordo.
- Non è simmetrica come ARI/NMI: righe e colonne sono due run diverse, l'ordine conta. La somma di riga è la dimensione del cluster in A, la somma di colonna quella del cluster in B.

**Percentuali per riga e per colonna** (cross-modalità)

- **Per riga** (somma 100 su ogni riga): per ogni cluster lesionale, come si distribuisce nei cluster sdc. Risponde a: "il cluster X finisce prevalentemente in un solo cluster sdc o si spalma su più?".
- **Per colonna** (somma 100 su ogni colonna): per ogni cluster sdc, da quali cluster lesionali proviene. Risponde alla domanda simmetrica: "il cluster Y è fatto di soggetti di un solo cluster lesionale o è un mix?".
- Servono entrambe perché con cluster di dimensioni molto diverse un conteggio alto in una cella può essere "quasi tutto il cluster" in un verso e "una frazione minima" nell'altro, a seconda delle somme di riga e di colonna.

**ARI, NMI, homogeneity, completeness**

- NMI, con la normalizzazione di default di scikit-learn, è la media armonica di homogeneity e completeness. Per questo **nasconde l'asimmetria** tra le due: due coppie di run con la stessa NMI possono avere pattern di disaccordo opposti, e uno scenario "homogeneity bassa + completeness alta" (o il contrario) è invisibile guardando solo ARI/NMI. Si guardano quindi homogeneity e completeness **separatamente**.
- **Homogeneity**: quanto ogni cluster di A contiene soggetti di un solo cluster di B (1 quando A raffina B). **Completeness**: quanto i soggetti di un cluster di B restano insieme in un solo cluster di A (1 quando B raffina A). La direzione è fissata in `docs/dev/cluster_comparison.md`.
- Lettura: tutte in [0, 1] (ARI può scendere sotto 0); vicino a 1 = corrispondenza forte, vicino a 0 = nessuna relazione. Se sono tutte alte, le due pipeline catturano la stessa struttura; se sono sbilanciate o basse, si torna alla contingency e ai residui per vedere quali cluster causano lo squilibrio.

**Chi-quadro e residui standardizzati**

- Test chi-quadro di indipendenza sulla contingency. H0: l'appartenenza al cluster lesion è indipendente da quella al cluster sdc. La tabella degli **attesi** è quella che ci si aspetterebbe sotto H0, calcolata dai totali di riga e di colonna.
- Il **residuo standardizzato** di Pearson di una cella è (osservato - atteso) / radice(atteso): lo scarto in unità di deviazione standard, come uno z-score.
- Il p-value dice **se** le due partizioni sono associate (p basso: non indipendenti); i residui dicono **dove**, cioè quali coppie di cluster determinano l'associazione. Heatmap dei residui: rosso = la coppia co-occorre **più** del previsto, blu = **meno**, vicino a 0 = in linea con l'indipendenza.
- Il test richiede almeno 2 cluster per lato (`chi_square_independence` solleva altrimenti).

**Purezza per cluster**

- Per ogni cluster sorgente (riga della tabella per riga): `dominant_target_cluster` è il cluster di destinazione con la quota più alta, `purity_pct` quella quota in %. La tabella è ordinata dal cluster **meno puro** (disperso su più destinazioni) al più puro (converge quasi tutto in uno).
- Purezza alta: corrispondenza netta con un solo cluster di destinazione. Bassa o moderata: il cluster si spezza su più destinazioni. Le prime righe sono i cluster da investigare, le ultime le corrispondenze più solide.
- È **metà del quadro**: dice quanto un cluster sorgente converge in una destinazione (circa l'homogeneity del singolo cluster), non se quella destinazione è a sua volta "posseduta" solo da quel sorgente (il corrispettivo della completeness, da leggere sulla tabella per colonna).

**Centroidi**

- Un confronto diretto dei centroidi tra lesion e sdc **non ha senso**: vivono in spazi di feature diversi (voxel della lesione contro regioni SDC) e le coordinate, anche se entrambi gli embedding sono 2D, non sono la stessa grandezza. Il sostituto valido è il **fenotipo clinico di ciascun cluster** (profilo per cluster, Parte 2), che non dipende dalle coordinate.
- La distanza centroide-centroide ha senso solo se le due run condividono lo stesso embedding: stessi `session_name`, `reduction_method`, `reduction_n_components`, `reduction_metric` (quindi stesso `input_path` della dim reduction). Non basta che il metodo di clustering sia diverso: due embedding diversi condividono lo stesso spazio solo per coincidenza numerica. `require_shared_embedding` solleva se una delle quattro chiavi differisce; nella Parte 3 le coppie incompatibili sono saltate stampando il motivo.

**Parte 4, due cluster della stessa run**

- Il **primo cluster** (`LABEL_1`) è il riferimento: il segno di `r`, degli odds ratio e della mappa di differenza dipende da lui, e scambiare i due cluster inverte tutto. Le variabili cliniche vengono sempre da `participants.csv`, mai dal `metadata.csv` della run.
- **Variabili numeriche**: Mann-Whitney; `r` è la correlazione rank-biserial, tra -1 e 1, positiva se il cluster 1 ha valori più alti. **Categoriche**: test esatto di Fisher per ogni categoria; l'odds ratio è sopra 1 se la categoria è più frequente nel cluster 1.
- `p_fdr` è corretto per tutti i test insieme (Benjamini-Hochberg): si legge quello, non `p`.
- **Regressione logistica** sui soli soggetti dei due cluster, esito "sta nel cluster 1": odds ratio sopra 1 = la variabile rende più probabile il cluster 1, sotto 1 il cluster 2; per le numeriche è per una deviazione standard in più. Il punto è blu se l'intervallo di confidenza al 95% non contiene 1. È un'associazione, non una causa; se il volume della lesione è l'input del clustering (run lesion) è associato ai cluster anche per costruzione. Se la regressione non è stimabile (pochi soggetti, collinearità, separazione perfetta) solleva `ValueError` col motivo (`docs/dev/cluster_drivers.md`).
- **Distanza tra i centroidi**: euclidea nello spazio dell'embedding, da leggere rispetto al **raggio** di ciascun cluster (la distanza media dei suoi soggetti dal proprio centroide): se la distanza è molto maggiore dei raggi, i cluster sono ben separati. Solo per le run su embedding, perché su una run su dato grezzo la matrice è lo spazio delle feature.
- **Mappe**: per ogni cluster la % di soggetti con lesione in ogni voxel, e la differenza cluster 1 - cluster 2 (rosso = lesione più frequente nel cluster 1, blu nel cluster 2).

---

## Lettura consigliata

- Le metriche intrinseche dicono se *quella* run è compatta e separata, non se è "giusta" rispetto a un'altra.
- ARI/NMI alti tra metodi diversi sono un segnale di convergenza, non una prova che `k` sia corretto. ARI/NMI bassi tra lesion e sdc non sono un errore: feature space diversi non hanno obbligo di produrre la stessa partizione.

Metodologia e letteratura: `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md`.
