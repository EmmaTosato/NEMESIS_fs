# Guida al Clustering (Raggruppamento)

Questa guida illustra l'uso dello script `clustering.py`. L'obiettivo è analizzare una matrice matematica di pazienti e raggrupparli automaticamente in "cluster" in base alla similitudine delle lesioni.

- **Script**: `src/pipeline/clustering.py`
- **Configurazione**: `config/pipelines/clustering.json`

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione.
```bash
sbatch jobs/run_clustering.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`, lanciare direttamente da terminale:
```bash
python -m src.pipeline.clustering --config config/pipelines/clustering.json
```

---

## Cos'è il Clustering?

Mentre la *Dim Reduction* semplifica le informazioni, il **Clustering fa un passo interpretativo**. Analizza le "distanze matematiche" tra i pazienti e raggruppa i soggetti "vicini" assegnando loro un'etichetta (es. "Tipo 1"). 

> **Consiglio**: È preferibile lanciare il clustering sulla matrice **compressa** dopo la *Dim Reduction* (2-3 componenti) piuttosto che sulla matrice parcellizzata grezza.

---

## Modalità di Funzionamento

### 1. Modalità Fine-Tuning (`"fine_tuning": true`)
Utilizzata per trovare la configurazione ottimale. Calcola indici interni di compattezza per ogni combinazione di parametri in `config/registry/params_clustering.json`.

- **Metriche calcolate**: Silhouette score, Calinski-Harabasz, Davies-Bouldin.
- **Specifiche per metodo**: K-Means calcola anche `inertia`; GMM calcola `bic`/`aic` — sweeppabile anche su `covariance_type` (`"full"`/`"tied"`/`"diag"`/`"spherical"`) insieme a `n_components`, uno sweep congiunto legittimo (a differenza di `linkage`/`metric` di Agglomerative o `k`/`init` di K-Means) perché AIC/BIC sono esattamente lo strumento statistico corretto per confrontare `covariance_type` diversi.
- **HDBSCAN (nuovo)**: `tuning_grid` sweeppa `min_cluster_size` x `min_samples` insieme, in un unico run (nessuna run ripetuta/sequenziale) — riusa la heatmap generica a 2 parametri. Niente DBCV/condensation tree (scelta deliberata: nemmeno l'esempio ufficiale sklearn li usa). In produzione, `cluster_plot.png` ha ora i marker dimensionati in base a `probabilities_` (confidenza di appartenenza al cluster) — i punti noise (label `-1`) hanno sempre probabilità 0 e restano visibili grazie a una dimensione minima.
- **HDBSCAN soft**: `tuning_grid` sweeppa `min_cluster_size` x `min_samples` x `cluster_selection_method` (`eom`/`leaf`). Una heatmap ha due assi: la run scrive un file per ogni valore di `cluster_selection_method`, `tuning_plot_cluster_selection_method=<valore>.png`, con `min_cluster_size` e `min_samples` sugli assi. In `tuning_results.csv` ci sono tre colonne in più (sezione "HDBSCAN soft" sotto).
- **Spectral (nuovo)**: `"assign_labels"` è ora fissato a `"cluster_qr"` in `params_clustering.json` (rimuove un'instabilità nascosta ereditata da k-means, di default sklearn userebbe `"kmeans"` per l'assegnazione finale delle etichette). `tuning_grid` può sweeppare `"affinity"` (`"nearest_neighbors"`/`"rbf"`) insieme al proprio iperparametro (`"n_neighbors"` per `nearest_neighbors`, `"gamma"` per `rbf`) — girano due sotto-sweep separati (uno per affinity) per non sprecare fit sull'iperparametro che non si applica, poi vengono uniti in un unico `tuning_plot.png` con una linea per ogni combinazione `(affinity, iperparametro)`. **Nota**: `save_tuning_clusterings: true` non è supportato insieme a `"affinity"` sweeppata (viene rifiutato con errore esplicito).
- **Grafici diagnostici**: Agglomerative genera un *dendrogramma* (un file `dendrogram_metric=<metric>.png` per ogni `metric` sweeppata, con un subplot per ogni `linkage` valido per quella metrica) + una *matrice di distanza interclasse* (una heatmap per ogni `metric` sweeppato, usa la colonna `"dataset"` dei metadati come proxy di ground-truth debole); Spectral genera un *eigengap plot* (un file `eigengap_affinity=<affinity>.png` per ogni `affinity` sweeppata, con un subplot per ogni valore del suo iperparametro `n_neighbors`/`gamma`). HDBSCAN non ne ha uno dedicato.
- **Sweep di Agglomerative su `linkage`/`metric` (nuovo)**: a differenza degli altri metodi, Agglomerative è deterministico (nessun `random_state`) — si può quindi sweeppare `n_clusters` x `linkage` x `metric` insieme, senza bisogno di un controllo di stabilità. Attenzione: `linkage="ward"` richiede `metric` euclideo (`"euclidean"`/`"l2"`) — ogni combinazione `ward`+metrica-non-euclidea viene automaticamente saltata (con warning nei log), mai fatta fallire. Per metriche non euclidee (`"cosine"`, `"manhattan"`, `"dice"`), Calinski-Harabasz/Davies-Bouldin non sono calcolabili (sono geometrici, solo euclidei) e compaiono come `NaN` in `tuning_results.csv` — il Silhouette resta sempre calcolato con la stessa metrica del clustering. Con 3 parametri sweeppati contemporaneamente, il grafico generico `tuning_plot.png` non viene generato (supportato solo per 1-2 parametri) — restano comunque i dendrogrammi e la matrice interclasse.
- **Scelta manuale**: Il sistema non sceglie in automatico, spetta all'utente leggere `tuning_results.csv` e grafici.
- **Consensus/Stability (Opzionale per KMeans/GMM/Spectral)**: 
  Aggiungendo un blocco `"consensus"` in `params_clustering.json`, si possono misurare le stabilità:
  - `"rsc"`: Ripete sui dati con seed casuali diversi (misura la dipendenza dall'inizializzazione).
  - `"monti"`: Sottocampionamento casuale (misura la dipendenza dal campione).
- **Stability analysis su init/n_init (Opzionale per KMeans/GMM)**:
  Aggiungendo un blocco `"stability"` in `params_clustering.json` (solo `"kmeans"`/`"gmm"`), si valida che la scelta di `init`/`n_init` (kmeans) o `init_params`/`n_init` (gmm) sia stabile *prima* di fidarsi dello sweep principale — a differenza dello sweep su `n_clusters`/`n_components`, `k`/`n_components` e `init` non vengono mai incrociati in una griglia congiunta (esplicitamente scartata come idea): la stability analysis gira separatamente, a 3 valori rappresentativi di `n_clusters`/`n_components` (min/mediana/max di quelli in `tuning_grid`). Scrive `stability_results.csv` + `stability_plot.png` (un pannello per valore rappresentativo, una linea per ogni candidato `init`/`init_params`, media ± deviazione standard vs `n_init`) accanto a `tuning_results.csv`. Formato del blocco:
  ```json
  "stability": {
    "nuisance_values": ["k-means++", "random"],
    "n_init_range": [1, 5, 10, 15, 20],
    "n_repeats": 5
  }
  ```

### 2. Modalità Produzione (`"fine_tuning": false`)
Genera i cluster definitivi usando i parametri precedentemente scelti in `config/registry/params_clustering.json`.

---

## Agglomerative

Parte con un cluster per soggetto e fonde via via i due cluster più vicini, fino a uno solo (l'albero delle fusioni). Il numero di cluster si sceglie dopo, tagliando l'albero. È deterministico: nessun `random_state`. Implementazione: `sklearn.cluster.AgglomerativeClustering`.

| Parametro | Cosa fa | Valori |
| :--- | :--- | :--- |
| **`n_clusters`** | Dove si taglia l'albero: quanti cluster restano. | Intero >= 2. Lo sweep prova ogni k da 2 a 30. |
| **`metric`** | Come si misura la distanza tra **due singoli soggetti**. Entra poi nel calcolo del linkage. | `euclidean`, `manhattan` (`l1`), `cosine`, più `dice` e `jaccard` calcolate dal progetto (sovrapposizione tra due mappe). |
| **`linkage`** | Come si misura la distanza tra **due gruppi** di soggetti, cioè il criterio con cui si decide quali due fondere. | `ward`, `average`, `complete`, `single`. |

**Il linkage** (sklearn: l'algoritmo fonde la coppia di cluster che minimizza questo criterio):

- **`ward`**: minimizza la varianza dei cluster che si fondono. Concettualmente vicino a K-Means, ma per via gerarchica. Dà cluster di dimensioni più regolari.
- **`average`**: media delle distanze tra tutte le coppie di soggetti dei due gruppi.
- **`complete`**: distanza massima tra le coppie di soggetti dei due gruppi. Favorisce cluster compatti.
- **`single`**: distanza minima tra le coppie, cioè i due soggetti più vicini. Tende a incatenare gruppi distinti attraverso pochi soggetti-ponte (*chaining*) ed è il meno robusto al rumore.

**Combinazioni valide.** `ward` accetta solo `euclidean`. Per le altre metriche si usa un altro linkage: sklearn indica `average` come alternativa quando la metrica non è euclidea. Lo sweep salta ogni coppia `ward` + metrica non euclidea e lo scrive nel log.

**Come scegliere la metrica** (sklearn): `manhattan` va bene con feature sparse, `cosine` è invariante alle scale globali del segnale. Il confronto tra metriche sullo stesso embedding si fa con la matrice di distanza interclasse (sezione "Grafici diagnostici" sopra).

**Valori di partenza** in `params_clustering.json`: `n_clusters: 6`, `linkage: average`, `metric: cosine`.

Fonte: [scikit-learn, `AgglomerativeClustering`](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html) e [guida al clustering gerarchico](https://scikit-learn.org/stable/modules/clustering.html#hierarchical-clustering).

---

## HDBSCAN

Cerca zone dense di soggetti, a densità diverse. Il numero di cluster **non si sceglie**: emerge dai dati. I soggetti che non stanno in nessuna zona densa non sono forzati in un cluster e prendono l'etichetta `-1` (rumore). Implementazione: `sklearn.cluster.HDBSCAN`. È deterministico.

| Parametro | Cosa fa | Effetto di un valore più alto |
| :--- | :--- | :--- |
| **`min_cluster_size`** | Numero minimo di soggetti perché un gruppo conti come cluster; i gruppi più piccoli restano rumore (con 50, un gruppo di 30 non è un cluster). | Meno cluster, più grandi; più soggetti scartati come rumore. |
| **`min_samples`** | Il `k` con cui si calcola la distanza di un soggetto dal suo k-esimo vicino, base della stima di densità. Controlla quanto il metodo tollera il rumore. | Metodo più conservativo: più soggetti nel rumore, zone dense più ristrette. |

- Con `min_samples` non specificato sklearn usa il valore di `min_cluster_size`. Il progetto li sweepa insieme in una sola run.
- La distanza è euclidea, perché HDBSCAN gira sull'embedding. Gli altri parametri di sklearn restano ai default: `cluster_selection_method="eom"` (sceglie i cluster più persistenti nell'albero) e `cluster_selection_epsilon=0`.
- Etichette: `-1` è il rumore. Dopo il fit, `probabilities_` dà per ogni soggetto la forza di appartenenza al suo cluster (0 per il rumore); in produzione dimensiona i marker di `cluster_plot.png`.
- Silhouette, CH e DB escludono il rumore: va letta sempre insieme a `noise_fraction` (vedi `knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md`).

**Valori di partenza** in `params_clustering.json`: `min_cluster_size: 100`, `min_samples: 10`.

Fonte: [scikit-learn, `HDBSCAN`](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html) e [guida al clustering](https://scikit-learn.org/stable/modules/clustering.html#hdbscan).

---

## HDBSCAN soft

Lo stesso algoritmo di HDBSCAN, con il pacchetto `hdbscan` al posto di quello di scikit-learn (`environment.yml`). Serve per il *soft clustering*: per ogni soggetto, una probabilità per ogni cluster. Come funziona il pacchetto: `knowledge/notes/dim_reduction_clustering/hdbscan_package.md`.

**Non è confrontabile con `hdbscan`.** I due non danno la stessa partizione con gli stessi numeri: il pacchetto usa un'altra convenzione per `min_samples` e un MST approssimato di default. Le run `hdbscan_soft` stanno in cartelle proprie (`.../tuning/hdbscan_soft/...`) e si leggono tra loro.

| Parametro | Cosa fa | Valore in `params_clustering.json` |
| :--- | :--- | :--- |
| **`min_cluster_size`** | Come in HDBSCAN. | base 100; griglia 10, 15, 20, 30, 50, 75, 100 |
| **`min_samples`** | La core distance è la distanza dal `min_samples`-esimo vicino. Più alto: più rumore. | base 10; griglia 1, 5, 10, 20 |
| **`cluster_selection_method`** | `eom`: pochi cluster grandi più tanti piccoli. `leaf`: cluster fini e omogenei. | base `eom`; griglia `eom`, `leaf` |
| **`approx_min_span_tree`** | Con `false` il risultato è quello esatto, non dipende dall'approssimazione. | fisso `false` |

`alpha` resta a 1 (la documentazione del pacchetto lo sconsiglia) e `allow_single_cluster` a falso. Il nome della cartella di produzione contiene `mcs`, `ms` e `sel_<metodo>`.

**Colonne in più in `tuning_results.csv`**, oltre a silhouette, CH, DB, `noise_fraction` e `n_clusters_found`:

| Colonna | Lettura |
| :--- | :--- |
| `membership_mean` | Media, sui soggetti non-rumore, della probabilità di stare nel **proprio** cluster (vettore soft). Vicino a 1 i soggetti stanno chiaramente nel loro cluster. |
| `membership_share_below_half` | Quota di soggetti non-rumore con quella probabilità sotto 0,5. |
| `persistence_mean` | Media della stabilità dei cluster (`cluster_persistence_`), da 0 (effimeri) a 1. |

Una combinazione senza nessun cluster (tutto rumore) ha queste tre colonne e quelle di silhouette a `NaN`, e un avviso nel log.

**Il vettore soft non somma a 1.** La parte mancante è la probabilità di essere rumore. Per un soggetto con etichetta `c`, la colonna `c` dice quanto appartiene a quel cluster; il rumore riceve comunque un vettore e si vede a quale cluster è più vicino.

**Tempi** (5845 soggetti): circa 30-55 secondi per 56 combinazioni su un embedding UMAP; circa 3 minuti sulla matrice grezza a 87 colonne.

**Tuning**: i vettori soft entrano solo come le tre colonne riassuntive, la matrice non viene salvata. **Produzione**: oltre a `matrix.npy` e `metadata.csv` (con `cluster_label`), la run salva `membership.npy` (soggetti × cluster; il numero di colonne è il numero di cluster, nessuna colonna se tutti i soggetti sono rumore) e la colonna `membership_own` in `metadata.csv`, la probabilità del soggetto nel proprio cluster (vuota per il rumore, che non ha un cluster proprio). In `cluster_plot.png` la dimensione dei marker segue `membership_own`. Si leggono nella sezione 3.2 di `clustering_evaluation.ipynb` (`docs/guides/evaluation.md`).

---

## ADP (DADApy)

*Advanced Density Peaks* (d'Errico et al. 2021, libreria `dadapy`) cerca i picchi di densità tra i soggetti: **il numero di cluster non si sceglie, emerge dai dati**. L'unico iperparametro che lo governa è `Z`, la soglia di significatività: un picco resta un cluster a sé solo se la sua densità supera quella del "passo" che lo collega al picco vicino di più di `Z` volte l'incertezza della stima. `Z` basso dà molti cluster piccoli, `Z` alto li fonde.

Si usa su una matrice **grezza** (lesione, SDC voxelwise, SDC streamline), non su un embedding: è l'unico metodo che clusterizza direttamente le distanze `dice`/`jaccard` della matrice.

### Ambiente e comando

`dadapy` dipende da `jax` e vive in un ambiente conda **separato** da `nemesis` (oggi `nemesis_fallback`: Python 3.11, `dadapy` 0.3.4, `numpy` 1.26.4, `scikit-learn` 1.9.1). L'import è lazy: in `nemesis` il registro dei metodi si carica comunque, ma una run `"adp"` solleva un errore che chiede di usare l'ambiente con `dadapy`. Per questo ha un config suo per ogni matrice (`config/pipelines/clustering_adp_<sessione>.json`, es. `clustering_adp_s2.2-vol.json`), con `"clustering_methods": ["adp"]` e nient'altro:

```bash
conda activate nemesis_fallback      # l'ambiente con dadapy
python -m src.pipeline.clustering --config config/pipelines/clustering_adp_<sessione>.json
```

L'ambiente `dadapy` non ha `dash`: `embedding_app` e i suoi test non vi girano. I risultati si leggono dall'ambiente `nemesis`.

### Parametri (`params_clustering.json`, voce `"adp"`)

| Parametro | Descrizione |
| :--- | :--- |
| **`metric`** | Come si misura la distanza tra due soggetti: `"dice"`, `"jaccard"` o `"euclidean"`. Su una matrice binaria `dice`/`jaccard` misurano la sovrapposizione tra due mappe; su una continua `>= 0` (SDC) sono le generalizzazioni pesate (Czekanowski/Ruzicka), che sulle matrici 0/1 coincidono con le classiche. |
| **`Z`** | Fattore di fusione dei picchi di densità (> 0, default DADApy 1.65). È l'unico parametro libero del metodo. Un picco resta un cluster a sé solo se la sua densità supera quella del punto più basso che lo collega a un picco vicino di più di `Z` volte l'incertezza della stima. **Più alto = fusione più aggressiva = meno cluster.** Lo sweep la varia da 0.25 a 16. |
| **`maxk`** | Numero massimo di vicini per soggetto su cui DADApy calcola distanze, dimensione intrinseca e densità (default DADApy `min(100, N-1)`). È un tetto: la stima di densità adatta il proprio numero di vicini, per ogni soggetto, entro `maxk`. Deve essere minore del numero di righe distinte. |

Fonte: [DADApy, `Clustering.compute_clustering_ADP`](https://dadapy.readthedocs.io/en/latest/clustering.html) (la documentazione ufficiale descrive `Z`, non `maxk`; per `maxk` vale il docstring nel codice di `dadapy.base`) e d'Errico, Facco, Laio, Rodriguez 2021, *Automatic topography of high-dimensional data sets by non-parametric density peak clustering*, Information Sciences 560.

Nessun parametro non elencato è accettato (un refuso solleva, non viene ignorato). `halo` è fisso a `false`; stima della dimensione intrinseca (2NN) e della densità (PAk) sono quelle di default di DADApy. Il metodo è deterministico: nessun `random_state`.

### Tuning

`tuning_grid` sweeppa `Z` e, per confrontare le distanze nella stessa run, `metric` (oggi `["dice", "euclidean"]`: una combinazione per ogni coppia, chiavi `metric=dice,Z=1.65` in `clusterings.npz`, una linea per metrica nel `tuning_plot.png`). Con una sola metrica, la chiave è `Z=1.65`. Densità e distanze si calcolano **una volta** per `metric`/`maxk`; ogni `Z` rifà solo il taglio dei picchi, quindi lo sweep costa quanto una run (circa 2 minuti su 1570 soggetti x 290940 voxel, con le distanze pesate in parallelo su tutti i core). Con più `metric` si calcola una matrice di distanze per ciascuna. La `silhouette` di due metriche non è confrontabile (ognuna usa la propria distanza): per confrontarle si usano la partizione (ARI tra le due) e le variabili esterne, come `lesion_side`.

`tuning_results.csv` ha, oltre ai valori sweeppati:

- `silhouette`, calcolata con la stessa distanza usata per clusterizzare (`dice`...), non con l'euclidea;

- `calinski_harabasz`, `davies_bouldin`: solo con `euclidean` (sono basate sui centroidi), `NaN` altrimenti; i due pannelli vuoti non vengono disegnati;

- `n_clusters_found`, `largest_cluster_share`, `n_small_clusters` (cluster con meno di 10 soggetti), `noise_fraction`;

- `id_2nn`: la dimensione intrinseca stimata, costante per `metric`/`maxk`;

- `ari_vs_prev_z`: ARI, sui soli soggetti clusterizzati, contro il `Z` immediatamente più basso (stesse altre impostazioni). Un tratto vicino a 1 è un plateau: la partizione non dipende dalla soglia.

`tuning_plot.png` ha `Z` in scala logaritmica e un pannello per ogni misura: `n_clusters_found`, `largest_cluster_share`, `ari_vs_prev_z`, `silhouette` (e `calinski_harabasz`/`davies_bouldin`, se la run ha `euclidean`), una linea per metrica. Con `save_tuning_clusterings: true` le partizioni sono in `clusterings.npz` con chiavi `Z=1.65` (formato letto dal notebook `clustering_tuning_explorer`, sezione ADP, che legge solo file già scritti: `dadapy` non serve).

**Come leggere lo sweep** (dettaglio in `knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md`, sezione "ADP"):

- `largest_cluster_share` vicino a 1: tutti i soggetti sono collassati in un gruppo.
- Un tratto di `Z` con `n_clusters_found` fisso e `ari_vs_prev_z` vicino a 1 è un plateau: il risultato non dipende dalla soglia. Se la partizione cambia a ogni passo, dipende dalla soglia e non dai dati.
- Un solo cluster a `Z` alto è il limite atteso: con una soglia severa nessun picco è significativo.
- Un numero di cluster che compare per un solo `Z` è un caso dello sweep.
- Il notebook riassume lo sweep in una tabella dei plateau: per ogni numero di cluster (e per ogni metrica), il `Z` minimo e massimo che lo producono e quanti valori dello sweep ci cadono.

### Soggetti che non entrano nel clustering

- **Riga a zero:** `dice`/`jaccard` non sono definite. La riga prende l'etichetta `-1` (rumore, come in HDBSCAN) **per ogni metrica**, così tutte le metriche clusterizzano gli stessi soggetti. Il run lo segnala a `WARNING` con l'indice di riga; `noise_fraction` ne riporta la quota.

- **Righe duplicate esatte:** a distanza 0 la stima di densità divide per zero. Le righe uguali si clusterizzano una volta sola e ogni duplicato prende l'etichetta del gemello; anche questo è loggato.

- Una matrice con tutte le righe a zero, o due righe diverse a distanza numericamente 0, solleva `ValueError`.

### Limiti da tenere presenti

- Le metriche geometriche del notebook di valutazione (`compute_clustering_metrics`) rifiutano `dice`/`jaccard`: assumono distanza euclidea. Per ADP si legge la `silhouette` del tuning, che usa la distanza giusta.

- Il grafico `silhouette_plot.png` di produzione usa la stessa distanza di `metric`.

- `cluster_plot.png` ha bisogno di un `viz_embedding_path` (la matrice grezza ha più di 3 colonne). L'UMAP di produzione è `euclidean`, ADP clusterizza con `dice`: le due viste non condividono la metrica.

- La memoria cresce con una matrice `N x N` in `float64` per ogni `metric` richiesta (circa 270 MB a 5800 soggetti).

---

## Dettaglio Parametri JSON (`clustering.json`)

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`project`** | *Stringa* | Nome del progetto (es. `"clinical_connectome"`). |
| **`input_path`** | *Stringa* | Percorso della matrice di input. Dati grezzi (`data/derived/...`) o compressi (`results/lesion/dim_reduction/...`). DEVE esistere. |
| **`reduction_method`** | *Stringa* | Dichiara quale metodo di dim reduction ha prodotto `input_path` (`"umap"`, `"tsne"`, `"pca"`, `"pacmap"`) — o `"raw"` se `input_path` è una matrice non ridotta. Obbligatorio, mai dedotto dal testo di `input_path`. Determina un livello in più nell'albero di output (vedi sotto), così risultati da embedding diversi non finiscono mai nella stessa cartella. |
| **`clustering_methods`** | *Lista* | Algoritmi da usare. Opzioni: `"kmeans"`, `"agglomerative"`, `"gmm"`, `"hdbscan"`, `"hdbscan_soft"`, `"spectral"`, `"evidence_accumulation"`, `"adp"`. È possibile metterne multipli per confrontarli, tranne `"adp"`, che gira da solo in un ambiente a parte (sezione "ADP" sotto). |
| **`params_file`** | *Stringa* | File configurazione interna algoritmi (di norma `"config/registry/params_clustering.json"`). |
| **`reduction_params_file`** | *Stringa \| null* | Il file `config/registry/params_reduction*.json` che ha prodotto `input_path` — `"config/registry/params_reduction.json"` per lesion, `"config/registry/params_reduction_sdc.json"` per sdc. **Obbligatorio quando `reduced_data: true`**, **vietato (deve mancare) quando `reduced_data: false`**. Serve a leggere `tag_param`/`tag_prefix` del `reduction_method` per ricostruire il tag dell'embedding (es. `"m_euclidean_nc2"`) direttamente dai parametri veri con cui `input_path` è stato costruito — mai scritto a mano in `session_name`, così non può disallinearsi dal vero `input_path` (vedi sotto). |
| **`output_root`** | *Stringa* | Cartella radice per i risultati (es. `"results/lesion/clustering"`). |
| **`session_name`** | *Stringa* | Identificativo di sessione (es. `"s1.1-vol"`). Da quando `reduction_params_file` esiste, **non serve più scriverci a mano l'embedding** (es. `"euclidean_n2"`) — viene derivato automaticamente da `input_path` e aggiunto al nome cartella finale. |
| **`overwrite`** | *Booleano* | Se `true`, sovrascrive esecuzioni precedenti con lo stesso nome. |
| **`fine_tuning`** | *Booleano* | `true` per tuning, `false` per produzione. |
| **`save_tuning_clusterings`** | *Booleano* | Solo in Fine-Tuning: se `true`, salva le etichette di cluster di *ogni* combinazione testata (non solo i punteggi in `tuning_results.csv`) in `clusterings.npz` + `metadata.csv`, per poterle rileggere senza ripetere lo sweep. `false` di default — obbligatorio dichiararlo comunque, anche in produzione. |
| **`run_notes`** | *Stringa* | Note libere sull'esecuzione. |

> **Nota su `params_clustering.json`**: Per la maggior parte dei metodi, bisogna specificare in questo file il numero di cluster voluti (es. `"n_clusters": 4`) prima di avviare l'esecuzione in produzione.

> **Nota su `"evidence_accumulation"`**: non va confuso con il blocco diagnostico `"consensus": {"rsc": {...}}` sopra (quello sweeppa la *stabilità* di un altro metodo, senza produrre cluster). `"evidence_accumulation"` come voce di `clustering_methods` è un metodo di produzione a sé (Fred & Jain 2002, replicato fedelmente), che ripete un metodo di base (`"base_method"`: `"kmeans"`/`"gmm"`/`"spectral"`) `n_repeats` volte e deriva le etichette finali dalla matrice di co-occorrenza — vedi `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md` §3. Con `base_method="spectral"` è esattamente l'RSC di Zanola et al. 2026. **Il numero di cluster finali non è un parametro** — emerge da solo tagliando a `"threshold"` (default 0.5, la soglia `t` del paper: due soggetti finiscono insieme solo se co-clusterizzati più del 50% delle volte). I suoi parametri in `params_clustering.json` sono `"base_method"` + `"n_repeats"` + `"threshold"` (obbligatori) + `"base_seed"` (opzionale, default 0) + tutti i parametri del `base_method` scelto, incluso il suo `n_clusters`/`n_components` — che qui è la granularità di *decomposizione iniziale* (va scelto più alto del numero di cluster atteso, non è il risultato finale) — niente `random_state` fisso, viene rifiutato esplicitamente.

> **Tuning di `"evidence_accumulation"` (nuovo)**: `tuning_grid` può sweeppare `"threshold"` insieme al parametro Split-phase del `base_method` scelto (es. `"n_clusters"` per `base_method="spectral"`/`"kmeans"`) — un grafico a linee (una per ogni valore Split-`k`, x=`threshold`), non una heatmap. In più, ogni run scrive automaticamente due diagnostici standalone indipendenti dallo sweep: `n_repeats_convergence.csv`/`.png` (la matrice di co-occorrenza si stabilizza al crescere di `n_repeats`, o il default è arbitrario?) e `consensus_matrix_heatmap.png` (matrice di co-occorrenza riordinata per cluster finale, stile Monti et al. 2003 — blocchi diagonali netti = cluster affidabili, sfumati = taglio ambiguo).

---

## Output e Grafici

A seconda della modalità, vengono generati risultati diversi. **Produzione e tuning vivono in due rami separati sotto `output_root`**, mai mescolati: `results/lesion/clustering/production/<metodo>/<reduction_method>/...` e `results/lesion/clustering/tuning/<metodo>/<reduction_method>/...` — il segmento `<reduction_method>` (da `reduction_method` in `clustering.json`) separa i risultati per embedding sorgente, es. `production/kmeans/umap/...` vs un ipotetico `production/kmeans/raw/...`.

**Nome della cartella finale**: `{dd-mm}_{session_name}_{tag_embedding}_{tag_clustering}` in produzione (es. `31-08_s1.1-vol_m_euclidean_nc2_n_clust5_linkaverage`), `{dd-mm}_{session_name}_{tag_embedding}` in tuning. `tag_embedding` (es. `m_euclidean_nc2`) è derivato automaticamente da `input_path` quando `reduced_data: true` — mai scritto a mano in `session_name` — leggendo `tag_param`/`tag_prefix` del `reduction_method` da `reduction_params_file` e i valori veri usati per `input_path` dal suo stesso `config.md`. `tag_clustering` (es. `n_clust5_linkaverage`) resta il tag già esistente, da `tag_param`/`tag_prefix` di `params_clustering.json`. Nessuno dei due tag è presente quando manca il rispettivo presupposto (`reduced_data: false` → niente `tag_embedding`; metodo senza `tag_param` → niente `tag_clustering`). Per `pca` `tag_embedding` è `nc<k>`, con `_<rotazione>` in coda solo se la PCA è ruotata (`nc42` non ruotata, `nc42_varimax` ruotata).

### Se in "Produzione" (`production/<metodo>/<reduction_method>/`, es. `production/kmeans/umap/` o `production/hdbscan/umap/`)
1. **`matrix.npy`**: Copia della matrice di partenza.
2. **`metadata.csv`**: File arricchito con la colonna **`cluster_label`**.
3. **`cluster_plot.png`**: Grafico 2D/3D statico colorato per cluster (titolo `"<Modality> - <ReductionMethod> - <ClusteringMethod>"`, es. `"Lesions - Umap - Kmeans"`). Nessuna versione `.html` per-run — la vista interattiva di un singolo run vive in `src.pipeline.embedding_app` (vedi `docs/guides/embedding_app.md`), che legge questo stesso `matrix.npy`/`metadata.csv` senza bisogno di un file HTML da rigenerare.
4. **`silhouette_plot.png`**: Grafico di qualità del clustering paziente per paziente.

Nessuna cartella `production/comparison/` — non esiste un plot di confronto cross-metodo generato dalla pipeline: per confrontare più metodi si aprono i `cluster_plot.png` di ciascuno, o si usa `embedding_app.py` (un run alla volta).

### Se in "Fine-Tuning" (`tuning/<metodo>/<reduction_method>/`)
1. **`tuning_results.csv`**: Risultati numerici dello sweep parametri.
2. **`tuning_plot.png`**: Sottografici per metrica calcolata.
3. Grafici diagnostici aggiuntivi (se supportati, es. dendrogramma).
4. **`clusterings.npz` & `metadata.csv`**: solo se `"save_tuning_clusterings": true` — un array di etichette per ogni combinazione testata (chiave `<param>=<valore>,...`), più la tabella soggetti corrispondente.
*(Non vengono salvati `matrix.npy` o grafici di assegnazione).*

### Diari di Bordo
Ogni metodo mantiene uno storico delle esecuzioni mai sovrascritto, in cima al proprio ramo (**non** per `<reduction_method>` — un solo file per metodo, copre tutti i `reduction_method`):
- `production/<metodo>/runs.csv` per Produzione — colonne `session, reduction_method, reduction_n_components, reduction_metric, <una per ogni chiave di tag_param del metodo>, timestamp, input_path, params, output, notes` (es. per agglomerative: `session, reduction_method, reduction_n_components, reduction_metric, n_clusters, linkage, timestamp, ...`).
- `tuning/<metodo>/runs_tuning.csv` per Fine-Tuning — colonne `session, reduction_method, reduction_n_components, reduction_metric, timestamp, input_path, params, output, notes` (nessuna colonna per singolo hyperparameter del metodo di clustering: un run di tuning sweeppa tutta la griglia, non sceglie un solo valore — ma `reduction_*` restano, descrivono l'embedding sorgente, non il metodo sweeppato).

`reduction_method`/`reduction_n_components`/`reduction_metric` descrivono l'embedding sorgente (`input_path`, quando `reduced_data: true`) — risolti automaticamente leggendo il `config.md` di quel run, mai dichiarati a mano nel config di clustering. Prefisso `reduction_` (non il semplice `n_components`/`metric` che usa `dim_reduction.py`) per non confliggere con l'omonimo hyperparameter proprio del metodo di clustering (es. `gmm` ha già un proprio `n_components`, il numero di componenti della mistura). `reduction_n_components`/`reduction_metric` sono stringa vuota (non assenti) quando `reduced_data: false` o quando il metodo sorgente non ha quel parametro (es. `pca` non ha `metric`). Nessuna colonna `id` (ridondante: nessun lettore la usava, e il tag/embedding sorgente sono già ricostruibili da `output_dir` e dalle colonne sopra). Lo stesso `reduction_method`/`reduction_n_components`/`reduction_metric` compare anche nel `config.md` di ogni singolo run.
