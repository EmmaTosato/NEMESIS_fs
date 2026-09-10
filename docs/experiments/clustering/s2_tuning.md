# Diario Esperimenti

**Pipeline:** Clustering (Tuning)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 01-09-2026 — s2.1-schaefer-200-tian-s2 (nc2)

### Tuning SDC - 5 metodi SOTA

##### Input
- s2.1-schaefer-200-tian-s2
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `31-08_s2.1-schaefer-200-tian-s2_m_euclidean_nc2`
- Dati originali: `data/derived/sdc_matrix/27-08_s2.1-schaefer-200-tian-s2`
- 1119 soggetti
##### Metodi
Agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Verificare se l'artefatto di lateralizzazione (`lesion_side`) e le metriche di silhouette seguono lo stesso andamento visto per i lesion embeddings (s1.1-vol e s1.2-vol)

##### Risultati

| Metodo | Miglior combo (silhouette) | Link |
| --- | --- | --- |
| Agglomerative | `k=3, average/ward/complete, euclidean` (~0.481) | [tuning/agglomerative/](../../../results/sdc/clustering/tuning/agglomerative/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| GMM | `n_components=4, full` (0.496) | [tuning/gmm/](../../../results/sdc/clustering/tuning/gmm/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| KMeans | `k=4` (0.497) | [tuning/kmeans/](../../../results/sdc/clustering/tuning/kmeans/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| HDBSCAN | `mcs=20, ms=10` (0.475, noise 0.08) *[1]* | [tuning/hdbscan/](../../../results/sdc/clustering/tuning/hdbscan/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |
| Spectral | `n_clusters=8, rbf, gamma=1.0` (0.502) | [tuning/spectral/](../../../results/sdc/clustering/tuning/spectral/umap/01-09_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/) |

*[1] Filtrato per `noise_fraction ≤ 0.1` per evitare la soluzione degenere a 0.608 con ~25% di dati marcati come rumore.*

- Silhouette per `k` bassi (3-6) in fascia compatta 0.45–0.50 per quasi tutti gli algoritmi.
- Subsampling Stability Index (calcolato su Agglomerative): valori eccellenti (`> 0.95`).
- Forte e sistematico sbilanciamento su `lesion_side`, replica specularmente l'artefatto già noto sulle matrici di lesione — in tutte le configurazioni ottimali (crosstab, es. `k=4` di KMeans o GMM) la partizione restituisce quasi sempre cluster puri per emisfero (gruppi da oltre 200 soggetti interamente "left" o "right") e alcuni piccoli cluster misti. In Spectral e HDBSCAN i cluster misti concentrano più soggetti, ma la frammentazione sui lati resta predominante.
- Conferma che la struttura SDC, derivata direttamente dalla maschera di lesione, ne eredita pesantemente la lateralizzazione — nessuno degli algoritmi standard esplorati riesce a raggruppare i profili di disconnessione prescindendo spontaneamente dall'emisfero colpito.

##### Decisioni

- Estendere l'analisi esplorativa all'altra versione di embedding (`nc3`) generata per s2.1-schaefer-200-tian-s2, per confermare se l'incremento di dimensionalità mitiga o conferma questi risultati, per poi decidere come uniformare la configurazione di produzione.

---

## 10-09-2026 — s2.2-vol (nc2 e nc3)

### Tuning SDC voxel-wise - 5 metodi SOTA

##### Input
- s2.2-vol
- Embedding: UMAP `euclidean`, n_components=2 e 3
- Path Embedding: `07-09_s2.2-vol_m_euclidean_nc2` / `_nc3`
- Dati originali: `data/derived/sdc_matrix/07-09_s2.2-vol` (1570 x 290940)
- 1570 soggetti

##### Metodi
Agglomerative, gmm, kmeans, hdbscan, spectral — stessa sequenza del 01-09 su s2.1
(spectral lanciato a parte: `save_tuning_clusterings=true` non è supportato insieme a uno sweep su `affinity`)

##### Obiettivo
- Verificare se la versione voxel-wise dell'SDC produce una struttura di cluster diversa da quella parcellata (s2.1), o se ne eredita gli stessi limiti

##### Risultati

350 combinazioni totali (175 per dimensionalità). Miglior silhouette per metodo, `nc2`:

| Metodo | Miglior combo (silhouette) | Link |
| --- | --- | --- |
| Agglomerative | `k=2, average, cosine` (0.800) | [tuning/agglomerative/](../../../results/sdc/clustering/tuning/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| HDBSCAN | `mcs=10, ms=10` (0.619, 42 cluster, noise 0.24) *[1]* | [tuning/hdbscan/](../../../results/sdc/clustering/tuning/hdbscan/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| KMeans | `k=2` (0.571) | [tuning/kmeans/](../../../results/sdc/clustering/tuning/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| GMM | `n_components=2, spherical` (0.570) | [tuning/gmm/](../../../results/sdc/clustering/tuning/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2/) |
| Spectral | `k=2, rbf, gamma=1.0` (0.570) | [tuning/spectral/](../../../results/sdc/clustering/tuning/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2/) |

*[1] Soluzione degenere: 42 cluster con un quarto dei soggetti marcato come rumore. Non confrontabile con le altre righe.*

- **Ogni metodo, in entrambe le dimensionalità, ha il suo massimo a k=2** — a differenza di s2.1, dove l'ottimo cadeva a k=3-4 in fascia compatta 0.45–0.50. Qui la silhouette è nettamente più alta (0.57–0.80) proprio perché la partizione è più netta, non perché sia più informativa.
- **Il k=2 è l'emisfero.** Crosstab con `lesion_side` (KMeans, nc2): un cluster raccoglie 666 `left` e **0** `right`; l'altro 571 `right` e 101 `left`. Con Agglomerative `average/cosine` la separazione è ancora più pulita (762 `left` / 59 `right` contro 5 / 512).
- Salendo a k=4 la struttura non cambia natura, si frammenta soltanto: KMeans produce due cluster interamente `left` (417 e 232), uno quasi interamente `right` (357), e un solo cluster misto (115 `left` / 214 `right`). GMM `n_components=4, full` riproduce lo stesso schema.
- `nc3` dà silhouette leggermente più basse ma lo stesso ordinamento e gli stessi ottimi — l'aggiunta di una dimensione non introduce struttura nuova.
- **Conclusione**: l'artefatto di lateralizzazione già documentato per s2.1 non è attenuato dalla rappresentazione voxel-wise, è *accentuato*. Su s2.1 gli algoritmi frammentavano in più cluster con qualche gruppo misto; qui la geometria dominante dell'embedding è un asse destra/sinistra e ogni algoritmo, indipendentemente dal criterio, taglia lungo quell'asse.

##### Decisioni
