# Clustering Tuning Results s1.1

## 26-07-2026 Analysis

- Dati: matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)
- Sessione `s1.1`.
- 4 metodi di riduzione (umap, pacmap, tsne, pca)
- 5 metodi di clustering (kmeans, agglomerative, gmm, dbscan, spectral — spectral escluso di proposito su pacmap, vedi sotto).
- Tuning su metodi di clustering
- Note:
  - Come leggere ogni indice/plot: [docs/methods/clustering_tuning_guide.md](../../docs/methods/clustering_tuning_guide.md).
  - Questo documento non seleziona automaticamente nessun parametro

### UMAP (min_dist=0.0, n_neighbors=5)

#### KMeans

| k                     | silhouette      | Calinski-Harabasz | Davies-Bouldin  |
| --------------------- | --------------- | ----------------- | --------------- |
| 2                     | 0.427           | 1105              | 0.946           |
| 3                     | 0.474           | 1417              | 0.764           |
| **4 (default)** | **0.497** | 1553              | **0.693** |
| 5                     | 0.496           | 1497              | 0.716           |
| 6                     | 0.475           | 1521              | 0.801           |
| 8                     | 0.469           | 1672              | 0.774           |
| 10                    | 0.440           | 1733              | 0.750           |

**k=4 è la scelta migliore**: silhouette massimo (pareggiato con k=5, 0.497 vs 0.496), Davies-Bouldin minimo netto (0.693). Calinski-Harabasz non è il più alto in assoluto (cresce con k come atteso) ma è già competitivo a k=4. Inertia (curva a gomito) non mostra un gomito netto, scende in modo regolare. **Nessun cambiamento consigliato rispetto al default.**

#### Agglomerative

| k                     | silhouette                    | Calinski-Harabasz | Davies-Bouldin |
| --------------------- | ----------------------------- | ----------------- | -------------- |
| 2                     | 0.456                         | 908               | 0.738          |
| 3                     | 0.425                         | 1098              | 0.719          |
| **4 (default)** | **0.419** ⚠️ peggiore | 1216              | 0.754          |
| **5**           | **0.485**               | 1423              | 0.743          |
| 6                     | 0.483                         | 1465              | 0.751          |
| 8                     | 0.453                         | 1578              | 0.757          |
| 10                    | 0.453                         | 1659              | 0.745          |

Il default k=4 ha il **silhouette più basso di tutta la griglia** (0.419, peggio anche di k=2). k=5 vince nettamente sul silhouette (0.485) ed è competitivo su Davies-Bouldin (0.743, terzo migliore dopo k=3 0.719 e k=2 0.738 — differenze comunque piccole, range 0.72-0.76). Dendrogramma: il salto più grande è alla radice (97→68, gap 29) ma non è dominante come su pacmap/tsne (il secondo salto è 68→47, gap 21 — non trascurabile), quindi la struttura non è nettamente binaria. **Raccomandazione: k=5**, chiaro miglioramento rispetto al default attuale.

#### GMM

| n                     | silhouette      | Calinski-Harabasz | Davies-Bouldin  | BIC  | AIC  |
| --------------------- | --------------- | ----------------- | --------------- | ---- | ---- |
| 2                     | 0.431           | 987               | 0.969           | 9591 | 9536 |
| 3                     | 0.446           | 1211              | 0.767           | 9318 | 9232 |
| **4 (default)** | **0.496** | **1549**    | **0.693** | 9153 | 9037 |
| 5                     | 0.495           | 1460              | 0.722           | 9057 | 8910 |
| 6                     | 0.444           | 1272              | 0.890           | 8705 | 8529 |
| 8                     | 0.431           | 1425              | 0.899           | 8626 | 8389 |
| 10                    | 0.405           | 1232              | 1.688           | 8506 | 8208 |

n=4 vince **tutti e tre** gli indici generici: silhouette massimo (pareggiato con n=5), Davies-Bouldin minimo, e — caso raro — Calinski-Harabasz ha un vero picco a n=4 (non solo un trend crescente: scende dopo). BIC/AIC scendono monotonicamente fino a n=10 senza risalire, quindi non informativi qui (pattern di overfitting tipico, vedi guida). **Nessun cambiamento consigliato: n=4 è la scelta più solida di tutto lo studio.**

#### DBSCAN

| eps                     | silhouette                              | Calinski-Harabasz | Davies-Bouldin | noise |
| ----------------------- | --------------------------------------- | ----------------- | -------------- | ----- |
| 0.3                     | -0.073                                  | 288               | 2.078          | 1.0%  |
| **0.5 (default)** | **-0.106**                        | 235               | 0.912          | 0.0%  |
| 0.7                     | 0.006                                   | 339               | 1.024          | 0.0%  |
| 1.0-2.0                 | degenerato (NaN, collassa in 1 cluster) | —                | —             | 0.0%  |

Il silhouette è **vicino a zero o negativo su tutto il range testato** — DBSCAN non trova struttura basata su densità in questo embedding, indipendentemente da `eps`. Il k-distance plot mostra una salita graduale fino a ~1050/1150 punti, poi un'impennata solo intorno a distanza 0.25-0.35 — più bassa del più piccolo `eps` testato (0.3), suggerendo che varrebbe la pena testare `eps` ancora più piccoli (~0.15-0.2) in un round di tuning dedicato. **Con la griglia attuale, DBSCAN non è consigliabile su umap.**

#### Spectral

| n                     | silhouette      | Calinski-Harabasz | Davies-Bouldin  |
| --------------------- | --------------- | ----------------- | --------------- |
| 2                     | 0.456           | 908               | 0.738           |
| 3                     | 0.441           | 1168              | 0.880           |
| **4 (default)** | 0.477           | 1442              | 0.700           |
| 5                     | 0.469           | 1331              | 0.723           |
| 6                     | 0.492           | 1479              | 0.738           |
| **8**           | **0.493** | 1564              | **0.677** |
| 10                    | 0.436           | 1722              | 0.770           |
| 11                    | 0.422           | 1716              | 0.755           |
| 12                    | 0.416           | 1744              | 0.760           |
| 13                    | 0.407           | 1694              | 0.758           |
| 14                    | 0.417           | 1770              | 0.772           |
| 15                    | 0.413           | 1801              | 0.785           |

n=8 vince silhouette (0.493, appena sopra n=6 0.492) e Davies-Bouldin (0.677, il migliore). Il default n=4 è decente ma non ottimale su nessuno dei due.

**Round di tuning aggiuntivo (griglia estesa a 15, per verificare l'eigengap)**: l'eigengap (diagnostica indipendente sulla struttura del grafo) suggeriva un salto più grande dopo l'11° autovalore, indicando n≈11 come possibile numero naturale di cluster. Rilanciato il tuning con la griglia estesa fino a 15 (`results/lesion/dim_reduction_clustering/umap/spectral/tuning/26-07_s1.1_d00`): **l'indicazione non regge sui dati**. Da n=11 in poi il silhouette *peggiora* monotonicamente rispetto al picco a n=8 (0.493 → 0.422 a n=11 → 0.407 al minimo locale n=13), e Davies-Bouldin non migliora oltre n=8 (0.677, il minimo di tutta la griglia estesa). Calinski-Harabasz continua a crescere con n (atteso, cresce quasi sempre con più cluster, non è un segnale di qualità autonomo). **Conclusione: n=8 resta la scelta migliore confermata su tutta la griglia 2-15** — l'eigengap qui indicava una struttura del grafo di similarità che non si traduce in una separazione migliore dei cluster nello spazio embedded.

---

### PACMAP (n_neighbors=5)

*Spectral escluso di proposito: fonde sempre uno dei due gruppi satellite disconnessi nel blob principale, indipendentemente da n_neighbors (osservato in sessione precedente).*

#### KMeans

| k                     | silhouette      | Calinski-Harabasz | Davies-Bouldin  |
| --------------------- | --------------- | ----------------- | --------------- |
| 2                     | **0.506** | 1621              | 0.746           |
| 3                     | 0.450           | 1547              | 0.820           |
| **4 (default)** | 0.479           | 1386              | 0.655           |
| 5                     | 0.434           | 1362              | 0.884           |
| **6**           | 0.504           | **1970**    | **0.581** |
| 8                     | 0.495           | 2436              | 0.630           |
| 10                    | 0.475           | 2564              | 0.726           |

Silhouette sostanzialmente pareggiato tra k=2 (0.506) e k=6 (0.504, differenza trascurabile). Davies-Bouldin e Calinski-Harabasz concordano entrambi nettamente su **k=6**. Il default k=4 non vince su nessun indice. **Raccomandazione: k=6**; k=2 resta un'alternativa legittima se si preferisce una struttura più macro (coerente con l'esclusione di spectral per lo stesso motivo — vedi sotto).

#### Agglomerative

| k                     | silhouette      | Calinski-Harabasz | Davies-Bouldin   |
| --------------------- | --------------- | ----------------- | ---------------- |
| **2**           | **0.489** | 1551              | 0.733            |
| 3                     | 0.430           | 1438              | 0.912 (peggiore) |
| **4 (default)** | 0.439           | 1304              | 0.677            |
| **5**           | 0.478           | 1375              | **0.541**  |
| 6                     | 0.458           | 1695              | 0.641            |
| 8                     | 0.466           | 2084              | 0.594            |
| 10                    | 0.451           | 2491              | 0.713            |

Tensione tra silhouette (picco k=2) e Davies-Bouldin (nettamente migliore a k=5, 0.541 contro 0.733 di k=2). Dendrogramma: il salto più grande è alla radice (365→180, ben più grande dei salti successivi ~110-180) — conferma k=2 come struttura visivamente più dominante, coerente col pattern "blob + satelliti" già noto. **Nessuna raccomandazione netta**: k=2 se si privilegia la struttura macro più naturale (e coerente col resto dell'evidenza su pacmap), k=5 se si privilegiano cluster compatti internamente.

#### GMM

| n                     | silhouette             | Calinski-Harabasz | Davies-Bouldin  | BIC   | AIC   |
| --------------------- | ---------------------- | ----------------- | --------------- | ----- | ----- |
| 2                     | **0.512**        | 1611              | 0.745           | 14768 | 14712 |
| 3                     | 0.433                  | 1443              | 0.848           | 14630 | 14544 |
| **4 (default)** | 0.374 (tra i peggiori) | 780               | 1.022           | 13816 | 13700 |
| 5                     | 0.436                  | 1030              | 1.018           | 13444 | 13298 |
| **6**           | 0.485                  | **1725**    | **0.584** | 13206 | 13029 |
| 8                     | 0.389                  | 1445              | 0.635           | 12923 | 12686 |
| 10                    | 0.387                  | 1873              | 0.837           | 12888 | 12590 |

Stesso pattern di kmeans: silhouette preferisce n=2, ma Davies-Bouldin e Calinski-Harabasz convergono su **n=6**. Il default n=4 è tra i **peggiori** valori della griglia su silhouette (0.374, quasi il minimo). BIC/AIC scendono monotonicamente, non informativi. **Raccomandazione: n=6** (o n=2 per lo split macro) — il default attuale n=4 è una scelta debole, da cambiare in ogni caso.

#### DBSCAN — trade-off qualità/copertura

| eps                     | silhouette      | Calinski-Harabasz | Davies-Bouldin  | noise                |
| ----------------------- | --------------- | ----------------- | --------------- | -------------------- |
| **0.3**           | **0.642** | **8981**    | **0.419** | **36.3%** ⚠️ |
| **0.5 (default)** | 0.284           | 689               | 0.688           | 8.4%                 |
| 0.7                     | 0.118           | 637               | 0.663           | 1.7%                 |
| 1.0-2.0                 | ~0.28 (piatto)  | ~98               | ~0.67 (piatto)  | ≤0.5%               |

`eps=0.3` vince su tutti e tre gli indici di qualità ma scarta il 36% della coorte. Il default `eps=0.5` è un compromesso ragionevole (8.4% noise, qualità nettamente inferiore al picco). **Non c'è una risposta oggettiva**: è una scelta esplicita tra qualità della separazione e copertura della coorte.

---

### TSNE (perplexity=30)

#### KMeans

| k                     | silhouette       | Calinski-Harabasz | Davies-Bouldin   |
| --------------------- | ---------------- | ----------------- | ---------------- |
| 2                     | 0.411            | 1081              | 0.948 (peggiore) |
| 3                     | 0.389            | 1071              | 0.913            |
| **4 (default)** | 0.367 (peggiore) | 964               | 0.925            |
| **5**           | **0.410**  | **1154**    | **0.831**  |
| 6                     | 0.388            | 1123              | 0.890            |
| 8                     | 0.386            | 1125              | 0.829            |
| 10                    | 0.365            | 1140              | 0.857            |

Il default k=4 ha il **silhouette peggiore** di tutta la griglia insieme a k=10. k=5 è quasi a pari merito col miglior silhouette (k=2, 0.411 vs 0.410) ma ha anche il miglior/quasi-miglior Davies-Bouldin (0.831, contro 0.948 di k=2) e un picco locale di Calinski-Harabasz (1154, il più alto). **Raccomandazione: k=5**, cambiamento chiaro rispetto al default.

#### Agglomerative

| k                     | silhouette      | Calinski-Harabasz | Davies-Bouldin   |
| --------------------- | --------------- | ----------------- | ---------------- |
| **2**           | **0.398** | 1004              | 0.951            |
| 3                     | 0.335           | 869               | 1.045 (peggiore) |
| **4 (default)** | 0.340           | 870               | 0.989            |
| 5                     | 0.322           | 913               | 0.926            |
| **6**           | 0.337           | 955               | **0.879**  |
| 8                     | 0.340           | 987               | 0.880            |
| 10                    | 0.330           | 1001              | 0.888            |

Struttura debole ovunque (silhouette 0.32-0.40, valori bassi rispetto a umap/pacmap). Silhouette nettamente più alto a k=2 (0.398 contro il secondo migliore 0.340). Dendrogramma: il salto alla radice (670→360, gap 310) è **di gran lunga** il più grande dell'albero — conferma fortemente k=2 come taglio naturale. Davies-Bouldin preferirebbe k=6 (0.879) ma il margine sul resto della griglia è modesto. **Raccomandazione: k=2**, supportata sia da silhouette sia dal dendrogramma.

#### GMM

| n                     | silhouette       | Calinski-Harabasz | Davies-Bouldin  | BIC   | AIC   |
| --------------------- | ---------------- | ----------------- | --------------- | ----- | ----- |
| **2**           | **0.416**  | **1058**    | 0.933           | 18602 | 18547 |
| 3                     | 0.381            | 1032              | 0.944           | 18538 | 18452 |
| **4 (default)** | 0.365 (peggiore) | 878               | 0.873           | 18480 | 18364 |
| 5                     | 0.370            | 957               | **0.815** | 18360 | 18214 |
| 6                     | 0.378            | 1004              | 0.907           | 18395 | 18219 |
| 8                     | 0.376            | 1026              | 0.863           | 18410 | 18173 |
| 10                    | 0.351            | 1022              | 0.881           | 18426 | 18128 |

n=2 vince silhouette e Calinski-Harabasz nettamente; Davies-Bouldin preferisce leggermente n=5 (0.815 contro 0.933 di n=2), ma il default n=4 è comunque tra i peggiori su silhouette. BIC/AIC non informativi (monotoni). **Raccomandazione: n=2** come scelta primaria (2 indici su 3 d'accordo), n=5 come alternativa se si vuole ottimizzare solo Davies-Bouldin.

#### DBSCAN — ⚠️ attenzione al default

| eps                     | silhouette | Calinski-Harabasz | Davies-Bouldin | noise                |
| ----------------------- | ---------- | ----------------- | -------------- | -------------------- |
| 0.3                     | degenerato | —                | —             | **99.6%**      |
| **0.5 (default)** | 0.988      | 37019             | 0.014          | **98.9%** ⚠️ |
| 0.7                     | 0.951      | 7262              | 0.060          | 96.2%                |
| 1.0                     | 0.548      | 1218              | 0.342          | 82.3%                |
| **1.5**           | 0.302      | 504               | 0.628          | **33.2%**      |
| 2.0                     | -0.179     | 78                | 0.826          | 9.5%                 |

**Il default `eps=0.5` classifica il 98.9% della coorte come rumore** — resterebbero solo ~13 soggetti su 1150 come "cluster reale". I valori di silhouette apparentemente ottimi a eps=0.5/0.7 (0.988, 0.951) sono un **artefatto**: calcolati su una manciata di punti superstiti, non un segnale di qualità. Solo a `eps≥1.5` la copertura torna ragionevole, ma lì la qualità è mediocre (silhouette 0.302) o negativa (eps=2.0). **Non usare mai il default `eps=0.5` su tsne in produzione.** Se serve comunque DBSCAN su tsne, `eps=1.5` è il compromesso meno peggio (33% noise, qualità reale non artefatta).

#### Spectral

| n                     | silhouette | Calinski-Harabasz | Davies-Bouldin   |
| --------------------- | ---------- | ----------------- | ---------------- |
| 2                     | 0.413      | 1080              | 0.944 (peggiore) |
| 3                     | 0.352      | 797               | 0.873            |
| **4 (default)** | 0.390      | 1018              | 0.859            |
| **5**           | 0.398      | 1091              | 0.830            |
| 6                     | 0.362      | 979               | 0.828            |
| 8                     | 0.351      | 1004              | 0.850            |
| 10                    | 0.357      | 1064              | 0.816            |
| 11                    | 0.370      | 1145              | 0.782            |
| 12                    | 0.375      | 1167              | 0.779            |
| 13                    | 0.369      | 1186              | 0.782            |
| 14                    | 0.370      | **1217**    | **0.772**  |
| 15                    | 0.364      | 1207              | 0.770            |

n=5 offre il miglior compromesso tra i valori originali: secondo miglior silhouette (0.398, dietro solo a n=2 0.413 che però ha il peggior Davies-Bouldin), Calinski-Harabasz alto.

**Round di tuning aggiuntivo (griglia estesa a 15, per verificare l'eigengap)**: l'eigengap suggeriva n≈12 come numero naturale di cluster. Rilanciato il tuning con griglia estesa a 15 (`results/lesion/dim_reduction_clustering/tsne/spectral/tuning/26-07_s1.1_p30`): **stesso esito di umap, l'indicazione non regge**. A n=12 il silhouette è 0.375, inferiore al picco n=5 (0.398); Davies-Bouldin migliora leggermente rispetto a n=5 (0.779 vs 0.830) ma il guadagno è marginale e non compensa il calo di silhouette. Calinski-Harabasz continua a crescere con n, come atteso, non un segnale di qualità autonomo. **Conclusione: n=5 resta la scelta migliore** — la griglia estesa non produce un candidato che superi nettamente n=5 su più indici insieme.

---

### PCA (150 componenti)

⚠️ **Attenzione generale**: il clustering diretto sui 150 componenti PCA è sistematicamente più debole delle altre riduzioni (curse of dimensionality per metodi basati su distanza/densità) — anche i "vincitori" quantitativi qui sotto restano deboli in assoluto.

#### KMeans

| k                     | silhouette      | Calinski-Harabasz | Davies-Bouldin  |
| --------------------- | --------------- | ----------------- | --------------- |
| **2**           | **0.436** | **166**     | **1.907** |
| 3                     | 0.365           | 100               | 2.083           |
| **4 (default)** | 0.397           | 138               | 1.954           |
| 5                     | 0.396           | 120               | 2.239           |
| 6                     | 0.397           | 103               | 2.265           |
| 8                     | 0.336           | 89                | 2.121           |
| 10                    | 0.273           | 74                | 2.133           |

k=2 vince **tutti e tre** gli indici in modo netto e senza ambiguità — raro in questo studio. **Raccomandazione: k=2.** Nota: anche il valore migliore (silhouette 0.436) resta comunque inferiore al peggior risultato ottenuto su umap/pacmap.

#### Agglomerative — ⚠️ cluster fortemente sbilanciati

| k                     | silhouette      | Calinski-Harabasz | Davies-Bouldin  |
| --------------------- | --------------- | ----------------- | --------------- |
| **2**           | **0.443** | **155**     | **1.874** |
| 3                     | 0.322           | 141               | 2.195           |
| **4 (default)** | 0.329           | 118               | 2.265           |
| 5                     | 0.298           | 102               | 2.092           |
| 6                     | 0.303           | 92                | 2.385           |
| 8                     | 0.313           | 80                | 2.119           |
| 10                    | 0.268           | 73                | 2.153           |

k=2 vince tutti e tre gli indici, ma il **dendrogramma rivela un problema più serio**: uno dei rami troncati contiene da solo **563 dei 1150 soggetti** (quasi metà dell'intera coorte in un'unica foglia), con gli altri rami molto più piccoli e sbilanciati. Non è una struttura clinicamente interpretabile in sottogruppi bilanciati, ma un blob dominante indifferenziato più piccole code — sintomo diretto della debolezza generale del clustering su PCA grezzo. **Da usare con cautela anche scegliendo k=2.**

#### GMM — unico metodo dove il default è già ottimale

| n                     | silhouette      | Calinski-Harabasz | Davies-Bouldin   | BIC    | AIC    |
| --------------------- | --------------- | ----------------- | ---------------- | ------ | ------ |
| 2                     | 0.058 (pessimo) | 81                | 3.020 (peggiore) | 595468 | 479623 |
| 3                     | 0.365           | 100               | 2.083            | 829087 | 655316 |
| **4 (default)** | **0.397** | **138**     | **1.954**  | 732674 | 500978 |
| 5                     | 0.396           | 120               | 2.239            | 704060 | 414439 |
| 6                     | 0.397           | 103               | 2.265            | 715363 | 367816 |
| 8                     | 0.336           | 89                | 2.121            | 772135 | 308738 |
| 10                    | 0.273           | 74                | 2.133            | 880956 | 301708 |

A differenza di kmeans/agglomerative, per GMM **n=2 è la scelta peggiore** (silhouette 0.058, quasi casuale) — forzare 2 gaussiane su questi dati produce componenti sovrapposte invece della stessa partizione semplice che trova kmeans. n=4 vince silhouette, Davies-Bouldin e Calinski-Harabasz. BIC/AIC instabili e non monotoni (sintomo di fit instabile in 150 dimensioni), non utilizzabili per la scelta. **Nessun cambiamento consigliato: n=4 è già la scelta migliore.**

#### DBSCAN — inutilizzabile

| eps                     | silhouette        | noise           |
| ----------------------- | ----------------- | --------------- |
| 0.3-0.7                 | degenerato (NaN)  | 96-97%          |
| **0.5 (default)** | degenerato        | **96.7%** |
| 1.0                     | 0.782 (artefatto) | 94.3%           |
| 2.0                     | 0.395             | 91.0%           |

**Ogni singolo valore di `eps` testato produce oltre il 90% di rumore.** Il silhouette "buono" a eps=1.0 (0.782) è calcolato su appena ~65 soggetti superstiti (5.7% della coorte) — non un risultato reale. DBSCAN è strutturalmente inadatto ai 150 componenti PCA grezzi (le distanze diventano quasi uniformi in alta dimensione, tipico della curse of dimensionality). **Da evitare del tutto su PCA**, indipendentemente dal valore di eps.

#### Spectral — nessuna struttura reale

| n                     | silhouette | Calinski-Harabasz | Davies-Bouldin |
| --------------------- | ---------- | ----------------- | -------------- |
| 2                     | 0.083      | 88                | 2.944          |
| 3                     | 0.131      | 93                | 2.464          |
| 4                     | 0.062      | 76                | 2.422          |
| **5 (default)** | 0.081      | 76                | 2.255          |
| 6                     | 0.049      | 73                | 2.291          |
| 8                     | -0.041     | 64                | 2.480          |
| 10                    | -0.054     | 53                | 2.597          |

Tutti i valori di silhouette sono vicini a zero (0.05-0.13) o negativi — un ordine di grandezza più debole di qualunque altra combinazione riduzione×metodo in questo studio. Eigengap: salto più grande dopo il 2° autovalore (suggerisce n=2), ma dato il livello di rumore generale questa indicazione va presa con grande scetticismo. **Spectral non trova struttura reale su PCA — qualunque n si scelga, il risultato non è affidabile.**

---

### PCA a 2 componenti — test di controllo

**Perché**: la sezione precedente (PCA a 150 componenti) mostrava un clustering sistematicamente debole/inutilizzabile. Prima di concludere che "PCA non funziona sui voxel di lesione", va isolata la variabile confusa: 150 componenti è un confronto non alla pari con gli altri 3 metodi, tutti usati a 2D — il fallimento poteva essere *curse of dimensionality* (qualunque metodo di clustering soffre in 150D) più che un limite di PCA come riduzione. Test: stessa pipeline, `pca.params.n_components` temporaneamente impostato a 2 nel registry, tuning rilanciato su tutti e 5 i metodi (`results/lesion/dim_reduction_clustering/pca/<metodo>/tuning/26-07_s1.1_c2/`), poi registry ripristinato a 150 (usato in produzione).

**Risultato: l'ipotesi è confermata — non era PCA, era la dimensionalità.**

| Metodo        | Silhouette max (150D)            | Silhouette max (2D)           | Miglioramento                                    |
| ------------- | -------------------------------- | ----------------------------- | ------------------------------------------------ |
| kmeans        | 0.436 (k=2)                      | **0.695 (k=3)**         | +59%, supera anche umap (0.497) e pacmap (0.506) |
| agglomerative | 0.443 (k=2)                      | **0.696 (k=3)**         | +57%, stesso pattern                             |
| gmm           | 0.397 (n=4)                      | 0.298 (n=2)                   | peggiora leggermente — unico caso               |
| dbscan        | 0.782 su 5.7% coorte (artefatto) | 0.507 su 95% coorte (eps=2.0) | da artefatto a risultato reale e utilizzabile    |
| spectral      | 0.131 (n=3, rumore)              | 0.415 (n=3)                   | +217%, ora un segnale reale                      |

#### KMeans (pca-2D)

| k           | silhouette      | Calinski-Harabasz | Davies-Bouldin  |
| ----------- | --------------- | ----------------- | --------------- |
| 2           | 0.655           | 819               | 0.627           |
| **3** | **0.695** | 1612              | **0.521** |
| 4           | 0.678           | 1656              | 0.521           |
| 5           | 0.673           | 2205              | 0.518           |
| 6           | 0.664           | 2189              | 0.517           |
| 8           | 0.604           | 2906              | 0.525           |
| 10          | 0.628           | 3661              | 0.489           |

Gomito netto sia sul silhouette (picco a k=3, poi calo regolare) sia sul Davies-Bouldin (crollo da 0.627 a k=2 → 0.521 a k=3, poi piatto) — i due indici concordano senza ambiguità. **k=3 è la scelta più pulita di tutto lo studio**, nessuna tensione tra indici.

#### Agglomerative (pca-2D)

Stesso pattern di kmeans: silhouette massimo a k=3 (0.696), Davies-Bouldin minimo condiviso tra k=5/k=6 (~0.51, ma k=3 è vicinissimo a 0.531). Dendrogramma: split a 3 rami più bilanciati che a 150D (il ramo più grande ora copre 311/1150 soggetti, 27% — ancora sbilanciato ma molto meno del 49% visto a 150D). **Raccomandazione: k=3**, coerente con kmeans.

#### GMM (pca-2D) — l'unico che non migliora

| n           | silhouette      | Davies-Bouldin | BIC   | AIC   |
| ----------- | --------------- | -------------- | ----- | ----- |
| **2** | **0.298** | 1.299          | 13932 | 13876 |
| 3           | 0.137           | 1.044          | 12500 | 12415 |
| 4           | 0.083           | 0.990          | 11835 | 11719 |
| 8           | 0.180           | 0.972          | 11233 | 10996 |

Silhouette molto più basso di kmeans/agglomerative sullo stesso embedding (0.30 contro 0.70) — le gaussiane probabilistiche non si adattano bene alla stessa struttura che kmeans/agglomerative separano nettamente, segno che i cluster non sono ellissoidi ben separati ma probabilmente allungati/non-gaussiani (coerente con un asse dominato dal volume lesionale, continuo più che a gruppi). BIC/AIC monotoni, non informativi come al solito. **n=2 resta la scelta meno peggio per GMM**, ma il metodo non è quello consigliato su questo embedding — preferire kmeans/agglomerative.

#### DBSCAN (pca-2D) — da artefatto a risultato reale

| eps           | silhouette      | noise          |
| ------------- | --------------- | -------------- |
| 0.3           | 0.399           | 48.3%          |
| 0.5           | -0.106          | 33.1%          |
| 0.7           | 0.001           | 23.3%          |
| 1.0           | 0.471           | 13.6%          |
| 1.5           | 0.489           | 8.0%           |
| **2.0** | **0.507** | **4.7%** |

A differenza dei 150D (>90% noise ovunque), qui la copertura è ragionevole a `eps≥1.0` con qualità crescente fino a `eps=2.0` (miglior silhouette *e* minor noise contemporaneamente — nessun trade-off qui, a differenza di pacmap). **Raccomandazione: eps=2.0**, il migliore su entrambi i fronti.

#### Spectral (pca-2D)

| n           | silhouette      | Davies-Bouldin |
| ----------- | --------------- | -------------- |
| 2           | 0.266           | 1.349          |
| **3** | **0.415** | 0.813          |
| 4           | 0.316           | 0.788          |
| 10          | 0.404           | 0.611          |

n=3 vince il silhouette, n=10 il Davies-Bouldin — tensione simile ad altri casi, ma entrambi i valori sono comunque un netto miglioramento rispetto al rumore quasi puro visto a 150D. **Raccomandazione: n=3**, coerente con kmeans/agglomerative.

#### ⚠️ Caveat prima di usarlo in produzione

Il miglioramento è reale ma **va interpretato con cautela prima di trattarlo come "il miglior embedding dello studio"**: le prime 2 componenti PCA sono per costruzione le direzioni di massima varianza nei voxel lesionati. Su maschere binarie di lesione, la varianza è quasi certamente dominata dal **volume della lesione** (lesioni grandi vs piccole correlano su moltissimi voxel contemporaneamente) più che dalla sua **posizione/topografia** — che è invece il segnale che umap/tsne/pacmap, essendo neighbor-embedding, sono costruiti per preservare (vedi [docs/methods/dimensionality_reduction_methods.md](../../docs/methods/dimensionality_reduction_methods.md)).

**Verifica eseguita — ipotesi confermata**: calcolato il volume lesionale per soggetto (somma dei voxel lesionati nella matrice binaria, `data/derived/lesion_matrix/21-07_s1.1/matrix.npy`) e correlato con PC1/PC2.

| Componente    | Varianza spiegata | Pearson r vs volume             | Spearman ρ vs volume |
| ------------- | ----------------- | ------------------------------- | --------------------- |
| PC1           | 14.0%             | 0.14 (debole)                   | -0.06                 |
| **PC2** | 8.9%              | **0.92** (quasi perfetta) | **0.87**        |

`PC2` è quasi un doppione lineare del volume lesionale (r=0.92). Prova diretta sul clustering: kmeans k=3 sull'embedding pca-2D, volume per cluster:

| Cluster | N (%)     | Volume mediano (voxel) | Range           |
| ------- | --------- | ---------------------- | --------------- |
| 0       | 870 (76%) | 1114                   | 1 – 16.885     |
| 1       | 128 (11%) | 10.778                 | 4.875 – 37.187 |
| 2       | 152 (13%) | 8.627                  | 4.145 – 41.646 |

Il cluster 0 (lesioni piccole) è separato dagli altri due quasi solo per dimensione (mediana ~10x più piccola) — il silhouette=0.695, il più alto di tutto lo studio, riflette in larga parte **"lesioni piccole vs lesioni grandi"**, non una separazione per topografia.

**Conclusione**: pca-2D non va scartato in automatico (distinguere lesioni piccole/grandi può avere rilevanza clinica), ma **non è un sostituto valido di umap/pacmap** per l'obiettivo del progetto (sottotipi topografici) — il segnale principale che cattura è ridondante con una semplice covariata di volume lesionale, molto più economica da calcolare di un intero embedding+clustering. Se si vuole isolare la componente topografica pura, andrebbe testato un PCA-2D calcolato dopo aver normalizzato/regressato via il volume lesionale (non fatto in questa sessione).

---

### Conclusioni

Tabella riassuntiva finale, dopo tutti i round di tuning (originale + griglia spectral estesa + test di controllo pca-2D):

| Riduzione                            | kmeans                                | agglomerative                       | gmm                         | dbscan                                                          | spectral                                 |
| ------------------------------------ | ------------------------------------- | ----------------------------------- | --------------------------- | --------------------------------------------------------------- | ---------------------------------------- |
| **umap**                       | k=4 (confermato)                      | k=5                                 | n=4 (confermato)            | ❌ nessuno affidabile                                           | **n=8** (confermato, Alta)         |
| **pacmap**                     | k=6 (o k=2 per split macro)           | k=5 (metriche) / k=2 (dendrogramma) | n=6 (o n=2 per split macro) | trade-off eps=0.3 (qualità) vs eps=0.5/0.7 (copertura)         | escluso di proposito (fonde i satelliti) |
| **tsne**                       | k=5                                   | k=2                                 | n=2                         | ⚠️ evitare default eps=0.5 (98.9% noise); eps=1.5 meno peggio | **n=5** (confermato, Alta)         |
| **pca (150 comp.)**            | k=2 (debole)                          | k=2 ⚠️ sbilanciato (563/1150)     | n=4 (confermato)            | ❌ da evitare (>90% noise)                                      | ❌ nessuna struttura                     |
| **pca-2D** (test di controllo) | k=3 ⚠️ confonde col volume (r=0.92) | k=3 ⚠️ stesso confondimento       | n=2 debole                  | eps=2.0 ⚠️ stesso confondimento                               | n=3 ⚠️ stesso confondimento            |

**Decisione presa** (su questo input, `data/derived/lesion_matrix/21-07_s1.1`, matrice voxel-wise): **PCA non viene portato avanti come riduzione**, né a 150 componenti (curse of dimensionality: struttura sistematicamente debole, dbscan/spectral inutilizzabili) né a 2 componenti (il segnale che cattura è ridondante col volume lesionale, non con la topografia — vedi sezione dedicata). Le altre 3 riduzioni (**umap**, **pacmap**, **tsne**) restano tutte valide, con i valori sopra.

**Aperto**: comportamento di **dbscan** ancora da capire a fondo — fallisce su umap/tsne/pca (nessuna struttura o quasi tutto rumore) e su pacmap ha un trade-off netto qualità/copertura mai risolto. Non è chiaro se sia un limite del metodo su questi embedding o se manchi ancora il valore di `eps` giusto — da riprendere prima di usarlo in produzione su una qualunque riduzione.

Le scelte operative conseguenti (quali valori usare per una run di produzione) sono tracciate separatamente in [`RUNNING_STRATEGIES.md`](RUNNING_STRATEGIES.md).

---

### Note metodologiche

- Tutti gli indici sono calcolati con `src/analysis/clustering_tuning.py::compute_clustering_metrics`; per DBSCAN i punti di rumore (`label -1`) sono esclusi da silhouette/CH/DB, `noise_fraction` è sempre riportato a parte.
- Dendrogrammi/eigengap/k-distance sono diagnostiche **standalone**, calcolate una sola volta dai `base_params` — non dipendono dal valore di k/eps scelto nella sweep.
- Nessun valore riportato qui è stato applicato in produzione durante questa sessione — i risultati di produzione su disco per tutte e 4 le riduzioni usano ancora i default del registry.
- Dati sorgente completi: `results/lesion/dim_reduction_clustering/<riduzione>/<metodo>/tuning/*/tuning_results.csv` + plot nella stessa cartella.
- Griglia `spectral` (`config/registry/params_clustering.json`) estesa da `[2,3,4,5,6,8,10]` a `[...,11,12,13,14,15]` per verificare l'indicazione dell'eigengap su umap/tsne (vedi sezioni dedicate) — resta così nel registry, non impatta la produzione (usata solo in `fine_tuning: true`).
