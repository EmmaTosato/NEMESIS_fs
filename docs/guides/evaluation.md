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

**Input**: run di produzione **reali**, già eseguite da `clustering.py` e lette da
`results/<lesion|sdc>/clustering/production/<metodo>/<embedding>/<run_name>/` (stesso
contratto `src.utils.artifacts.load_matrix`/`save_matrix` usato da `embedding_app.py`).
Nessun dataset sintetico. Le funzioni riusabili del notebook (caricamento, allineamento,
demografiche, confronto cross-modalità) sono definite una volta in `## Utils`, in cima al
notebook; le sezioni numerate sotto le applicano, non le ridefiniscono.

Il notebook è diviso in due parti:

- **Parte 1 - Confronto entro la stessa pipeline**: metodi/`k` diversi sugli stessi dati
  (stessa pipeline - lesion o sdc, a seconda della sezione).
- **Parte 2 - Confronto cross-modalità**: la stessa domanda ma tra pipeline diverse
  (lesion vs sdc), dove i soggetti non coincidono per costruzione.

---

## Cosa mostra

### Parte 1 — Confronto entro la stessa pipeline

#### §3 - Metriche intrinseche (sul singolo modello)

Una riga per run: Silhouette, Calinski-Harabasz, Davies-Bouldin (riusate da `clustering_tuning.compute_clustering_metrics`, stesso codice di produzione/tuning - non reimplementate), **Dunn Index** (nuovo, `clustering_tuning.dunn_index` - non esisteva nel repo, si legge come Silhouette: più alto è meglio, rapporto fra la più piccola distanza inter-cluster e il più grande diametro intra-cluster), più `inertia` (kmeans) o `bic`/`aic` (gmm) quando il metodo li espone.

Confrontabili solo **tra run dello stesso metodo/scala** (es. `kmeans k=4` vs `kmeans k=6`) - AIC/BIC di GMM non sono sulla stessa scala di Silhouette/Dunn/CH/DB, non vanno letti a confronto diretto con altri metodi. DBCV è stato esplicitamente scartato (memoria `project-clustering-tuning-redesign`, sezione hdbscan - nemmeno l'esempio ufficiale sklearn lo usa).

#### §4-§6 - Metriche di confronto diretto (tra 2+ run)

- **§4 ARI/NMI** (`sklearn.metrics.adjusted_rand_score`/`normalized_mutual_info_score`, nessun codice nuovo) tra ogni coppia di run - heatmap simmetrica.
- **§5 Match matrix** (`sklearn.metrics.cluster.contingency_matrix`, solo visualizzazione) per una coppia scelta - dove due run si accordano/disaccordano cella per cella.
- **§6 Subsampling Stability Index** (nuovo, `consensus_clustering.subsampling_stability_index`): ARI tra un fit sul 100% dei soggetti e lo stesso metodo/parametri rifittato su un campione all'80% (senza reinserimento) - un valore vicino a 1 significa che il clustering non dipende da un piccolo sottoinsieme di soggetti (es. outlier). **Diverso da `run_monti_repeats`** (già esistente, usato dal blocco `"consensus"` di `clustering.py`): quello costruisce una matrice di co-occorrenza su N ripetizioni, pensato solo per i metodi con vera stocasticità interna (`CONSENSUS_ELIGIBLE_METHODS = {kmeans, gmm, spectral}`); il Subsampling Stability Index è un singolo confronto 100%-vs-80%, valido per **qualunque** metodo registrato in `CLUSTERING_METHODS`, incluso uno deterministico come `agglomerative` (la domanda "il risultato cambia con un campione più piccolo?" ha senso anche lì).

#### §8 - Centroidi within-modality

Solo quando due run condividono `session_name`/`reduction_method`/`reduction_n_components`/`reduction_metric` (`require_shared_embedding`, solleva altrimenti) il confronto diretto di centroidi/distanze nello spazio embedding condiviso ha senso - qui: due metodi di clustering diversi (kmeans vs agglomerative) sulla stessa run UMAP 2D sdc. Le due run vengono dalla stessa pipeline, solo il metodo cambia - non è un confronto cross-modalità come in Parte 2.

### Parte 2 — Confronto cross-modalità (lesion vs sdc)

Tutta la Parte 1 confronta metodi/`k` diversi **sulla stessa pipeline**, sullo stesso set di soggetti in ordine identico. La Parte 2 confronta invece **run di pipeline diverse** (lesion vs sdc), dove i soggetti non coincidono per costruzione - ogni metrica qui è a coppie, nessun confronto N-way simultaneo, nessun diagramma Sankey/alluvial (deliberatamente fuori scope).

- **§1 - Confronto cross-modalità**: `aligned_labels_intersection` allinea due run per inner join su `subject_id` (stampa esplicitamente N soggetti per lato, N nell'intersezione, N esclusi - mai un merge silenzioso, `code_standards.md` §0), poi sull'intersezione: contingency table grezza + row-normalized + column-normalized, ARI/NMI, homogeneity/completeness (`sklearn.metrics`, separano la direzione dell'asimmetria che NMI media), residui standardizzati di Pearson (`scipy.stats.chi2_contingency`, marcano quali celle si scostano più del previsto sotto indipendenza).
- **§2 - Purezza per cluster**: per ogni cluster sorgente, % nel cluster di destinazione dominante, una riga per cluster, dal meno puro al più puro - lettura rapida derivata dalla row-normalized table di §1.
- **§3 - Profilo clinico/demografico cross-cluster**: generalizza il blocco demografico di Parte 1 §7 a entrambe le run della coppia, ristretto ai soggetti dell'intersezione - il sostituto valido di un confronto centroidi quando le due run vivono in feature space non comparabili (voxel lesione vs regioni SDC).
- **§4 - Fenotipo funzionale FC**: bloccato oggi (nessuna run di produzione clustering FC, ReHo/ALFF/global-connectivity non implementati in `src/features/functional.py`) - solo uno scaffolding con `NotImplementedError` esplicito.

---

## Lettura consigliata

- Le metriche intrinseche dicono se *quella* run è internamente compatta/separata - non dicono se è "giusta" rispetto a un'altra run.
- ARI/NMI e la match matrix dicono quanto due run (stesso metodo o metodi diversi) si assomigliano - un ARI alto tra `kmeans k=4` e `agglomerative k=4` è un segnale di convergenza tra criteri diversi, non una prova che `k=4` sia corretto.
- Il Subsampling Stability Index risponde a una domanda diversa dalle prime due: quella singola run è un artefatto del campione esatto di soggetti?
- Nessuna cella del notebook rifà la scelta di `k`/metodo - quella è già stata fatta in tuning, prima che queste run venissero prodotte; qui si valuta a posteriori come sono andate (`code_standards.md` §0: nessuna selezione automatica, né in tuning né qui).
- Il confronto cross-modalità (Parte 2) risponde a una domanda diversa dalla Parte 1: non "quale `k`/metodo è migliore", ma "quanto le due pipeline (lesion, sdc) raccontano la stessa struttura sui soggetti che condividono". Un ARI/NMI basso tra le due non è un errore da correggere - due feature space diversi (voxel lesione vs regioni SDC) non hanno alcun obbligo di produrre la stessa partizione.

Metodologia/letteratura di riferimento (tabelle originali, proposte non ancora implementate): `knowledge/dim_reduction_clustering/clustering_literature_survey.md`, memoria persistente `project-clustering-tuning-evaluation-tables`.
