# Log Esperimenti: Clustering — Tuning

**Pipeline:** `clustering`
**Dati:** Embedding UMAP di produzione, sessione lesion matrix s1.1 (1150 soggetti).

---

## 27/28-08-2026 — s1.1
#### Tuning agglomerative su 6 embedding UMAP (metric × n_components)

**Obiettivo:**
- Sweep `n_clusters` × `linkage` × `metric` per agglomerative su tutti e 6 gli embedding UMAP di produzione (`dice`/`euclidean` × `n_components`∈{2,3,10}).
- Verificare se un `k` di produzione emerge in modo robusto, e se è indipendente da confondenti noti (`lesion_side`, `dataset`, volume).
- KMeans/GMM/HDBSCAN/Spectral: sweep lanciata (27-08) sugli stessi 6 embedding, non ancora analizzata in dettaglio.

**Strategie testate**
- modality: Lesion embedding (UMAP, post dim_reduction)
- datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR

| Metodo | Run | Griglia | Link |
|---|---|---|---|
| Agglomerative | 6×70 | `n_clusters`∈{2,3,4,5,6,8,10} × `linkage`∈{ward,average,complete,single} × `metric`∈{euclidean,cosine,manhattan} | [tuning/agglomerative/](../../../results/lesion/clustering/tuning/agglomerative/) |
| KMeans, GMM, HDBSCAN, Spectral | — | vedi `tuning_grid` per metodo in `params_clustering.json` | [tuning/](../../../results/lesion/clustering/tuning/) — non ancora analizzato |

**Risultati:**

1. **k=2 = artefatto `lesion_side`, confermato su tutti e 6 gli embedding** (crosstab `clusterings.npz` × `metadata.csv`): silhouette alto (0.64–0.95 su `dice`, 0.35–0.46 su `euclidean`) ma lo split ricalca quasi esattamente il lato della lesione, non struttura clinica.
2. **Interclass distance matrix** (proxy `dataset`) quasi piatta su tutte e 3 le run `euclidean` — nessuna `metric` favorita per separare i siti; unica eccezione debole e stabile: PSP mostra compattezza interna (~11–13% sotto la media inter-sito) a ogni `n_components` testato.
3. **Dendrogrammi (`euclidean_n2`)**: `single` va scartato (chaining, scala non interpretabile); `ward`/`average` concordano quasi esattamente sul primo taglio (k=2); nessun secondo salto si stacca nettamente dagli altri.
4. **k "migliore" post-k=2 (`linkage`≠single, `metric`=euclidean)**: `average`/`ward` convergono **dentro** ogni singolo embedding, ma **non tra embedding diversi** — k=5 (n2), k=3 (n3), k=4 (n10). Ogni volta la struttura sottostante è la stessa: 1-2 cluster quasi puri per lato lesione, distinti tra loro dal volume, più un cluster misto a basso volume.
5. Nessun artefatto di sito rilevato nei k candidati controllati (`dataset` ben distribuito in ogni cluster).
6. **`average` e `ward` a k=5 (`euclidean_n3`), quantificato**: ARI=0.68/NMI=0.81 tra le due partizioni — accordo sostanziale ma non identico (meno di quanto sembrasse a occhio dai crosstab). Entrambi però singolarmente molto stabili al subsampling 80% (Subsampling Stability Index: `average`=1.00, `ward`=0.96) — non è un problema di rumore/outlier, sono due risposte diverse e ugualmente solide alla stessa domanda. La stabilità da sola non basta a scegliere tra i due linkage.

**Decisioni aperte:**
- **`n_components` e `k` vanno decisi insieme, non in sequenza** — il k "migliore" non è stabile al variare della dimensionalità dell'embedding (punto 4). Assi possibili, nessuno ancora scelto:
  - (A) convergenza cross-metodo a parità di `n_components` (kmeans/gmm/spectral/agglomerative)
  - (B) consenso/stabilità (RSC/Monti) sulla coorte reale come criterio finale — item già aperto in `management/notes/TODO.md`
  - (C) regressare `lesion_side`/`lesion_volume_voxels` dall'embedding prima del clustering, invece di scoprire l'artefatto a valle
  - (D) criterio clinico (differenziazione su outcome oltre side/volume) invece che puramente geometrico
- KMeans/GMM/HDBSCAN/Spectral da analizzare con lo stesso schema (diagnostica standalone → tabella tuning → crosstab artefatto) prima di poter applicare l'asse (A).

**Strumenti:** [`notebooks/post-results_analysis/clustering_tuning_explorer.ipynb`](../../../notebooks/post-results_analysis/clustering_tuning_explorer.ipynb) — esplorazione interattiva `tuning_results.csv` + diagnostiche per run scelta; esteso con ARI/NMI tra due combinazioni della stessa sweep e Subsampling Stability Index per un candidato (portati da `clustering_evaluation.ipynb`, adattati per girare direttamente su una sweep di tuning senza bisogno di una run di produzione).
