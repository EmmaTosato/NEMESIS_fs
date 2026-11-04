# GMM in NEMESIS

- **Teoria:** [Gaussian Mixture Model (GMM)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/gmm.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Clustering/gmm.md`)
- **Letteratura:** nei `sources` della nota teorica

Metodo `"gmm"` in `CLUSTERING_METHODS` (`src/analysis/clustering.py`), `sklearn.mixture.GaussianMixture`
(scikit-learn 1.8.0, ambiente `nemesis`). Parametri: `config/registry/params_clustering.json`, voce `"gmm"`.
Altri metodi: [README](README.md). Metriche condivise: [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).
BIC, AIC e ICL, specifici di questo metodo, sono definiti nella nota teorica.

## Su cosa lo applichiamo
- **Input:** embedding UMAP a 2, 3 o 10 componenti o score PCA (fino a 12 componenti in `s2.4-vol`), con circa 1100-5900 soggetti
  a seconda della coorte (1119, 1150, 1570, 5269, 5845 nelle matrici salvate).
- **Numero di parametri:** con $d=2$ e $k=6$ `full` sono $18 + 12 + 5 = 35$; con $d=12$ e $k=30$ `full` sono $2340 + 360 + 29 = 2729$.
  Su 5845 soggetti è ancora stimabile, ma `full` ad alto $k$ si avvicina al limite in cui ogni componente ha pochi soggetti per parametro.
- **Forma dei gruppi:** la mistura assume gruppi ellissoidali. Gli embedding UMAP non conservano del tutto la densità: un gruppo visibile
  in UMAP non è necessariamente Gaussiano, e il BIC può spezzarlo in più componenti.
- **Produzione:** `gmm_cluster` usa `fit_predict`, cioè solo l'etichetta più probabile. Le probabilità soft (`predict_proba`) non vengono salvate (scelta del progetto).
- **Dimensione della sweep:** 29 valori di $k$ x 4 `covariance_type` = 116 fit per run. Il tempo per fit non è stato misurato separatamente.

## Parametri usati (significato: documentazione scikit-learn)
| Parametro | Nel progetto |
|---|---|
| `n_components` | base 6; griglia 2-30 |
| `covariance_type` | base `spherical`; griglia tutte e 4 (`full`, `tied`, `diag`, `spherical`) |
| `tol`, `reg_covar`, `max_iter` | default |
| `n_init` | default (1) |
| `init_params` | default |
| `random_state` | 0 |

## Come lo ottimizziamo
1. **Stabilità dell'inizializzazione** (blocco `"stability"`): prova `init_params` in `["kmeans", "random"]` con `n_init` in `[1, 5, 10, 15, 20]`
   e 5 semi, registrando il BIC. Se il BIC a parità di $k$ varia molto tra semi a `n_init=1`, la sweep principale va letta con cautela o `n_init` va alzato.
   Lettura: [clustering_tuning_guide](clustering_tuning_guide.md).
2. **Sweep congiunta di `n_components` x `covariance_type`**.
3. **Lettura di BIC e AIC:** più basso è meglio (convenzione sklearn). Se la curva scende fino all'ultimo $k$ della griglia,
   la griglia non arriva al punto di svolta e il criterio non indica nulla in quel range ([clustering_tuning_guide](clustering_tuning_guide.md)).
4. **ICL** come controllo post-hoc.
5. **Indici geometrici** (silhouette, CH, DB) come confronto: [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).
6. **Stabilità del numero di cluster** (opzionale, blocco `"consensus"`): vedi [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md), sezione 7.

L'ICL è la funzione post-hoc `integrated_completed_likelihood` in `src/analysis/clustering_tuning.py`, non collegata alla pipeline.

## Come leggiamo l'output
- **BIC/AIC:** confrontabili solo tra modelli stimati sugli stessi dati; non si confrontano tra embedding o sessioni diverse.
- **Certezza dell'assegnazione:** le responsabilità $\gamma_{ij}$ dicono quanto ogni soggetto è vicino a un confine. Oggi la pipeline non le salva: si ricalcolano con `predict_proba`.
- **Dimensione e pesi delle componenti:** una componente con $\pi_j$ molto piccolo o pochi soggetti può servire solo a descrivere code o outlier.
- **Indici geometrici e riproducibilità tra semi** (ARI): [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).

## Attenzioni specifiche
- `n_init=1` di default: un solo massimo locale per combinazione, se la stability analysis non mostra che basta.
- `spherical` come base: cluster sferici come K-means, ma con varianza e peso propri per ogni componente; con gruppi di varianza diversa
  le etichette divergono da quelle di K-means (su due gruppi sintetici di varianza 3.0 e 0.5, ARI 0.24 tra i due).
  Le forme non sferiche richiedono `diag`, `tied` o `full`.
- Solo l'etichetta in produzione: l'informazione di incertezza, il vantaggio principale del metodo, oggi non arriva ai risultati salvati.
- Il BIC può spezzare in più componenti un gruppo UMAP non Gaussiano.
