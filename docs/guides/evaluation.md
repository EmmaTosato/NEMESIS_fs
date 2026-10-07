# Guida ai notebook di valutazione del clustering

Due notebook sotto `notebooks/post-results_analysis/` (evaluation e comparison) lavorano su run di clustering già **prodotte** (`fine_tuning: false`, lette da `results/<lesion|sdc>/clustering/production/<metodo>/<embedding>/<run_name>/`). La scelta di `k`/iperparametri è fatta altrove (`clustering.py --fine_tuning true`, `tuning_results.csv`/`tuning_plot.png`): qui non si sceglie niente in automatico (`code_standards.md` §0), si leggono tabelle e grafici.

| Notebook | Domanda | Unità di analisi |
|---|---|---|
| `clustering_evaluation.ipynb` | com'è fatta questa run? | una run alla volta |
| `clustering_comparison.ipynb` | in cosa differiscono queste run? | due o più run |

## Scope: dove vive ogni analisi

Il criterio (empirica contro interpretativa) è in [`exploration.md`](exploration.md). Evaluation e comparison sono **empirici**; l'interpretazione dei cluster è in `cluster_interpretation.ipynb`, che non è documentato qui.

| Analisi | Notebook |
|---|---|
| Metriche geometriche, del modello, stabilità di una run | `clustering_evaluation` |
| Accordo tra partizioni (ARI/NMI/VI), contingency, abbinamento e Jaccard tra cluster di run diverse | `clustering_comparison` |
| Distanze tra cluster **nello spazio dell'embedding** (centroidi, Mahalanobis, linkage) | `clustering_comparison` |
| Tabelle e test su età, sesso, NIHSS, volume, dataset, lato, localizzazione | `cluster_interpretation` |
| Mappe di overlap e disconnessione, soggetti rappresentativi | `cluster_interpretation` |
| Distanze tra cluster **nello spazio delle mappe o del profilo clinico** | `cluster_interpretation` |
| Perché due cluster abbinati differiscono (A∩B, A\B, B\A descritti con le variabili esterne) | `cluster_interpretation`, che riceve l'abbinamento dal comparison |

I casi di confine seguono il criterio: una distanza calcolata sulle coordinate dell'embedding è empirica; una calcolata su mappe anatomiche o variabili cliniche descrive i cluster ed è interpretativa. Un'analisi che serve a entrambi i notebook (l'abbinamento dei cluster) vive come funzione in `src/analysis/`, perché i notebook non si importano tra loro.

**Stato attuale.** `clustering_evaluation` contiene ancora la sezione 5 (associazione con le variabili cliniche) e le sezioni 6.2 e 6.3 (centroidi, soggetti rappresentativi): per il criterio sopra ricadono in `cluster_interpretation`, che le ha già. `clustering_comparison` ha ancora le sezioni della versione unica, con la vecchia numerazione e il profilo clinico per cluster della Parte 2 §3.

Sono notebook locali, non pipeline CLI:

```bash
conda activate nemesis
jupyter lab notebooks/post-results_analysis/clustering_evaluation.ipynb
```

Nessun dataset sintetico: le run si scelgono a mano in `SELECTED_RUNS` (path della colonna `output` di `list_production_runs`).

---

## `clustering_evaluation.ipynb` — una run alla volta

Ogni sezione è un **metodo di valutazione** (una metrica, un gruppo di metriche lette insieme, o un grafico) e riporta quattro cose: che metodo è, cosa fa, come si legge, a quali metodi di clustering si applica.

L'applicabilità è verificata dal codice: `src/analysis/clustering_evaluation.py` tiene il registro `EVALUATIONS` (valutazione → metodi) e `require_applicable`, che solleva `ValueError` per un metodo non previsto. Nel notebook `applicable_runs(valutazione)` salta le run non applicabili stampando il motivo e solleva se non ne resta nessuna; le sezioni a run singola chiamano `require_applicable` sulla run scelta. Un test (`tests/unit/test_clustering_evaluation.py`) garantisce che il registro nomini solo metodi di `CLUSTERING_METHODS`.

| Sezione | Metodo di valutazione | Metodi di clustering | Codice |
|---|---|---|---|
| 2 | Metriche geometriche: Silhouette, Calinski-Harabasz, Davies-Bouldin, Dunn | tutti | `clustering_tuning.compute_clustering_metrics`, `dunn_index` |
| 3 | Metriche del modello: `inertia`, `bic`/`aic`, `noise_fraction`/`n_clusters_found` | kmeans, gmm, hdbscan | `clustering_evaluation.model_fit_metrics` |
| 4 | Stabilità al sottocampionamento (ARI tra fit al 100% e all'80%) | tutti | `consensus_clustering.subsampling_stability_index` |
| 5 | Associazione con variabili cliniche: tabella per cluster, Kruskal-Wallis (età, NIHSS), chi-quadro (sesso) | tutti | `scipy.stats` su `assets/metadata/participants.csv` |
| 6 | Grafici: plot prodotti, embedding con centroidi, soggetti rappresentativi sul cervello | tutti | `plotting`, `anatomical_maps.resolve_lesion_paths` |

Cose che non si vedono dal registro:

- **Metriche geometriche**: assumono distanza euclidea e cluster compatti e convessi, quindi favoriscono kmeans/gmm. `compute_clustering_metrics(combo_params=...)` rifiuta una run con `metric`/`affinity` non euclideo. Valori di embedding diversi (lesion vs sdc) non sono confrontabili.
- **Metriche del modello**: kmeans e gmm vengono rifittati con i parametri della run e accettati solo se riproducono esattamente le etichette salvate (altrimenti `ValueError`, tipico di `random_state` non fissato). `inertia` e BIC/AIC non sono sulla stessa scala.
- **Stabilità**: per hdbscan il rumore (`-1`) conta come un gruppo nell'ARI; è un singolo confronto con seed fisso, non un ensemble (a differenza di `run_monti_repeats`, che vale solo per `CONSENSUS_ELIGIBLE_METHODS`).
- **Rumore di hdbscan**: escluso da tabella e test clinici, dai centroidi e dagli indici geometrici; la sua quota è sempre mostrata (`noise_fraction`, conteggio stampato).
- **DBCV** è escluso (già scartato nel tuning, `docs/guides/clustering.md`).

Lesion e sdc possono convivere nella stessa `SELECTED_RUNS`: ogni run è valutata da sola. I soggetti rappresentativi richiedono i `.nii.gz` dei soggetti in `data/`.

---

## `clustering_comparison.ipynb` — due o più run

Contiene le analisi che mettono a confronto più run:

- ARI/NMI a coppie (heatmap) e match matrix (contingency) tra due run sugli stessi soggetti;
- distanza centroide-centroide tra run che condividono lo stesso embedding (`require_shared_embedding` solleva altrimenti);
- confronto cross-modalità lesion vs sdc sull'intersezione dei `subject_id` (`aligned_labels_intersection` stampa N per lato, intersezione ed esclusi, mai un merge silenzioso): contingency grezza e normalizzata, ARI/NMI/homogeneity/completeness, chi-quadro con residui standardizzati, purezza per cluster, profilo clinico per cluster.

Le sezioni sono ancora quelle della versione unica del notebook, in attesa di riorganizzazione.

---

## Lettura consigliata

- Le metriche intrinseche dicono se *quella* run è compatta e separata, non se è "giusta" rispetto a un'altra.
- La stabilità risponde a una domanda diversa: la run è un artefatto del campione esatto di soggetti?
- ARI/NMI alti tra metodi diversi sono un segnale di convergenza, non una prova che `k` sia corretto. ARI/NMI bassi tra lesion e sdc non sono un errore: feature space diversi non hanno obbligo di produrre la stessa partizione.

Metodologia e letteratura: `knowledge/dim_reduction_clustering/clustering_literature_survey.md`.
