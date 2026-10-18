# Analizzare un tuning di clustering già salvato (`analyze_clustering_tuning`)

Calcola su un tuning di `clustering.py` già concluso ciò che lo sweep non scrive, senza rifare il clustering: legge `tuning_results.csv`, `clusterings.npz` e `config.md` della cartella della run e scrive i risultati accanto a quei file. Lesione e SDC allo stesso modo. ADP non è gestito (ha le sue diagnostiche: [`clustering.md`](clustering.md)).

- **Script**: `src/pipeline/analyze_clustering_tuning.py`
- **Configurazione**: `config/pipelines/analyze_clustering_tuning.json`

---

## Esecuzione

### 1. In locale
```bash
conda activate nemesis
python -m src.pipeline.analyze_clustering_tuning --config config/pipelines/analyze_clustering_tuning.json
```

### 2. Sul server (tramite SLURM)
```bash
sbatch jobs/run_analyze_clustering_tuning.sh
```

---

## Cosa serve

Una cartella di tuning scritta da `clustering.py` con `fine_tuning: true` e `save_tuning_clusterings: true` (senza `clusterings.npz` lo script si ferma). Le chiavi di `clusterings.npz` devono corrispondere esattamente alle righe di `tuning_results.csv`: una cartella riusata da una run con un'altra griglia non viene analizzata. Per agglomerative serve anche la matrice a cui punta `input_path` in `config.md`.

## Parametri JSON

| Parametro | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`tuning_dir`** | *Stringa* | La cartella della run, es. `results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_m_dice_nc2`. Il metodo si legge dal suo `config.md`. |
| **`overwrite`** | *Booleano* | Se `false`, lo script si ferma se uno dei suoi file esiste già; se `true`, li sostituisce. |
| **`k_range`** | *Oggetto* | `min` e `max` (interi, `min` ≥ 2): i k per cui si calcola il salto del dendrogramma (agglomerative). |
| **`curves_max_noise_fraction`** | *Numero in (0, 1]* | Le curve di HDBSCAN tengono solo le combinazioni con `noise_fraction` fino a questo valore. |
| **`usable`** | *Oggetto* | I criteri del flag `usable` (HDBSCAN): `min_clusters`, `max_clusters`, `max_noise_fraction`, `max_largest_cluster_share`. Non hanno un default. |

## Output

Nella cartella della run (rilanciare la pipeline del tuning con `overwrite: true` la ricrea da zero e questi file spariscono: si rilancia anche questa).

| Metodo | File | Contenuto |
| :--- | :--- | :--- |
| agglomerative | `cophenetic_correlation.csv` | Una riga per (`metric`, `linkage`) valido: correlazione tra le distanze vere e quelle dell'albero (da 0 a 1, vicino a 1 l'albero è fedele). Non si confronta tra `metric` diverse. |
| agglomerative | `dendrogram_jump.csv` | Una riga per (`metric`, `linkage`, `n_clusters`): altezza della fusione da k a k−1 divisa per quella da k+1 a k. Vicino a 1 non c'è un taglio naturale a k; più è alto, più il taglio è netto. |
| agglomerative | `k_curves_metric=<metric>.png` | Silhouette e Davies-Bouldin per `n_clusters`, una linea per linkage (single escluso). |
| hdbscan, hdbscan_soft | `candidates.csv` | `tuning_results.csv` più `n_clusters_found` (contato dalle etichette), `largest_cluster_share` (sul totale dei soggetti, rumore compreso) e `usable`: tra `min_clusters` e `max_clusters` cluster, rumore e cluster più grande entro i limiti. È un filtro pratico, non un indice. |
| hdbscan, hdbscan_soft | `noise_filtered_curves[_<cluster_selection_method>].png` | Silhouette e Davies-Bouldin contro `min_cluster_size`, una linea per `min_samples`, solo le combinazioni con poco rumore. Se per un `cluster_selection_method` nessuna combinazione è sotto il limite (`leaf` non scende sotto il 15%), manca quel file e il log lo dice. |

Ogni lancio scrive un log in `logs/analyze_clustering_tuning/`.
