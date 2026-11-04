# Clustering agglomerativo in NEMESIS

- **Teoria:** [Clustering agglomerativo (gerarchico)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/agglomerative.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Clustering/agglomerative.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/agglomerative.md) (derivata, non è una fonte)

Metodo `agglomerative` di `CLUSTERING_METHODS` (`src/analysis/clustering.py`), implementato con `sklearn.cluster.AgglomerativeClustering`
(scikit-learn 1.8.0, ambiente `nemesis`). Parametri: `config/registry/params_clustering.json`, voce `agglomerative`.
Altri metodi: [README](README.md). Metriche condivise: [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).

## Su cosa lo applichiamo
- **Input:** embedding UMAP con `n_components` 2, 3 o 10 (metrica UMAP `euclidean` o `dice`), score PCA (anche varimax),
  la matrice SDC "stream" a 87 colonne (`docs/guides/evaluation.md`), oppure la matrice lesionale grezza. Circa 1100-5850 soggetti a seconda della matrice.
- **Metrica:** `euclidean`, `cosine`, `manhattan`. Su un embedding UMAP le coordinate non sono sparse e la loro scala non ha un significato fisico:
  la scelta tra le tre metriche non ha una motivazione dalla letteratura per questo caso, ed è un'esplorazione del progetto.
- **Distanze precalcolate:** per `euclidean` (e `dice`/`jaccard`, supportate dal codice ma non nella griglia attuale) con linkage diverso da `ward`,
  la matrice delle distanze è calcolata una volta per metrica e riusata per fit e silhouette (`_agglomerative_fit_metric_aware`).
  È un'ottimizzazione: il risultato è lo stesso del fit diretto.
- **Costo:** con $n \approx 5800$ la matrice condensata ha circa 17 milioni di valori, circa 135 MB in `float64`.

## Parametri usati (significato: documentazione scikit-learn)
| Parametro | Nel progetto |
|---|---|
| `n_clusters` | sweep 2-30; base 3 |
| `linkage` | tutti e quattro (`ward`, `average`, `complete`, `single`); base `ward` |
| `metric` | `euclidean`, `cosine`, `manhattan`; base `euclidean`; con `ward` solo `euclidean` |
| `distance_threshold` | non usato nello sweep; `0` per avere l'albero intero (`compute_dendrogram_linkage`) |
| `connectivity` | non usato |
| `compute_full_tree` | default |
| `compute_distances` | `True` solo per dendrogramma e cofenetica |
| `memory` | non usato |

`ward` con metrica non euclidea è saltato con un avviso (`is_invalid_ward_metric_combo`): restano 10 coppie (linkage, metric) × 29 k = 290 combinazioni.
Il file dei parametri è stato condiviso da più run: va confrontato con la colonna `params` di `runs_tuning.csv` prima di rilanciare (`lessons_learned.md`, #36).

## Come lo ottimizziamo
Nessuna fonte dà una regola per scegliere linkage e k; le diagnostiche sono quelle classiche più due del progetto.
1. **Linkage, a metrica fissata:**
   - correlazione cofenetica per (metric, linkage), da confrontare solo dentro una metrica. Output: `cophenetic_correlation.csv` (`evaluate_clustering_tuning`);
   - accordo tra linkage: ARI tra le partizioni di due linkage allo stesso k (`linkage_agreement.csv`). Dove è vicino a 1 la scelta del linkage cambia poco. Scelta del progetto.
2. **Numero di cluster:**
   - **salto del dendrogramma** (colonna `jump` di `tuning_results.csv`): l'altezza della fusione da $k$ a $k-1$ cluster divisa per quella da $k+1$ a $k$;
     con $h_1 \ge h_2 \ge \dots$ le altezze dalla più alta, $J(k) = h_{k-1}/h_k$. È una diagnostica del progetto, senza fasce di letteratura;
   - indici per k: silhouette (con la stessa `metric`), e CH e DB solo per `euclidean` (colonne di `tuning_results.csv`).
     Le curve `k_curves_metric=<metric>.png` disegnano silhouette e DB (DB solo per `euclidean`), una linea per linkage.
     Si cerca un picco della silhouette e una valle di DB **stabili** tra linkage, non un massimo isolato.
     `single` non è disegnato (la sua silhouette scende molto sotto quella degli altri): i suoi valori sono nelle tabelle del report.
3. **Stabilità rispetto all'embedding:** stesso k e linkage su UMAP con `n_components` diversi: ARI tra le partizioni e contingenza dei cluster
   (confronto tra più run: non è nel `report.md` di una singola run).

Guida operativa ai grafici: [clustering_tuning_guide](clustering_tuning_guide.md), sezioni "Agglomerative".

## Come leggiamo l'output
- **Indici interni** (vedi [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md)): silhouette con la metrica del clustering; CH e DB solo con `euclidean` (`NaN` altrimenti). Nessun rumore: `noise_fraction` è sempre 0.
- **Del modello:** correlazione cofenetica e salto del dendrogramma al k della run (`model_fit_metrics`, `src/analysis/clustering_evaluation.py`).
  Il fit viene ripetuto e accettato solo se riproduce le etichette salvate.
- **Silhouette per cluster:** tabella per cluster.

## Attenzioni specifiche
- **Pareggi nelle distanze:** con distanze uguali (frequenti su un embedding UMAP molto impacchettato, o con `dice` saturata a 1) più coppie hanno lo stesso valore
  e l'ordine delle fusioni dipende dall'implementazione. Osservazione del progetto, non verificata su una fonte.
- **Embedding 2D:** de Bodt et al. (2025) raccomandano di non fare analisi a valle su embedding 2D; il progetto clusterizza anche su `n_components=2`
  e confronta con 3 e 10 proprio per questo
  (vedi [challenge_of_clustering_after_dim_reduction](../../../knowledge/concepts/Machine_Learning/Unsupervised/challenge_of_clustering_after_dim_reduction.md)).
- **Linkage non usati:** `centroid` e `median` non sono usati dal progetto.
