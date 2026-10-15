# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Parametri scelti a valle del tuning ([`s2_tuning.md`](s2_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni
- In ogni `config.md` `params_file` punta a un file temporaneo: i parametri veri sono in `config.md` e `runs.csv`.

---

## 14-10-2026 — s2.4-stream

### Produzione dopo il tuning

##### Input
- s2.4-stream (SDC streamline): matrice grezza `data/derived/sdc_matrix/07-10_s2.4-stream`, 5831 soggetti × 87 tratti, nessun embedding
- Vista 2D solo per i grafici e per Dash: UMAP `14-10_s2.4-stream_m_euclidean_nc2`, creato apposta ([`dim_reduction/s2_production.md`](../dim_reduction/s2_production.md))
##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Produrre i cluster dei candidati del tuning del 12-10 ([`s2_tuning.md`](s2_tuning.md)), ognuno come lettura a una risoluzione diversa

##### Risultati

19 run concluse.

| Metodo | Parametri | Run | Cluster | Link |
| --- | --- | --- | --- | --- |
| agglomerative | `average, cosine`, k = 3, 4, 5, 6, 7, 8, 9 | 7 | k | [runs.csv](../../../results/sdc/clustering/production/agglomerative/runs.csv) |
| hdbscan | 15/10, 30/1, 10/10, 20/5, 15/5, 20/1 | 6 | 8, 9, 11, 11, 14, 18 (rumore 70.9-82.9%) | [runs.csv](../../../results/sdc/clustering/production/hdbscan/runs.csv) |
| adp | `dice`, Z = 2.5, 3.0, 3.5, 4.0, 5.0, 6.0 | 6 | 19, 16, 14, 12, 9, 7 | [runs.csv](../../../results/sdc/clustering/production/adp/runs.csv) |

HDBSCAN: sigla `min_cluster_size/min_samples`. Cartelle: `<dd-mm>_s2.4-stream_<tag>` sotto `production/<metodo>/raw/`.

- Agglomerative k=3: 3013, 2518 e 300 soggetti.
- HDBSCAN lascia fuori il 71-83% dei soggetti: descrive solo il 17-29% della coorte.
- Numero di cluster e rumore coincidono con il tuning in tutte le run.

##### Decisioni
- HDBSCAN prodotto anche senza righe utilizzabili, su richiesta: le 6 righe con 8-20 cluster.
- Il lato lesionale non è trattato: i cluster puri per lato sono attesi (average/cosine k=3 separa sinistre, destre e infratentoriali).
- In questo spazio i cluster ricalcano lato, volume e sede infratentoriale, non una struttura nuova.

---

## 12-10-2026 — s2.4-vol

### Produzione ampia dopo il tuning

##### Input
- s2.4-vol (SDC voxelwise)
- Embedding: UMAP `euclidean`, `n_neighbors=15`, `min_dist=0.0`, n_components∈{2,10}, `08-10_s2.4-vol_m_euclidean_nc{2,10}`
- ADP: matrice grezza `data/derived/sdc_matrix/07-10_s2.4-vol` (5845 × 291345)
- 5845 soggetti
##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Produrre i cluster dei candidati del tuning del 12-10 ([`s2_tuning.md`](s2_tuning.md)), ognuno come lettura a una risoluzione diversa

##### Risultati

25 run concluse.

| Metodo | Parametri | Input | Run | Cluster | Link |
| --- | --- | --- | --- | --- | --- |
| agglomerative | `ward, euclidean`, k = 5, 7, 9, 13, 15, 18 | euclidean nc2 | 6 | k | [runs.csv](../../../results/sdc/clustering/production/agglomerative/runs.csv) |
| agglomerative | `average, euclidean`, k = 3, 6, 7, 8, 10, 13, 14, 15 | euclidean nc10 | 8 | k | stesso |
| hdbscan | 100/10, 75/10, 50/10 | euclidean nc2 | 3 | 14, 16, 20 (rumore 9.1-12.3%) | [runs.csv](../../../results/sdc/clustering/production/hdbscan/runs.csv) |
| hdbscan | 75/5, 75/10, 75/20, 50/10 | euclidean nc10 | 4 | 8, 8, 11, 19 (rumore 1.4-13.3%) | stesso |
| adp | `dice`, Z = 2.0, 2.5, 3.0, 3.5 | matrice grezza | 4 | 16, 9, 7, 7 | [runs.csv](../../../results/sdc/clustering/production/adp/runs.csv) |

HDBSCAN: sigla `min_cluster_size/min_samples`.

- Il k nel nome e il numero di cluster coincidono con il tuning in tutte le run; Z=3.0 ha 2705, 2321, 195, 188, 166, 142 e 128 soggetti.
- Le 12 run su nc10 e le 4 ADP sono disegnate sul gemello 2D `08-10_s2.4-vol_m_euclidean_nc2` (stessi parametri tranne `n_components`).

##### Decisioni
- HDBSCAN prodotto con 8-20 cluster (7 run) pur senza righe utilizzabili, per coerenza con s1.4: vanno lette come descrizioni, non come struttura.
- ADP solo con `dice`. Z=3.5 incluso anche se dà la stessa partizione di Z=3.0, per coerenza con s1.4.
- Il lato lesionale non è trattato: i cluster puri per lato sono attesi.
- Ogni run ADP dura circa 48 minuti e copia `matrix.npy` (6.3 GB): `production/adp` pesa 25 GB.

---

## 10-09-2026 — s2.2-vol

### 5 opzioni di k in esplorazione

##### Input
- s2.2-vol
- Embedding: UMAP `euclidean`, n_components=2, `07-09_s2.2-vol_m_euclidean_nc2`
- Dati raw: `data/derived/sdc_matrix/07-09_s2.2-vol`
- 1570 soggetti
##### Metodi
agglomerative, gmm, kmeans, spectral, hdbscan

##### Obiettivo
- Stesso sweep di s1.1-vol/s1.2-vol (k=2..6 in parallelo su 4 metodi). Il tuning ([`s2_tuning.md`](s2_tuning.md)) mostra che ogni metodo converge sul taglio emisfero
- A/B (k=2/3) estendono lo sweep verso il basso, dove il massimo del tuning cade qui; C/D/E (k=4/5/6) sono gli stessi k delle lesioni
- F: spectral a `gamma=5.0`, k=8. G/H: HDBSCAN fine e grossolano

##### Risultati

| Opzione | Metodi e parametri | Cluster | Purezza per emisfero *[1]* |
| --- | --- | --- | --- |
| A (k2) | agglomerative `average, cosine`; kmeans; gmm `spherical`; spectral `rbf, gamma=1.0` | 2 | 0.71–0.86 |
| B (k3) | agglomerative `average, cosine`; kmeans; gmm `diag`; spectral `rbf, gamma=1.0` | 3 | 0.66–0.86 |
| C (k4) | agglomerative `average, cosine`; kmeans; gmm `diag`; spectral `rbf, gamma=0.1` | 4 | 0.55–0.90 |
| D (k5) | agglomerative `average, cosine`; kmeans; gmm `tied`; spectral `rbf, gamma=0.1` | 5 | 0.51–0.90 |
| E (k6) | agglomerative `average, cosine`; kmeans; gmm `spherical`; spectral `rbf, gamma=1.0` | 6 | 0.42–0.91 |
| F (solo spectral) | spectral `rbf, gamma=5.0` | 8 | 0.56–0.91 |
| G | hdbscan `min_cluster_size=10, min_samples=10` | 42 (+369 rumore) | 0.40–1.0 |
| H | hdbscan `min_cluster_size=100, min_samples=10` | 5 (+189 rumore) | 0.50–0.91 |

*[1] Frazione di ogni cluster occupata dalla categoria `lesion_side` più frequente: intervallo sui cluster dell'opzione e sui metodi.*

Output: `results/sdc/clustering/production/<metodo>/umap/10-09_s2.2-vol_m_euclidean_nc2_*` ([cartella](../../../results/sdc/clustering/production/)).

- Ogni opzione resta dominata dal lato: la purezza non scende sotto 0.40 e nella maggior parte dei cluster supera 0.80.
- Agglomerative non è monotono in k: silhouette 0.80 (k=2), 0.745 (k=4), 0.761 (k=6). La purezza resta nella stessa fascia, quindi non è una struttura diversa.
- G ha purezza > 0.9 in 30 cluster su 42, ma scarta 369 soggetti (23.5%).
- Nessuna opzione produce un cluster misto per emisfero grande quanto i puri, a differenza delle lesioni.

##### Decisioni
- Nessun k unico: le granularità A-H restano aperte.
- Diversamente dalle lesioni, nessuna granularità sfugge alla lateralizzazione: a qualunque risoluzione la struttura trovabile è l'emisfero. Chi usa queste run deve saperlo prima di leggere un cluster come sottotipo clinico.
