# Diario Esperimenti

**Pipeline:** Clustering (Tuning)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Vedi session_data.md per specifica sulle sessioni

---

## 01-09-2026 — s2.1 (nc2)

#### Tuning SDC, tutti e 5 i metodi

- **Input:**
    - s2.1
    - Embedding: UMAP `euclidean`, n_components=2
    - Path: `01-09_s2.1_m_euclidean_nc2`
    - Dati originali: `data/derived/sdc_matrix/27-08_s2.1`
    - 1119 soggetti
- **Metodi:** agglomerative, gmm, kmeans, hdbscan, spectral
- **Obiettivo:**
    - Verificare se l'artefatto di lateralizzazione (`lesion_side`) e le metriche di silhouette seguono lo stesso andamento visto per i lesion embeddings (s1.1 e s1.2)

**Risultati**

| Metodo | Miglior combo (silhouette) | Link |
| --- | --- | --- |
| Agglomerative | `k=3, average/ward/complete, euclidean` (~0.481) | [tuning/agglomerative/](../../../results/sdc/clustering/tuning/agglomerative/umap/01-09_s2.1_m_euclidean_nc2/) |
| GMM | `n_components=4, full` (0.496) | [tuning/gmm/](../../../results/sdc/clustering/tuning/gmm/umap/01-09_s2.1_m_euclidean_nc2/) |
| KMeans | `k=4` (0.497) | [tuning/kmeans/](../../../results/sdc/clustering/tuning/kmeans/umap/01-09_s2.1_m_euclidean_nc2/) |
| HDBSCAN | `mcs=20, ms=10` (0.475, noise 0.08) *[1]* | [tuning/hdbscan/](../../../results/sdc/clustering/tuning/hdbscan/umap/01-09_s2.1_m_euclidean_nc2/) |
| Spectral | `n_clusters=8, rbf, gamma=1.0` (0.502) | [tuning/spectral/](../../../results/sdc/clustering/tuning/spectral/umap/01-09_s2.1_m_euclidean_nc2/) |

*[1] Filtrato per `noise_fraction ≤ 0.1` per evitare la soluzione degenere a 0.608 con ~25% di dati marcati come rumore.*

- Silhouette per `k` bassi (3-6) in fascia compatta 0.45–0.50 per quasi tutti gli algoritmi.
- Subsampling Stability Index (calcolato su Agglomerative): valori eccellenti (`> 0.95`).
- Forte e sistematico sbilanciamento su `lesion_side`, replica specularmente l'artefatto già noto sulle matrici di lesione — in tutte le configurazioni ottimali (crosstab, es. `k=4` di KMeans o GMM) la partizione restituisce quasi sempre cluster puri per emisfero (gruppi da oltre 200 soggetti interamente "left" o "right") e alcuni piccoli cluster misti. In Spectral e HDBSCAN i cluster misti concentrano più soggetti, ma la frammentazione sui lati resta predominante.
- Conferma che la struttura SDC, derivata direttamente dalla maschera di lesione, ne eredita pesantemente la lateralizzazione — nessuno degli algoritmi standard esplorati riesce a raggruppare i profili di disconnessione prescindendo spontaneamente dall'emisfero colpito.

**Decisioni**

- Estendere l'analisi esplorativa all'altra versione di embedding (`nc3`) generata per s2.1, per confermare se l'incremento di dimensionalità mitiga o conferma questi risultati, per poi decidere come uniformare la configurazione di produzione.
