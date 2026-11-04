# K-means in NEMESIS

- **Teoria:** [K-means](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/kmeans.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Clustering/kmeans.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/kmeans.md) (derivata, non è una fonte)

Metodo `"kmeans"` in `CLUSTERING_METHODS` (`src/analysis/clustering.py`), `sklearn.cluster.KMeans`
(scikit-learn 1.8.0, ambiente `nemesis`). Parametri: `config/registry/params_clustering.json`, voce `"kmeans"`.
Altri metodi: [README](README.md). Metriche condivise: [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).

## Su cosa lo applichiamo
- **Input:** un embedding, non la matrice grezza. Le run esistenti usano UMAP a 2, 3 o 10 componenti (sessioni `s1.1-vol`, `s1.2-vol`,
  `s2.1-schaefer-200-tian-s2`, `s2.2-vol`) e, in produzione, la matrice SDC streamline a 87 colonne (sessione `s2.3-stream`).
  Su score PCA non è stato lanciato. Soggetti: da circa 1100 a circa 5800.
- **Distanza:** sempre euclidea (K-means non ne accetta altre). Su UMAP K-means prende le distanze dell'embedding così come sono.
- **Scala:** negli score PCA le prime componenti hanno varianza maggiore e quindi contano di più nella distanza; se sia voluto è una scelta del progetto.
- **Costo:** con $n \approx 5000$, $k \le 30$ e poche dimensioni un fit richiede frazioni di secondo; è il metodo più economico della pipeline.

## Parametri usati (significato: documentazione scikit-learn)
| Parametro | Nel progetto |
|---|---|
| `n_clusters` | base 6; griglia 2-30 |
| `init` | non impostato, quindi `"k-means++"` |
| `n_init` | `"auto"`: con `init="k-means++"` vale **1** sola inizializzazione |
| `max_iter`, `tol`, `algorithm` | default |
| `random_state` | 0 |

## Come lo ottimizziamo
1. **Stabilità dell'inizializzazione** (blocco `"stability"` in `params_clustering.json`): per 3 valori rappresentativi di `n_clusters`
   (minimo, mediana e massimo della griglia) ripete il fit con `init` in `["k-means++", "random"]`, `n_init` in `[1, 5, 10, 15, 20]` e 5 semi,
   registrando l'inertia. Se l'inertia varia molto tra semi a `n_init=1`, i valori della sweep principale dipendono dal seme.
   Lettura: [clustering_tuning_guide](clustering_tuning_guide.md), "Stabilità dell'inizializzazione".
2. **Sweep di `n_clusters`** da 2 a 30: per ogni $k$ silhouette, Calinski-Harabasz, Davies-Bouldin e inertia.
3. **Curva dell'inertia ("gomito"):** criterio visivo, senza una regola formale.
4. **Gap statistic** (Tibshirani, Walther & Hastie): funzione post-hoc `compute_gap_statistic` in `src/analysis/clustering_tuning.py`,
   non collegata alla pipeline. Riferimento: distribuzione uniforme nel box delle feature, la più semplice delle due proposte in Tibshirani et al.
   (l'altra allinea il box alle componenti principali).
5. **Stabilità del numero di cluster** (opzionale, blocco `"consensus"`): co-occorrenza tra ripetizioni a semi diversi (RSC) o su sottocampioni
   (Monti et al.); vedi [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md), sezione 7.

Il tuning non sceglie $k$ da solo (regola del progetto, [clustering_tuning_guide](clustering_tuning_guide.md)).

## Come leggiamo l'output
- **Indici interni** (silhouette, Calinski-Harabasz, Davies-Bouldin): definizioni e limiti in [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).
- **Inertia:** solo per confrontare valori di $k$ sullo stesso input; non si confronta tra embedding diversi (scala diversa).
- **Dimensioni dei cluster e profili dei centroidi:** un centroide è un punto dell'embedding, interpretabile tornando ai soggetti vicini
  (nell'Embedding Explorer, [embedding_app](../../guides/embedding_app.md)).
- **Riproducibilità:** ARI tra le partizioni di semi diversi. Un ARI basso tra semi dice che la partizione è uno dei tanti minimi locali.

## Attenzioni specifiche
- Con `n_init="auto"` e `init="k-means++"` ogni fit è un solo k-means++: un singolo minimo locale per ogni $k$ della sweep,
  se la stability analysis non mostra che basta.
- Silhouette e Calinski-Harabasz premiano la geometria convessa che K-means impone: un valore alto conferma in parte l'assunzione del metodo, non la struttura dei dati.
- Su UMAP la densità non è conservata del tutto e possono comparire false separazioni (*false tears*) dentro un cluster vero.
- Negli score PCA le prime componenti pesano di più nella distanza (vedi "Scala").
