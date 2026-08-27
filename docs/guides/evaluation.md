# Guida al Notebook di Evaluation del Clustering

Confronto tra 2+ run di clustering già **prodotte** (`fine_tuning: false`) - il tuning (scelta di `k`/iperparametri) è già avvenuto altrove (`clustering.py --fine_tuning true` + `tuning_results.csv`/`tuning_plot.png`, letti a occhio). Questo notebook non rifà né sostituisce quella scelta: valuta *a posteriori* come sono andate le run già prodotte, solo tabelle/heatmap da leggere - nessuna selezione automatica qui né in tuning (`code_standards.md` §0).

- **Notebook**: `notebooks/post-results_analysis/clustering_evaluation.ipynb`
- **Codice riusabile dietro le nuove metriche**: `src/analysis/clustering_tuning.py::dunn_index`, `src/analysis/consensus_clustering.py::subsampling_stability_index` (con test in `tests/unit/`)

---

## Esecuzione

Locale soltanto, come ogni notebook sotto `notebooks/` - non è una pipeline CLI:

```bash
conda activate nemesis
jupyter lab notebooks/post-results_analysis/clustering_evaluation.ipynb
```

**Input**: per default il notebook punta a `results/lesion/clustering/production/<metodo>/<sessione>/` (lo stesso output di `clustering.py`, letto con `src.utils.artifacts.load_matrix` - il contratto usato anche da `embedding_app.py`). Al momento della stesura di questa guida non esiste ancora nessuna run di produzione clustering reale su disco - il notebook genera invece 4 run stand-in su un dataset **sintetico** (`make_blobs`, stesso stile dei prototipi `temp/*/run_prototype.py`), ma le scrive/rilegge attraverso il vero `save_matrix`/`load_matrix`, quindi la logica di confronto sotto è già valida per una vera run - basta cambiare `RUN_SPECS`/`run_dirs` con i path reali.

---

## Cosa mostra

### 1. Metriche intrinseche (sul singolo modello)

Una riga per run: Silhouette, Calinski-Harabasz, Davies-Bouldin (riusate da `clustering_tuning.compute_clustering_metrics`, stesso codice di produzione/tuning - non reimplementate), **Dunn Index** (nuovo, `clustering_tuning.dunn_index` - non esisteva nel repo, si legge come Silhouette: più alto è meglio, rapporto fra la più piccola distanza inter-cluster e il più grande diametro intra-cluster), più `inertia` (kmeans) o `bic`/`aic` (gmm) quando il metodo li espone.

Confrontabili solo **tra run dello stesso metodo/scala** (es. `kmeans k=4` vs `kmeans k=6`) - AIC/BIC di GMM non sono sulla stessa scala di Silhouette/Dunn/CH/DB, non vanno letti a confronto diretto con altri metodi. DBCV è stato esplicitamente scartato (memoria `project-clustering-tuning-redesign`, sezione hdbscan - nemmeno l'esempio ufficiale sklearn lo usa).

### 2. Metriche di confronto diretto (tra 2+ run)

- **ARI/NMI** (`sklearn.metrics.adjusted_rand_score`/`normalized_mutual_info_score`, nessun codice nuovo) tra ogni coppia di run - heatmap simmetrica.
- **Match matrix** (`sklearn.metrics.cluster.contingency_matrix`, solo visualizzazione) per una coppia scelta - dove due run si accordano/disaccordano cella per cella.
- **Subsampling Stability Index** (nuovo, `consensus_clustering.subsampling_stability_index`): ARI tra un fit sul 100% dei soggetti e lo stesso metodo/parametri rifittato su un campione all'80% (senza reinserimento) - un valore vicino a 1 significa che il clustering non dipende da un piccolo sottoinsieme di soggetti (es. outlier). **Diverso da `run_monti_repeats`** (già esistente, usato dal blocco `"consensus"` di `clustering.py`): quello costruisce una matrice di co-occorrenza su N ripetizioni, pensato solo per i metodi con vera stocasticità interna (`CONSENSUS_ELIGIBLE_METHODS = {kmeans, gmm, spectral}`); il Subsampling Stability Index è un singolo confronto 100%-vs-80%, valido per **qualunque** metodo registrato in `CLUSTERING_METHODS`, incluso uno deterministico come `agglomerative` (la domanda "il risultato cambia con un campione più piccolo?" ha senso anche lì).

---

## Lettura consigliata

- Le metriche intrinseche dicono se *quella* run è internamente compatta/separata - non dicono se è "giusta" rispetto a un'altra run.
- ARI/NMI e la match matrix dicono quanto due run (stesso metodo o metodi diversi) si assomigliano - un ARI alto tra `kmeans k=4` e `agglomerative k=4` è un segnale di convergenza tra criteri diversi, non una prova che `k=4` sia corretto.
- Il Subsampling Stability Index risponde a una domanda diversa dalle prime due: quella singola run è un artefatto del campione esatto di soggetti?
- Nessuna cella del notebook rifà la scelta di `k`/metodo - quella è già stata fatta in tuning, prima che queste run venissero prodotte; qui si valuta a posteriori come sono andate (`code_standards.md` §0: nessuna selezione automatica, né in tuning né qui).

Metodologia/letteratura di riferimento (tabelle originali, proposte non ancora implementate): `knowledge/dim_reduction_clustering/clustering_literature_survey.md`, memoria persistente `project-clustering-tuning-evaluation-tables`.
