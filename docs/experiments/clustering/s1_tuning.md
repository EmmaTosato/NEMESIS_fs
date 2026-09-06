# Diario Esperimenti

**Pipeline:** Clustering (Tuning)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Vedi data_sessions.md per specifica sulle sessioni

---

## 31-08-2026 — s1.1-vol

### Tuning su coorte originale - 5 metodi SOTA

##### Input
- s1.1-vol
- Embedding:
    - UMAP
    - 6 combinazioni (`dice`/`euclidean` × `n_components`∈{2,3,10})
- Path Embedding:
    - `11-08_s1.1-vol_m_dice_nc2`
    - `11-08_s1.1-vol_m_euclidean_nc2`
    - `13-08_s1.1-vol_m_dice_nc3`
    - `13-08_s1.1-vol_m_euclidean_nc3`
    - `11-08_s1.1-vol_m_dice_nc10`
    - `11-08_s1.1-vol_m_euclidean_nc10`
- Dati originali: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
Agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Sweep `n_clusters` × `linkage` × `metric` per agglomerative su tutti e 6 gli embedding UMAP di produzione
- Verificare se un `k` di produzione emerge in modo robusto, e se è indipendente da confondenti noti (`lesion_side`, `dataset`, volume)

##### Risultati

| Metodo | Run | Griglia | Link |
| --- | --- | --- | --- |
| Agglomerative | 6×70 | `n_clusters`∈{2,3,4,5,6,8,10} × `linkage`∈{ward,average,complete,single} × `metric`∈{euclidean,cosine,manhattan} | [tuning/agglomerative/](../../../results/lesion/clustering/tuning/agglomerative/) |
| GMM | 6×28 | `n_components`∈{2,3,4,5,6,8,10} × `covariance_type`∈{full,tied,diag,spherical} | [tuning/gmm/](../../../results/lesion/clustering/tuning/gmm/) |
| KMeans | 6×7 | `n_clusters`∈{2,3,4,5,6,8,10} | [tuning/kmeans/](../../../results/lesion/clustering/tuning/kmeans/) |
| HDBSCAN | 6×18 | `min_cluster_size`∈{5,10,15,20,30,50} × `min_samples`∈{5,10,20} | [tuning/hdbscan/](../../../results/lesion/clustering/tuning/hdbscan/) |
| Spectral | 6×72 | `n_clusters`∈{2..15} × `affinity`∈{nearest_neighbors,rbf} (`n_neighbors`∈{10,30,50} / `gamma`∈{0.1,1,5}) | [tuning/spectral/](../../../results/lesion/clustering/tuning/spectral/) |

**Agglomerative**

| Check | Esito |
| --- | --- |
| k=2 | Artefatto `lesion_side`, su tutti e 6 gli embedding |
| Interclass matrix (proxy `dataset`) | Piatta su `euclidean` — nessuna metrica separa i siti. Eccezione: PSP ~12% più compatto internamente |
| Dendrogramma (`euclidean_n2`) | `single` scartato (chaining); `ward`/`average` concordano solo al primo taglio (k=2) |
| k migliore oltre k=2 (`ward`/`average`, `euclidean`) | **Non converge tra `n_components`** — vedi tabella sotto |
| `dataset` nei k candidati | Non confondente, ben distribuito |
| `average` vs `ward` a k=5 fisso (`n3`) | ARI 0.68 / NMI 0.81 — accordo parziale, entrambi stabili (SSI 1.00 / 0.96) |

| `n_components` | k migliore | Silhouette (average / ward) |
| --- | --- | --- |
| 2 | 5 | 0.497 / 0.485 |
| 3 | 3 | 0.481 / 0.482 |
| 10 | 4 | 0.444 / 0.444 |

Struttura ricorrente in ogni k candidato: 1-2 cluster quasi puri per lato lesione + volume, 1 cluster misto a basso volume.

**GMM**

| Check | Esito |
| --- | --- |
| Stabilità init (`kmeans` vs `random`) | Entrambe piatte da subito (nessuna instabilità di seed) — ma `kmeans` domina sempre in BIC, gap crescente con `n_components`. `random` da scartare |
| BIC/AIC | Monotoni decrescenti su tutta la griglia, nessun gomito — non informativi qui, ignorati come criterio |
| Davies-Bouldin | Buono ovunque tranne un outlier netto: `full`@`n_components`=10 (~1.7 vs ~0.7-0.9) — fit degenere nonostante il BIC più basso in assoluto |
| Miglior candidato (Silhouette) | `full`, `n_components`=4 (silhouette 0.496, DB 0.693 — coerente, non l'anomalia di nc=10) |
| Crosstab (`full`, `n_components`=4) vs `lesion_side` | Stesso artefatto di agglomerative: 2 cluster puri per lato lesione (left/right) + 2 misti |

**KMeans**

| Check | Esito |
| --- | --- |
| Stabilità init (`k-means++` vs `random`) | Entrambe convergono alla stessa inertia già a `n_init`≥5, a ogni `n_clusters` — nessun vincitore netto, nessuna instabilità |
| Silhouette / Davies-Bouldin | Concordano esattamente: picco Silhouette e minimo Davies-Bouldin entrambi a **k=4** (0.497 / 0.693) |
| Calinski-Harabasz / inertia | CH cresce quasi sempre con k (non decisivo, ma non contraddice k=4); inertia senza gomito netto, coerente con k=4-5 |
| Crosstab `lesion_side`, k=4 (miglior candidato) | Stesso artefatto: cluster puro left (215/0/49), cluster puro right (1/243/41), 2 cluster misti a maggioranza left |
| Crosstab `lesion_side`, k=5 | Stesso pattern, un cluster misto in più (3 quasi-puri per lato + 2 misti) |

**HDBSCAN**

| Check | Esito |
| --- | --- |
| Silhouette/CH più alti (`min_cluster_size=5, min_samples=5`) | **Trappola**: silhouette=0.609, CH=4321 (outlier), ma `noise_fraction`=0.245 — il rumore più alto di tutta la sweep, scarta i soggetti difficili invece di separarli |
| Filtro `noise_fraction`≤0.1 | Solo 2 combinazioni sopravvivono. Vero candidato: `min_cluster_size=20, min_samples=10` (silhouette 0.475, noise 0.083, il più basso della sweep) |
| Sopra `min_samples`, `min_cluster_size` extra non cambia nulla | Coppie con valori identici (es. `(30,20)`≡`(50,20)`, `(30,10)`≡`(50,10)`) — il vincolo attivo è `min_samples` |
| Crosstab `lesion_side`, `(20,10)` | 7 cluster su 8 quasi puri per lato; 1 misto (left=176/right=114/unknown=56) ma **è il cluster più grande** (346 soggetti) — a differenza degli altri metodi, dove il misto è il più piccolo |
| Rumore (`-1`) | Composizione non stabile tra combinazioni: sbilanciato `right` a `(15,10)`, `left` a `(20,10)` — da non sovra-interpretare |

**Spectral**

| Check | Esito |
| --- | --- |
| Silhouette per combinazione | `nearest_neighbors(n_neighbors=10)` instabile/erratico (silhouette giù fino a 0.10-0.15) — grafo da scartare. Le altre convergono in una fascia 0.40-0.50, picco a `n_clusters`=4-8 |
| Miglior candidato (Silhouette) | `rbf`, `n_clusters`=8 (0.502) — alternativa con DB migliore: `nearest_neighbors(n_neighbors=30)`, `n_clusters`=5 (silhouette 0.494, DB 0.628, il più basso della tabella) |
| Eigengap vs Silhouette | **Disaccordo netto**: eigengap suggerisce `n_clusters`≈10-14 (10 per `n_neighbors`=30, 11 per 50, 14 per 10) contro il picco Silhouette 4-8 — nessuna regola meccanica per risolverlo |
| Crosstab (`n_clusters=6, nearest_neighbors, n_neighbors=50`) vs `lesion_side` | 5 cluster su 6 quasi puri per lato; 1 misto (392 soggetti) — di nuovo il cluster più grande, come HDBSCAN |

##### Decisioni

- Vedi production del 1 settembre (o la prima successiva nel caso venisse eliminata)

---

## 01-09-2026 — s1.2-vol

### Stesso tuning su coorte estesa (5269 soggetti) - Metodi SOTA

##### Input
- s1.2-vol
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `28-08_s1.2-vol_m_euclidean_nc2`
- Dati originali: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Ripetere il tuning di s1.1-vol sulla coorte estesa, per verificare se i candidati reggono a scala maggiore

##### Risultati

| Metodo | Griglia | Miglior combo (silhouette) | Link |
| --- | --- | --- | --- |
| KMeans | `n_clusters`∈{2,3,4,5,6,8,10} | `k=5` (0.443) | [tuning/kmeans/](../../../results/lesion/clustering/tuning/kmeans/umap/01-09_s1.2-vol_m_euclidean_n2/) |
| Agglomerative | `n_clusters`×`linkage`×`metric` (70/84 valutate, 14 saltate: `ward`+metrica non euclidea) | `k=2, average, cosine` (0.761) | [tuning/agglomerative/](../../../results/lesion/clustering/tuning/agglomerative/umap/01-09_s1.2-vol_m_euclidean_n2/) |
| GMM | `n_components`×`covariance_type` | `n_components=5, full` (0.447) | [tuning/gmm/](../../../results/lesion/clustering/tuning/gmm/umap/01-09_s1.2-vol_m_euclidean_n2/) |
| HDBSCAN | `min_cluster_size`×`min_samples` | `mcs=5, ms=10` (0.613, noise 0.32) | [tuning/hdbscan/](../../../results/lesion/clustering/tuning/hdbscan/umap/01-09_s1.2-vol_m_euclidean_n2/) |
| Spectral | `n_clusters`×`affinity` (`n_neighbors`/`gamma`) | `rbf, k=5, gamma=1.0` (0.426) | [tuning/spectral/](../../../results/lesion/clustering/tuning/spectral/umap/01-09_s1.2-vol_m_euclidean_n2/) |

- `k=2` di agglomerative è quasi certamente lo stesso artefatto `lesion_side` visto in s1.1-vol (silhouette anomalo, come il k=2 già scartato lì).
- Miglior silhouette assoluto di HDBSCAN arriva con `noise_fraction`=0.32 (quasi 1/3 scartato come rumore) — combinazioni a noise più basso (`mcs=30, ms=5`: noise 0.14) scendono a silhouette 0.34, stesso trade-off già visto in s1.1-vol.
- **Gap scoperto in produzione** (vedi `s1_production.md`, 03-09-2026): questo tuning non riportava il numero di cluster trovati da HDBSCAN — solo silhouette/CH/DB/noise_fraction. `mcs=5, ms=10` (il candidato scelto per la produzione, opzione E) è risultato avere **143 cluster** (+1706 noise), invisibile qui. Corretto sotto (`n_clusters_found` aggiunto a `METHOD_METRIC_COLUMNS["hdbscan"]`, `src/analysis/clustering_tuning.py`).

---

## 03-09-2026 — s1.2-vol (re-tuning HDBSCAN)

### Stesso tuning, colonna `n_clusters_found` aggiunta + griglia `min_cluster_size` alzata

##### Input
- Stesso embedding di sopra (`28-08_s1.2-vol_m_euclidean_nc2`, 5269 soggetti)
##### Motivazione
- `n_clusters_found` non era mai stato calcolato per HDBSCAN durante il tuning (solo in produzione, via `len(np.unique(labels))`) — la scelta dei candidati era alla cieca sul numero di cluster risultante
- `min_cluster_size` alzato da `[5,10,15,20,30,50]` a `[10,20,30,50,75,100]`: `mcs=5` (non più nella griglia) aveva già mostrato in produzione 143 cluster su questa coorte, chiaramente troppo fine

##### Risultati

| `min_cluster_size` | `min_samples` | Silhouette | Noise | `n_clusters_found` |
| --- | --- | --- | --- | --- |
| 10 | 5 | 0.561 | 0.226 | 149 |
| 10 | 10 | 0.612 | 0.308 | 121 |
| 10 | 20 | 0.385 | 0.247 | 57 |
| 20 | 5 | 0.532 | 0.211 | 93 |
| 20 | 10 | 0.349 | 0.161 | 62 |
| 20 | 20 | 0.404 | 0.228 | 46 |
| 30 | 5 | 0.341 | 0.143 | 53 |
| 30 | 10 | 0.348 | 0.145 | 45 |
| 30 | 20 | 0.398 | 0.214 | 38 |
| 50 | 5 | 0.366 | 0.163 | 34 |
| 50 | 10 | 0.416 | 0.165 | 26 |
| 50 | 20 | 0.417 | 0.195 | 25 |
| 75 | 5 | 0.359 | 0.156 | 18 |
| 75 | 10 | 0.405 | 0.168 | 20 |
| 75 | 20 | **0.449** | 0.231 | 19 |
| 100 | 5 | 0.341 | 0.173 | 13 |
| 100 | 10 | 0.384 | 0.221 | 15 |
| 100 | 20 | **0.464** | 0.245 | 15 |

- Anche `mcs=10` (il valore più basso ora ammesso) produce 121-149 cluster — la frammentazione forte non è specifica di `mcs=5`, serve `mcs`≥50 per scendere sotto i ~30 cluster.
- Candidati più in linea con la granularità scelta in s1.1-vol (8-20 cluster su 1150 soggetti): `mcs=75, ms=20` (19 cluster, silhouette 0.449, noise 0.231) o `mcs=100, ms=20` (15 cluster, silhouette 0.464 — il migliore dell'intera griglia, noise 0.245). `mcs=50, ms=20` (25 cluster, silhouette 0.417, noise più basso 0.195) resta un'alternativa a granularità intermedia.
- I due candidati già lanciati in produzione (opzioni E `mcs=5,ms=10`→143 cluster ed F `mcs=30,ms=5`→53 cluster) erano entrambi più frammentati di queste nuove alternative — **rifatte lo stesso giorno** con `mcs=100,ms=20` (E, 15 cluster) e `mcs=75,ms=20` (F, 19 cluster), vedi `s1_production.md`.

---

## 03-09-2026 — s1.2-vol (agglomerative su matrice raw)

### Clustering diretto sui voxel, senza dimensionality reduction

##### Input
- Dati originali: `data/derived/lesion_matrix/25-08_s1.2-vol` — matrice raw **5269 × 264274 voxel**
- Nessun embedding (`reduced_data: false`, `reduction_method: "raw"`)

##### Metodi
agglomerative

##### Obiettivo
- Verificare se la struttura topografica emerge clusterizzando i voxel nativi, senza la distorsione introdotta da UMAP
- Confrontare una metrica binaria volume-normalizzata (`dice`) contro `euclidean` sullo stesso dato
- Abilitato da `ce4e749`: cache della distanza precomputata per metrica, condivisa tra fit e scoring — senza, lo sweep su questa matrice non era praticabile

##### Risultati

Griglia `n_clusters`∈{2..6} × `linkage`∈{average, complete} × `metric`∈{euclidean, dice} — 20 combinazioni, [tuning/agglomerative/raw/](../../../results/lesion/clustering/tuning/agglomerative/raw/03-09_s1.2-vol/).

**Tutte e 20 le combinazioni sono degeneri**: il cluster maggiore contiene tra il 90.9% e il 100% dei soggetti, il resto sono micro-cluster (spesso singoletti).

| metrica | linkage | silhouette (k=2→6) | partizione a k=6 |
| --- | --- | --- | --- |
| euclidean | average | 0.734 → 0.706 | `[5257, 5, 2, 2, 2, 1]` |
| euclidean | complete | 0.474 → 0.465 | `[4790, 330, 119, 19, 6, 5]` |
| dice | average | ~0.0107 (costante) | `[5264, 1, 1, 1, 1, 1]` |
| dice | complete | 0.006 → −0.028 | `[5118, 75, 23, 22, 19, 12]` |

- **Il silhouette è qui attivamente fuorviante**: il valore più alto dell'intera griglia (0.734) corrisponde alla partizione `[5262, 7]`. È alto perché 5262 punti sono mutuamente vicini *rispetto* a 7 outlier, non perché esista struttura.
- CH/DB sono vuoti per tutte le righe `dice`: sono centroid-based, definiti solo in geometria euclidea, quindi `compute_clustering_metrics_metric_aware` restituisce NaN invece di un numero sbagliato. Il silhouette `dice` è invece calcolato metric-aware sulla matrice di distanza dice, quindi lo 0.0107 è un valore genuino.

##### Diagnosi — due fallimenti opposti

Misurato sulla matrice raw (occupazione media 0.8% dei voxel, volume lesionale mediano 460 su 264274):

- **`euclidean` misura il volume, non la topografia.** `corr(distanza euclidea, somma dei volumi lesionali) = 0.942` — con overlap quasi nullo, √(|A|+|B|−2|A∩B|) ≈ √(|A|+|B|). I 5 cluster di `complete, k=5` sono infatti ordinati monotonicamente per volume mediano (351 → 5852 → 15136 → 20233 → 40274 voxel): è uno stratificatore di volume, non un clustering topografico.
- **`dice` misura la cosa giusta ma non ha segnale globale.** L'**86.1% delle coppie ha distanza esattamente 1.0** (zero voxel in comune), mediana = 1.0. La matrice di distanza è un plateau: a(i) ≈ b(i) ≈ 1 per quasi tutti i punti → silhouette ≈ 0 e costante rispetto a k. Coerentemente i cluster `dice` *non* sono ordinati per volume: dice fa il suo lavoro, semplicemente non c'è gradiente globale da clusterizzare.

##### Conseguenza: perché la dim reduction non è una comodità computazionale

Il segnale di overlap esiste, ma solo **localmente**: il soggetto mediano ha ~778 partner con overlap non nullo su 5268, e solo lo 0.1% non ne ha nessuno.

Agglomerative consuma la matrice di distanza **completa** — tutte le ~13.9M di coppie, di cui l'86% sono pareggi a distanza massima che dominano per numerosità pura. UMAP guarda solo i k vicini di ogni punto: il grafo k-NN seleziona per costruzione la frazione informativa e il plateau non entra mai nel calcolo.

Confronto diretto, stesso metodo/coorte/k=6, cambia solo l'input:

| Input | `average` | `complete` | `ward` |
| --- | --- | --- | --- |
| Raw (264274 voxel) | `[5257, 5, 2, 2, 2, 1]` — 99.8% | `[4790, 330, 119, 19, 6, 5]` — 90.9% | n/d |
| UMAP 2D (`28-08_s1.2-vol_m_euclidean_nc2`) | `[2464, 956, 777, 559, 304, 209]` — 46.8% | `[1043, 957, 954, 866, 825, 624]` — 19.8% | `[1530, 1095, 941, 851, 547, 305]` — 29.0% |

Non è la stessa risposta ottenuta più in fretta: è una partizione inutilizzabile contro una bilanciata. UMAP non comprime informazione esistente — **ricostruisce per transitività una geometria globale che nel dato di partenza non esiste**: nell'embedding due lesioni senza alcun voxel in comune hanno comunque una distanza sensata, mediata da catene di soggetti parzialmente sovrapposti, mentre nello spazio raw quella distanza è 1.0 per tutte e indistinguibile.

Due precisazioni: `single` linkage resta degenere anche sull'embedding (`[5128, 79, 37, 16, 8, 1]`) — è il chaining di single linkage, indipendente dalla rappresentazione; e "non degenere" non significa "biologicamente valido" (il k=2 su embedding resta il sospetto artefatto `lesion_side`).

##### Il punto

- **Chiude un ramo.** La domanda era "serve davvero UMAP, o passandoci attraverso perdiamo qualcosa?". Risposta misurata: no. Il clustering gerarchico diretto sui voxel non è un'alternativa praticabile, per motivi strutturali e non di tuning — non serve tornarci.
- **Dà una difesa metodologica.** "Usiamo la dim reduction prima di clusterizzare" passa da convenzione a scelta giustificata da due numeri (86% di coppie a overlap zero, `corr` = 0.942 tra distanza euclidea e volume). È la risposta pronta a chi chiede perché non si è clusterizzato il dato nativo.
- **Non dà nulla sulle decisioni aperte**: nessun candidato di produzione, nessuna indicazione sul k di s1.1-vol né sull'SDC.

##### Decisione
- Nessun candidato di produzione da questa run.
- Il percorso `reduced_data: false` è **chiuso per agglomerative** su dati lesionali voxel-wise a questa scala.
- La diagnosi è però *metrica-specifica, non metodo-specifica*, e non va estesa alla cieca: qualsiasi metodo che consumi la matrice `dice`/`jaccard` globale incontra lo stesso plateau, e qualsiasi metodo euclideo su binario raw (es. kmeans) stratifica per volume. I metodi a densità locale (hdbscan) non sono coperti da questa run — userebbero solo il vicinato, come UMAP.
