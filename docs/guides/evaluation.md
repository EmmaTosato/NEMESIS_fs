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
| 3 | Metriche del modello: `inertia`, `bic`/`aic`, `noise_fraction`/`n_clusters_found` | kmeans, gmm, hdbscan, hdbscan_soft | `clustering_evaluation.model_fit_metrics` |
| 3.1 | Posizione nel cluster: probabilità media e quota sotto soglia per cluster | hdbscan | `clustering_evaluation.membership_confidence` |
| 3.2 | Appartenenza ai cluster: per cluster, probabilità media nel proprio e cluster più vicino; vettori medi; soggetti più deboli | hdbscan_soft | `clustering_evaluation.soft_membership_summary` |
| 4 | Descrizione dei cluster con le variabili di `participants.csv`: soggetti con il dato, media ± deviazione standard, mediana [Q1–Q3], percentuali per categoria; nessun test | tutti | funzioni del notebook (`registry_frame`, `coverage_table`, `describe_clusters`) |

Cose che non si vedono dal registro:

- **Metriche geometriche**: assumono distanza euclidea e cluster compatti e convessi, quindi favoriscono kmeans/gmm. `compute_clustering_metrics(combo_params=...)` rifiuta una run con `metric`/`affinity` non euclideo. Valori di embedding diversi (lesion vs sdc) non sono confrontabili.
- **Metriche del modello**: kmeans e gmm vengono rifittati con i parametri della run e accettati solo se riproducono esattamente le etichette salvate (altrimenti `ValueError`, tipico di `random_state` non fissato). `inertia` e BIC/AIC non sono sulla stessa scala.
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

---

## `clustering_comparison.ipynb` — due o più run

Contiene le analisi che mettono a confronto più run:

- ARI/NMI a coppie (heatmap) e match matrix (contingency) tra due run sugli stessi soggetti;
- distanza centroide-centroide tra run che condividono lo stesso embedding (`require_shared_embedding` solleva altrimenti);
- confronto cross-modalità lesion vs sdc sull'intersezione dei `subject_id` (`aligned_labels_intersection` stampa N per lato, intersezione ed esclusi, mai un merge silenzioso): contingency grezza e normalizzata, ARI/NMI/homogeneity/completeness, chi-quadro con residui standardizzati, purezza per cluster, profilo clinico per cluster.

- Parte 4, **due cluster della stessa run** (la sezione "Dentro lo stesso clustering" dell'app Dash, stesse funzioni di `src/analysis/cluster_pair.py`): profilo demografico e clinico (Mann-Whitney e Fisher, p corretto Benjamini-Hochberg), regressione logistica del cluster 1 contro il cluster 2 con grafico degli odds ratio, distanza tra i centroidi nell'embedding rapportata al raggio dei cluster, mappe di overlap della lesione dei due cluster e loro differenza. Si sceglie la run (`PAIR_RUN`) e i due cluster (`LABEL_1`, `LABEL_2`); il primo è il riferimento per il segno di `r`, degli odds ratio e della differenza. Le mappe leggono le maschere di tutti i soggetti dei due cluster (circa 1 minuto su ~900 soggetti) e richiedono i `.nii.gz` in `data/`. La disconnessione per le run sdc non è nel notebook, solo nell'app.

Le Parti 1-3 sono ancora quelle della versione unica del notebook, in attesa di riorganizzazione.

---

## Lettura consigliata

- Le metriche intrinseche dicono se *quella* run è compatta e separata, non se è "giusta" rispetto a un'altra.
- ARI/NMI alti tra metodi diversi sono un segnale di convergenza, non una prova che `k` sia corretto. ARI/NMI bassi tra lesion e sdc non sono un errore: feature space diversi non hanno obbligo di produrre la stessa partizione.

Metodologia e letteratura: `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md`.
