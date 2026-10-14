# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Parametri scelti a valle del tuning ([`s2_tuning.md`](s2_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

_s2.1-schaefer-200-tian-s2 è ferma al tuning (vedi `s2_tuning.md`), in attesa di estendere l'analisi a `nc3` e di decidere la config di produzione. s2.2-vol ha la sua prima run di produzione qui sotto. Struttura entry da usare per le prossime:_

```
## DD-MM-YYYY — sX.X

### <titolo>

##### Input
- sX.X
- Embedding: <metodo, parametri>
- Path Embedding: <cartella `input_path` in `dim_reduction/production/`, es. `31-08_s2.1-schaefer-200-tian-s2_m_euclidean_nc2` — NON la cartella di output di clustering stesso>
- Dati originali: data/derived/sdc_matrix/<...>
- N soggetti
##### Metodi
<metodo scelto>

##### Obiettivo
- ...

##### Risultati

<tabella o descrizione>

##### Decisioni

- ...
```

---

## 14-10-2026 — s2.4-stream

### Produzione dopo il tuning: k buoni e discreti, HDBSCAN meno peggio con 8-20 cluster

##### Input
- s2.4-stream (SDC streamline), matrice grezza 5831 soggetti × 87 tratti, `data/derived/sdc_matrix/07-10_s2.4-stream` (nessun embedding in ingresso)
- Vista 2D (solo per i grafici e per Dash): UMAP `14-10_s2.4-stream_m_euclidean_nc2`, creato apposta ([`dim_reduction/s2_production.md`](../dim_reduction/s2_production.md))
- Parametri scelti dal tuning del 12-10-2026 ([`s2_tuning.md`](s2_tuning.md)); stesso criterio "buono + discreto" di [`s1_production.md`](s1_production.md)

##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Produrre i cluster dei candidati "buoni" e "discreti" del tuning, ognuno come lettura a una risoluzione diversa

##### Risultati

19 run, tutte concluse; righe di `runs.csv` e cartelle di output coincidono (7 + 6 + 6, nessun duplicato).

| Metodo | Parametri | Run | Cluster | Link |
| --- | --- | --- | --- | --- |
| agglomerative | `linkage=average, metric=cosine`, k = 3, 4, 5, 6, 7, 8, 9 | 7 | k | [runs.csv](../../../results/sdc/clustering/production/agglomerative/runs.csv) |
| hdbscan | 15/10, 30/1, 10/10, 20/5, 15/5, 20/1 | 6 | 8, 9, 11, 11, 14, 18 (rumore 70.9-82.9%) | [runs.csv](../../../results/sdc/clustering/production/hdbscan/runs.csv) |
| adp | `metric=dice`, Z = 2.5, 3.0, 3.5, 4.0, 5.0, 6.0 | 6 | 19, 16, 14, 12, 9, 7 | [runs.csv](../../../results/sdc/clustering/production/adp/runs.csv) |

HDBSCAN: sigla `min_cluster_size/min_samples`. Le cartelle di output sono `<dd-mm>_s2.4-stream_<tag>` sotto `production/<metodo>/raw/`.

**Quali sono "buoni" e quali "discreti"** (dal tuning):
- agglomerative: k=3 buono (ARI 0.964, minimo 0.889), k=4-9 parziali. Gli altri linkage non hanno k stabili e non sono stati prodotti
- HDBSCAN: **nessuna riga è usabile**; sono le 6 "meno peggio" con 8-20 cluster, scelte su richiesta. Il 71-83% dei soggetti è rumore, quindi descrivono solo il 17-29% della coorte: nuclei densi di lesioni piccole e code di lesioni molto grandi. I cluster sono stabili (ARI senza rumore 0.92-0.99), non il rumore
- ADP: Z=2.5, 3.0, 3.5 buoni (plateau); Z=4.0, 5.0, 6.0 usabili con 12, 9, 7 cluster, non letti nel report. Stabilità per sottocampionamento non calcolata

**Controlli sulle run:**
- Agglomerative: il k nel nome coincide col numero di cluster; k=3 ha 3013, 2518 e 300 soggetti, come nel report
- HDBSCAN e ADP: numero di cluster e rumore coincidono con la riga di tuning in tutte le 12
- `cluster_plot.png` e `silhouette_plot.png` presenti in tutte le 19, disegnati sull'UMAP 2D creato apposta; tutte si aprono in Dash

##### Decisioni
- HDBSCAN prodotto anche senza righe usabili, su richiesta: le 6 righe con 8-20 cluster, nonostante il rumore
- Il lato lesionale non è stato trattato: l'input è invariato, e i cluster puri per lato sono attesi (average/cosine k=3 separa sinistre, destre e infratentoriali)
- In questo spazio i cluster ricalcano lato, volume e sede infratentoriale (dal report del tuning), non una struttura nuova

##### Note
- La vista 2D non è lo spazio del clustering (87 tratti): l'UMAP euclidean serve solo per disegnare. Come nelle altre sessioni, `params_file` nel `config.md` punta a un file temporaneo; il registro del repo non è stato modificato

---

## 12-10-2026 — s2.4-vol

### Produzione ampia dopo il tuning: k buoni e discreti, righe HDBSCAN usabili con 8-20 cluster

##### Input
- s2.4-vol (SDC voxelwise), 5845 soggetti
- Embedding: UMAP `euclidean`, `n_neighbors=15`, `min_dist=0.0`, n_components 2 e 10, path `08-10_s2.4-vol_m_euclidean_nc{2,10}` in `results/sdc/dim_reduction/production/umap/`
- ADP sulla matrice grezza `data/derived/sdc_matrix/07-10_s2.4-vol` (5845 x 291345)
- Parametri scelti dal tuning del 12-10-2026 ([`s2_tuning.md`](s2_tuning.md)); stesso criterio "buono + discreto" di [`s1_production.md`](s1_production.md)

##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Produrre i cluster di tutti i candidati "buoni" e "discreti" del tuning, ognuno come lettura a una risoluzione diversa
- Un k non stabile resta una partizione valida per descrivere i soggetti, ma non sostiene "esistono N sottotipi"

##### Risultati

25 run, tutte concluse; righe di `runs.csv` e cartelle di output coincidono (14 + 7 + 4, nessun duplicato).

| Metodo | Parametri | Input | Run | Cluster | Link |
| --- | --- | --- | --- | --- | --- |
| agglomerative | `linkage=ward, metric=euclidean`, k = 5, 7, 9, 13, 15, 18 | euclidean nc2 | 6 | k | [runs.csv](../../../results/sdc/clustering/production/agglomerative/runs.csv) |
| agglomerative | `linkage=average, metric=euclidean`, k = 3, 6, 7, 8, 10, 13, 14, 15 | euclidean nc10 | 8 | k | stesso |
| hdbscan | 100/10, 75/10, 50/10 | euclidean nc2 | 3 | 14, 16, 20 (rumore 9.1-12.3%) | [runs.csv](../../../results/sdc/clustering/production/hdbscan/runs.csv) |
| hdbscan | 75/5, 75/10, 75/20, 50/10 | euclidean nc10 | 4 | 8, 8, 11, 19 (rumore 1.4-13.3%) | stesso |
| adp | `metric=dice`, Z = 2.0, 2.5, 3.0, 3.5 | matrice grezza | 4 | 16, 9, 7, 7 | [runs.csv](../../../results/sdc/clustering/production/adp/runs.csv) |

HDBSCAN: sigla `min_cluster_size/min_samples`. Le cartelle di output sono `<dd-mm>_s2.4-vol_<embedding>_<tag>` sotto `production/<metodo>/umap/` (`raw/` per ADP).

**Quali sono "buoni" e quali "discreti"** (dal tuning):
- agglomerative buoni: nc2 k=5 (ward); nc10 k=8, 13, 14, 15 (average). Gli altri k sono discreti
- HDBSCAN: **nessuna riga è buona**. Sono righe "usabili" (3-30 cluster, rumore ≤ 25%, cluster più grande ≤ 60%) con 8-20 cluster, ma l'ARI minimo al sottocampionamento è 0.12-0.30
- ADP: Z=3.0 e 3.5 buoni (stessa partizione, 7 cluster), Z=2.0 e 2.5 usabili. Stabilità per sottocampionamento non calcolata. Z=4.0 (5 cluster) e Z=5.0 (3 cluster) sono buoni ma fuori dall'intervallo 7-20, quindi non prodotti

**Controlli sulle run:**
- Agglomerative: il k nel nome coincide col numero di cluster ottenuto in tutte le 14
- HDBSCAN: numero di cluster e rumore coincidono con la riga di tuning in tutte le 7
- ADP: 16, 9, 7, 7 cluster come nel tuning; Z=3.0 ha 2705, 2321, 195, 188, 166, 142, 128 soggetti, come nel report
- `cluster_plot.png` e `silhouette_plot.png` presenti in tutte le 25. Le 12 run su nc10 sono disegnate sul gemello `08-10_s2.4-vol_m_euclidean_nc2` (stessi parametri tranne `n_components`); le 4 ADP sullo stesso embedding nc2
- Tutte le 25 si aprono in Dash (le run su nc10 e ADP sul loro gemello 2D, con la nota in calce)

##### Decisioni
- Prodotte tutte le righe HDBSCAN usabili con 8-20 cluster (7 run) pur non essendo stabili, per coerenza con s1.4; vanno lette come descrizioni, non come struttura
- ADP solo con `metric=dice`, Z=3.5 incluso anche se dà la stessa partizione di Z=3.0 (per coerenza con s1.4, non perché aggiunga informazione)
- Il lato lesionale non è stato trattato: l'input è invariato, e i cluster puri per lato sono attesi

##### Note
- Ogni run ADP dura circa 48 minuti (ricalcola le distanze dice su 291345 colonne) e copia `matrix.npy` (6.3 GB): `production/adp` pesa 25 GB
- Come per s1.4, `params_file` nel `config.md` punta a un file temporaneo; il registro del repo non è stato modificato e i parametri veri sono in `config.md` e `runs.csv`

---

## 10-09-2026 — s2.2-vol

### 5 opzioni di k in esplorazione

##### Input
- s2.2-vol
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `07-09_s2.2-vol_m_euclidean_nc2`
- Dati originali: `data/derived/sdc_matrix/07-09_s2.2-vol`
- 1570 soggetti

##### Metodi
agglomerative, gmm, kmeans, spectral, hdbscan

##### Obiettivo
- Produrre più granularità con la stessa profondità di s1.1-vol/s1.2-vol (l'intero sweep k=2..6 in parallelo su 4 metodi, non solo 2-3 valori), sapendo dal tuning ([`s2_tuning.md`](s2_tuning.md)) che ogni metodo converge sullo stesso taglio emisfero:
  - A-E: k=2/3/4/5/6 su 4 metodi in parallelo (agglomerative, kmeans, gmm, spectral) — stessa struttura a risoluzione crescente, non letture alternative. **C/D/E (k=4/5/6) sono esattamente gli stessi k prodotti per s1.1-vol/s1.2-vol** ([`results/lesion/clustering/production`](../../../results/lesion/clustering/production)); A/B (k=2/3) estendono lo sweep verso il basso, dove il tuning di s2.2-vol (a differenza di s1) mostra il vero massimo
  - F: isola spectral al suo secondo picco (`gamma=5.0`, k=8), un regime diverso da A-E — come l'opzione D di s1.1-vol
  - G/H: hdbscan a due granularità (fine/grossolana), come in s1.1-vol

##### Risultati

| Opzione | Metodo | Parametri | Cluster trovati | Purezza per emisfero *[1]* | Link |
| --- | --- | --- | --- | --- | --- |
| A (k2) | agglomerative | `linkage=average, metric=cosine` | 2 | 0.78 / 0.86 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k2_link_average/config.md) |
| A (k2) | kmeans | — | 2 | 0.72 / 0.86 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k2/config.md) |
| A (k2) | gmm | `covariance_type=spherical` | 2 | 0.73 / 0.86 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp2_cov_spherical/config.md) |
| A (k2) | spectral | `affinity=rbf, gamma=1.0` | 2 | 0.86 / 0.71 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k2_aff_rbf/config.md) |
| B (k3) | agglomerative | `linkage=average, metric=cosine` | 3 | 0.72–0.86 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k3_link_average/config.md) |
| B (k3) | kmeans | — | 3 | 0.66–0.86 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k3/config.md) |
| B (k3) | gmm | `covariance_type=diag` | 3 | 0.66–0.86 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp3_cov_diag/config.md) |
| B (k3) | spectral | `affinity=rbf, gamma=1.0` | 3 | 0.74–0.86 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k3_aff_rbf/config.md) |
| C (k4) | agglomerative | `linkage=average, metric=cosine` | 4 | 0.72–0.90 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k4_link_average/config.md) |
| C (k4) | kmeans | — | 4 | 0.55–0.88 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k4/config.md) |
| C (k4) | gmm | `covariance_type=diag` | 4 | 0.57–0.88 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp4_cov_diag/config.md) |
| C (k4) | spectral | `affinity=rbf, gamma=0.1` | 4 | 0.60–0.87 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k4_aff_rbf/config.md) |
| D (k5) | agglomerative | `linkage=average, metric=cosine` | 5 | 0.52–0.90 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k5_link_average/config.md) |
| D (k5) | kmeans | — | 5 | 0.54–0.88 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k5/config.md) |
| D (k5) | gmm | `covariance_type=tied` | 5 | 0.51–0.89 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp5_cov_tied/config.md) |
| D (k5) | spectral | `affinity=rbf, gamma=0.1` | 5 | 0.62–0.88 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k5_aff_rbf/config.md) |
| E (k6) | agglomerative | `linkage=average, metric=cosine` | 6 | 0.52–0.91 | [config.md](../../../results/sdc/clustering/production/agglomerative/umap/10-09_s2.2-vol_m_euclidean_nc2_k6_link_average/config.md) |
| E (k6) | kmeans | — | 6 | 0.49–0.89 | [config.md](../../../results/sdc/clustering/production/kmeans/umap/10-09_s2.2-vol_m_euclidean_nc2_k6/config.md) |
| E (k6) | gmm | `covariance_type=spherical` | 6 | 0.51–0.88 | [config.md](../../../results/sdc/clustering/production/gmm/umap/10-09_s2.2-vol_m_euclidean_nc2_n_comp6_cov_spherical/config.md) |
| E (k6) | spectral | `affinity=rbf, gamma=1.0` | 6 | 0.42–0.90 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k6_aff_rbf/config.md) |
| F (k8, solo spectral) | spectral | `affinity=rbf, gamma=5.0` | 8 | 0.56–0.91 | [config.md](../../../results/sdc/clustering/production/spectral/umap/10-09_s2.2-vol_m_euclidean_nc2_k8_aff_rbf/config.md) |
| G (hdbscan A) | hdbscan | `min_cluster_size=10, min_samples=10` | 42 (+369 noise) | 0.40–1.0 | [config.md](../../../results/sdc/clustering/production/hdbscan/umap/10-09_s2.2-vol_m_euclidean_nc2_mcs10_ms10/config.md) |
| H (hdbscan B) | hdbscan | `min_cluster_size=100, min_samples=10` | 5 (+189 noise) | 0.50–0.91 | [config.md](../../../results/sdc/clustering/production/hdbscan/umap/10-09_s2.2-vol_m_euclidean_nc2_mcs100_ms10/config.md) |

*[1] Frazione del cluster occupata dalla categoria `lesion_side` più frequente (left/right/both/unknown) — quanto un cluster è "puro" per emisfero.*

- Ogni opzione, a ogni granularità, resta dominata dal lato della lesione: anche a k=8 (opzione F) e nei 5 cluster di H, la purezza per emisfero non scende mai sotto 0.40 e nella maggior parte dei cluster supera 0.80.
- **Agglomerative non è monotono in k**: la silhouette del tuning cala da k=2 (0.80) a k=4 (0.745), ma risale a k=6 (0.761) — più alta di k=4 e k=5. Non indica una struttura genuinamente diversa a k=6: la purezza per emisfero resta nella stessa fascia (0.52–0.91) delle altre granularità.
- hdbscan (G) trova strutture quasi pure (>0.9 in 30 dei 42 cluster) ma a costo di 369 soggetti (23.5%) scartati come rumore — coerente con quanto già visto nel tuning.
- Nessuna opzione produce un cluster genuinamente misto per emisfero di dimensione paragonabile ai puri — a differenza di s1 (lesioni), dove alcuni cluster misti erano sostanziali.

##### Decisioni

**Stessa decisione di s1: nessun k unico, si tengono aperte le granularità A-H.** Ma qui la ragione è diversa da s1 — non è che criteri diversi indichino k diversi in modo legittimamente ambiguo: è che **nessuna granularità sfugge all'artefatto di lateralizzazione**, quindi tenerle aperte non è "più letture della stessa struttura clinica", è "documentare che la struttura trovabile qui è l'emisfero, a qualunque risoluzione si guardi". Chi userà queste run a valle deve saperlo prima di interpretare un cluster come un sottotipo clinico.
