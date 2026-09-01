# Log Esperimenti: Clustering — Tuning SDC

**Pipeline:** `clustering`
**Dati:** Embedding UMAP di produzione, sessione SDC s2.1 (5269 soggetti).

---

## 01-09-2026 — s2.1 (nc2)

**Obiettivo:** Tuning sui dati di disconnessione strutturale (SDC) a partire dall'embedding `01-09_s2.1_m_euclidean_nc2` per tutti e 5 i metodi, verificando se l'artefatto di lateralizzazione (`lesion_side`) e le metriche di silhouette seguono lo stesso andamento visto per i lesion embeddings (s1.1 e s1.2).

**Risultati Sintetici (Metriche ottimali)**

| Metodo         | Miglior combo (silhouette)                             | Link relativo                                                                               |
| -------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Agglomerative** | `k=3, average/ward/complete, euclidean` (~0.481)         | [tuning/agglomerative/](../../../results/sdc/clustering/tuning/agglomerative/umap/01-09_s2.1_m_euclidean_nc2/) |
| **GMM**           | `n_components=4, full` (0.496)                         | [tuning/gmm/](../../../results/sdc/clustering/tuning/gmm/umap/01-09_s2.1_m_euclidean_nc2/)                 |
| **KMeans**        | `k=4` (0.497)                                          | [tuning/kmeans/](../../../results/sdc/clustering/tuning/kmeans/umap/01-09_s2.1_m_euclidean_nc2/)              |
| **HDBSCAN**       | `mcs=20, ms=10` (0.475, noise 0.08) *[1]*              | [tuning/hdbscan/](../../../results/sdc/clustering/tuning/hdbscan/umap/01-09_s2.1_m_euclidean_nc2/)            |
| **Spectral**      | `n_clusters=8, rbf, gamma=1.0` (0.502)                 | [tuning/spectral/](../../../results/sdc/clustering/tuning/spectral/umap/01-09_s2.1_m_euclidean_nc2/)          |

*[1] Filtrato per `noise_fraction <= 0.1` per evitare la soluzione degenere a 0.608 con ~25% di dati marcati come rumore.*

**Check Artefatti e Considerazioni Finali:**

- Le metriche di Silhouette per `k` bassi (`k` compreso tra 3 e 6) si attestano in un range piuttosto compatto tra 0.45 e 0.50 per quasi tutti gli algoritmi.
- L'analisi del **Subsampling Stability Index** (calcolata su Agglomerative) restituisce valori di stabilità eccellenti (`> 0.95`).
- Il clustering SDC mostra un **forte e sistematico sbilanciamento su `lesion_side`**, replicando specularmente l'artefatto già noto sulle matrici di lesione.
- In tutte le configurazioni ottimali investigate tramite le crosstab nel notebook (es. `k=4` di KMeans o GMM), la partizione restituisce quasi sempre **cluster puri per emisfero** (es. gruppi da oltre 200 soggetti interamente "left" o interamente "right") e alcuni piccoli cluster "misti". In Spectral e HDBSCAN i cluster misti tendono a concentrare un maggior numero di soggetti, ma la struttura frammentata sui lati resta predominante.
- Questo conferma che la struttura della disconnessione strutturale (SDC), essendo strettamente derivata dalla maschera di lesione, ne eredita pesantemente la lateralizzazione. Nessuno degli algoritmi standard esplorati riesce a raggruppare i profili di disconnessione prescindendo spontaneamente dall'emisfero colpito. 

**Prossimi passi:**
Resta da estendere l'analisi esplorativa all'altra versione di embedding (`nc3`) generata per s2.1, per confermare se l'incremento di dimensionalità mitiga o conferma questi risultati, per poi decidere come uniformare la configurazione di produzione.
