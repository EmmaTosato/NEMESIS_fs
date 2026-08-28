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

## Dettaglio Parametri JSON (`clustering.json`)

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`project`** | *Stringa* | Nome del progetto (es. `"clinical_connectome"`). |
| **`input_path`** | *Stringa* | Percorso della matrice di input. Dati grezzi (`data/derived/...`) o compressi (`results/lesion/dim_reduction/...`). DEVE esistere. |
| **`clustering_methods`** | *Lista* | Algoritmi da usare. Opzioni: `"kmeans"`, `"agglomerative"`, `"gmm"`, `"hdbscan"`, `"spectral"`, `"evidence_accumulation"`. È possibile metterne multipli per confrontarli. |
| **`params_file`** | *Stringa* | File configurazione interna algoritmi (di norma `"config/registry/params_clustering.json"`). |
| **`output_root`** | *Stringa* | Cartella radice per i risultati (es. `"results/lesion/clustering"`). |
| **`session_name`** | *Stringa* | Nome esecuzione (es. `"test_gruppi_1"`). |
| **`overwrite`** | *Booleano* | Se `true`, sovrascrive esecuzioni precedenti con lo stesso nome. |
| **`fine_tuning`** | *Booleano* | `true` per tuning, `false` per produzione. |
| **`save_tuning_clusterings`** | *Booleano* | Solo in Fine-Tuning: se `true`, salva le etichette di cluster di *ogni* combinazione testata (non solo i punteggi in `tuning_results.csv`) in `clusterings.npz` + `metadata.csv`, per poterle rileggere senza ripetere lo sweep. `false` di default — obbligatorio dichiararlo comunque, anche in produzione. |
| **`run_notes`** | *Stringa* | Note libere sull'esecuzione. |

> **Nota su `params_clustering.json`**: Per la maggior parte dei metodi, bisogna specificare in questo file il numero di cluster voluti (es. `"n_clusters": 4`) prima di avviare l'esecuzione in produzione.

> **Nota su `"evidence_accumulation"`**: non va confuso con il blocco diagnostico `"consensus": {"rsc": {...}}` sopra (quello sweeppa la *stabilità* di un altro metodo, senza produrre cluster). `"evidence_accumulation"` come voce di `clustering_methods` è un metodo di produzione a sé (Fred & Jain 2002, replicato fedelmente), che ripete un metodo di base (`"base_method"`: `"kmeans"`/`"gmm"`/`"spectral"`) `n_repeats` volte e deriva le etichette finali dalla matrice di co-occorrenza — vedi `knowledge/dim_reduction_clustering/clustering_literature_survey.md` §3. Con `base_method="spectral"` è esattamente l'RSC di Zanola et al. 2026. **Il numero di cluster finali non è un parametro** — emerge da solo tagliando a `"threshold"` (default 0.5, la soglia `t` del paper: due soggetti finiscono insieme solo se co-clusterizzati più del 50% delle volte). I suoi parametri in `params_clustering.json` sono `"base_method"` + `"n_repeats"` + `"threshold"` (obbligatori) + `"base_seed"` (opzionale, default 0) + tutti i parametri del `base_method` scelto, incluso il suo `n_clusters`/`n_components` — che qui è la granularità di *decomposizione iniziale* (va scelto più alto del numero di cluster atteso, non è il risultato finale) — niente `random_state` fisso, viene rifiutato esplicitamente.

> **Tuning di `"evidence_accumulation"` (nuovo)**: `tuning_grid` può sweeppare `"threshold"` insieme al parametro Split-phase del `base_method` scelto (es. `"n_clusters"` per `base_method="spectral"`/`"kmeans"`) — un grafico a linee (una per ogni valore Split-`k`, x=`threshold`), non una heatmap. In più, ogni run scrive automaticamente due diagnostici standalone indipendenti dallo sweep: `n_repeats_convergence.csv`/`.png` (la matrice di co-occorrenza si stabilizza al crescere di `n_repeats`, o il default è arbitrario?) e `consensus_matrix_heatmap.png` (matrice di co-occorrenza riordinata per cluster finale, stile Monti et al. 2003 — blocchi diagonali netti = cluster affidabili, sfumati = taglio ambiguo).

---

## Output e Grafici

A seconda della modalità, vengono generati risultati diversi. **Dal 2026-08, produzione e tuning vivono in due rami separati sotto `output_root`**, mai mescolati: `results/lesion/clustering/production/<metodo>/...` e `results/lesion/clustering/tuning/<metodo>/...`.

### Se in "Produzione" (`production/<metodo>/`, es. `production/kmeans/` o `production/hdbscan/`)
1. **`matrix.npy`**: Copia della matrice di partenza.
2. **`metadata.csv`**: File arricchito con la colonna **`cluster_label`**.
3. **`cluster_plot.png` & `.html`**: Grafico 2D (prime 2 colonne) colorato per cluster. La versione HTML è interattiva.
4. **`silhouette_plot.png`**: Grafico di qualità del clustering paziente per paziente.
5. **Cartella `production/comparison/`**: (Solo se si usano più metodi) Affianca i risultati visivi degli algoritmi scelti (es. `cluster_plot_comparison.png`), utilissimo per decidere quale metodo "taglia" meglio i dati.

### Se in "Fine-Tuning" (`tuning/<metodo>/`)
1. **`tuning_results.csv`**: Risultati numerici dello sweep parametri.
2. **`tuning_plot.png`**: Sottografici per metrica calcolata.
3. Grafici diagnostici aggiuntivi (se supportati, es. dendrogramma).
4. **`clusterings.npz` & `metadata.csv`**: solo se `"save_tuning_clusterings": true` — un array di etichette per ogni combinazione testata (chiave `<param>=<valore>,...`), più la tabella soggetti corrispondente.
*(Non vengono salvati `matrix.npy` o grafici di assegnazione).*

### Diari di Bordo
Ogni metodo mantiene uno storico delle esecuzioni mai sovrascritto, in cima al proprio ramo:
- `production/<metodo>/runs.csv` per Produzione.
- `tuning/<metodo>/runs_tuning.csv` per Fine-Tuning.
