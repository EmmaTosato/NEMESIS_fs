# Guida alla Riduzione + Clustering (`dim_reduction_clustering`)

Questa guida riguarda lo script più utilizzato nell'intero progetto NEMESIS: `dim_reduction_clustering.py`. 

- **Script**: `src/pipeline/dim_reduction_clustering.py`
- **Configurazione**: `config/pipelines/dim_reduction_clustering.json`

---

## 🚀 Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione.
```bash
sbatch jobs/run_dim_reduction_clustering.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`:
```bash
python -m src.pipeline.dim_reduction_clustering --config config/pipelines/dim_reduction_clustering.json
```

---

## 🧠 La "Scorciatoia" d'Eccellenza

Invece di eseguire faticosamente e manualmente prima lo script di Riduzione e, in seguito, quello di Clustering, questo script compie **entrambi i passaggi consecutivamente**.
Prende i dati grezzi, comprime lo spazio geometrico usando **UN** singolo algoritmo, e in cascata vi applica **MOLTEPLICI** algoritmi di clustering, generando anche file di comparazione automatica.

---

## ⚙️ Dettaglio Parametri JSON

I parametri uniscono quelli di `dim_reduction` e `clustering`:

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`project`** | *Stringa* | Nome progetto (es. `"clinical_connectome"`). |
| **`input_path`** | *Stringa* | Cartella di origine *Matrix Building* (es. `"data/derived/lesion_matrix/21-07_s1.1"`). **NON** dati già compressi. |
| **`reduction_method`** | *Stringa* | **Unico** algoritmo per comprimere (es. `"umap"`). |
| **`clustering_methods`** | *Lista* | Gli algoritmi di clustering da applicare in sequenza (es. `["kmeans", "gmm"]`). |
| **`reduction_params_file`**| *Stringa* | File registro matematica riduzione. |
| **`clustering_params_file`**| *Stringa* | File registro matematica clustering. |
| **`output_root`** | *Stringa* | Sede dei risultati (es. `"results/lesion/dim_reduction_clustering"`). Ha il suo ramo separato. |
| **`session_name`** | *Stringa* | Etichetta dell'operazione massiva. |
| **`overwrite`** | *Booleano* | Se `true` sovrascrive directory identiche. |
| **`fine_tuning`** | *Booleano* | Se `false` (default) effettua Produzione Finale. Se `true` compie tuning del clustering. **(Vedi Note)** |
| **`regress_out_volume`** | *Booleano* | Rimuove linearmente l'effetto volume prima del clustering. Incompatibile con metriche `jaccard/dice`. |
| **`viz_n_components`** | *Intero (solo 2)*| Forza a 2 componenti l'output *esclusivamente per la grafica visiva*. **A differenza del solo Dim Reduction, qui `3` non è ammesso**. |
| **`color_by`** | *Lista* | (*Opzionale*). Se popolata, genera parallelamente grafici di embedding aggiuntivi esplorativi (`dataset`, `side`, `volume`, `nihss`). |
| **`run_notes`** | *Stringa* | Spazio note libere. |

---

## 🔎 Note Fondamentali sul Funzionamento Interno

- **La Riduzione NON si tara mai in questo script**: la `dim_reduction` avviene qui sempre "in produzione", prendendo i valori finali fissati su `reduction_params_file`. Per tarare UMAP o PCA, devi usare prima lo script isolato.
- Il flag **`fine_tuning: true` qui serve solo a tarare gli algoritmi di clustering** sullo spazio appena compresso.
- **`metadata.csv` viene arricchito in automatico** come nella Dim Reduction classica, ereditando le colonne cliniche indipendentemente da `color_by`.

---

## 📂 Organizzazione e Output Generato

L'output viene salvato nella root dedicata e organizzato ad albero (Riduzione ➔ Clustering):
```text
results/lesion/dim_reduction_clustering/
└── umap/
    ├── kmeans/
    │   └── <Data>_<session_name>_<umap_tag>_<kmeans_tag>/
    ├── gmm/
    │   └── <Data>_<session_name>_<umap_tag>_<gmm_tag>/
    ├── runs.csv  <-- Diario di produzione a livello di Riduzione
    └── comparison/
        └── umap_<Data>_<session_name>_<umap_tag>/
```

### Contenuto Cartella Specifica (es. `umap/kmeans/`)
- `matrix.npy`: La matrice di dati compressi.
- `metadata.csv`: L'anagrafica completa arricchita della colonna fondamentale `cluster_label`.
- `config.md`: Riepilogo minuzioso del run.
- `cluster_plot.png` e `.html`: Grafici base in 2D in cui i colori sono assegnati in base al cluster di appartenenza.
- `silhouette_plot.png`: Verifica della qualità del raggruppamento per singolo paziente. 

### Super-Cartella di Confronto (`comparison/`)
Generata in automatico quando elenchi più algoritmi di raggruppamento. Include `cluster_comparison.png` e `cluster_comparison_interactive.html` che permettono di visionare la medesima struttura geometrica del cervello (es. UMAP), ma mostrandola fianco a fianco colorata con i diversi algoritmi (es. come la raggruppa KMeans contro come la raggruppa GMM).
