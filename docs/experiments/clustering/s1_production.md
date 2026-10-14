# Diario Esperimenti

**Pipeline:** Clustering (Produzione)

**Dati:** Low dimensional embedding o dati raw

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Parametri scelti a valle del tuning ([`s1_tuning.md`](s1_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

## 12-10-2026 — s1.4-vol

### Produzione ampia dopo il tuning: k buoni e discreti, tutte le righe HDBSCAN usabili con 8-20 cluster

##### Input
- s1.4-vol, 5845 soggetti
- Embedding: UMAP `{dice, euclidean}` x `n_components` 2/10, path `08-10_s1.4-vol_m_{dice,euclidean}_nc{2,10}` in `results/lesion/dim_reduction/production/umap/`
- ADP sulla matrice grezza `data/derived/lesion_matrix/07-10_s1.4-vol` (5845 x 221955)
- Parametri scelti dal tuning del 12-10-2026 ([`s1_tuning.md`](s1_tuning.md))

##### Metodi
agglomerative, hdbscan, adp

##### Obiettivo
- Produrre i cluster di tutti i candidati "buoni" e "discreti" del tuning, non un solo k: ogni run è una lettura a una risoluzione diversa
- **Buono** = criteri del [README dei report](../../../results/reports/cluster_tuning_notebooks/README.md). **Discreto** = agglomerative "parziale" (stabile oppure almeno 2 segnali degli indici), HDBSCAN "usabile" (3-30 cluster, rumore ≤ 25%, cluster più grande ≤ 60%), ADP con plateau meno netto
- Un k non stabile resta una partizione valida per descrivere i soggetti, ma non sostiene "esistono N sottotipi"

##### Risultati

67 run, tutte concluse; 67 righe in `runs.csv` di ciascun metodo, nessun duplicato.

| Metodo | Parametri | Input | Run | Cluster | Link |
| --- | --- | --- | --- | --- | --- |
| agglomerative | `linkage=ward, metric=euclidean`, k = 3, 6, 8, 11, 13, 16, 20 | dice nc2 | 7 | k | [runs.csv](../../../results/lesion/clustering/production/agglomerative/runs.csv) |
| agglomerative | k = 3, 4, 5, 7, 8, 9, 17 | dice nc10 | 7 | k | stesso |
| agglomerative | k = 3, 7, 11 | euclidean nc2 | 3 | k | stesso |
| agglomerative | k = 3, 4, 5, 6, 8, 10 | euclidean nc10 | 6 | k | stesso |
| hdbscan | 8 cluster: 100/{1,5,10,20}, 75/{10,20}; 9: 50/20; 10: 30/20; 11: 10/20, 15/20, 20/20; 18: 75/1; 19: 75/5; 20: 50/10 | dice nc2 | 14 | 8-20, rumore 0.6-12.7% | [runs.csv](../../../results/lesion/clustering/production/hdbscan/runs.csv) |
| hdbscan | 8: 100/{1,5,10,20}, 75/20; 10: 50/10, 50/20; 11: 30/20; 14: 75/5, 75/10; 17: 75/1; 20: 30/10 | dice nc10 | 12 | 8-20, rumore 0.3-13.6% | stesso |
| hdbscan | 11: 100/10; 12: 100/1; 14: 75/10; 15: 75/5; 19: 75/1 | euclidean nc2 | 5 | 11-19, rumore 10.9-13.6% | stesso |
| hdbscan | 12: 100/20; 14: 100/5, 75/20; 15: 100/1, 100/10; 16: 75/10; 19: 50/20, 75/5; 20: 75/1 | euclidean nc10 | 9 | 12-20, rumore 12.7-19.6% | stesso |
| adp | `metric=dice`, Z = 2.5, 3.0, 3.5, 4.0 | matrice grezza | 4 | 17, 15, 12, 7 | [runs.csv](../../../results/lesion/clustering/production/adp/runs.csv) |

Dentro ogni tabella la sigla è `min_cluster_size/min_samples`. Le cartelle di output sono `<dd-mm>_s1.4-vol_<embedding>_<tag>` sotto `production/<metodo>/umap/` (`raw/` per ADP).

**Quali sono "buoni" e quali "discreti"** (dal tuning):
- agglomerative buoni: dice nc2 k=3; dice nc10 k=3, 4, 5, 7; euclidean nc10 k=3, 4, 5. Gli altri k sono discreti (euclidean nc2 non ha nessun k buono)
- HDBSCAN buone: dice nc2 8 delle 11 righe con 8-11 cluster (non buone: 100/1, 10/20, 15/20); dice nc10 le 5 righe con 8 cluster; euclidean nc10 tutte tranne 100/1 e 100/10. Le altre sono discrete; euclidean nc2 non ne ha di buone
- ADP: Z=3.0 buono, Z=2.5, 3.5, 4.0 usabili. Stabilità per sottocampionamento non calcolata

**Controlli sulle run:**
- Agglomerative: il k nel nome coincide col numero di cluster ottenuto in tutte le 23
- HDBSCAN: numero di cluster e quota di rumore coincidono con la riga di tuning in tutte le 40
- ADP: 17, 15, 12, 7 cluster come nel tuning; Z=3.0 ha 4 cluster grandi (1886, 1422, 1180, 165) e 11 piccoli, il più piccolo di 2 soggetti
- Ward k=3 su euclidean nc10: 3437 / 1187 / 1221 soggetti, come nel report del tuning
- `cluster_plot.png` e `silhouette_plot.png`: presenti in tutte le 67 run. Le 19 run su dice nc10 sono state rifatte (`overwrite`) con `viz_embedding_path` = `12-10_s1.4-vol_m_dice_nc2`, un UMAP dice 2D con `n_neighbors=50` e `min_dist=0.0` creato apposta (gemello di dice nc10; il dice nc2 scelto dal tuning ha `n_neighbors=100`, quindi il controllo di coerenza lo rifiutava). I cluster non cambiano (le run sono deterministiche). Le 19 righe vecchie di `runs.csv` sono state tolte, restano quelle nuove

##### Decisioni
- Prodotte tutte le righe HDBSCAN con 8-20 cluster, non una per numero di cluster: 40 run invece di 24. Molte righe condividono la stessa partizione (per esempio le 5-6 righe a 8 cluster dei dice, ARI tra loro ≥ 0.995), quindi non sono 40 letture indipendenti
- ADP solo con `metric=dice`: l'euclidean è degenere su ogni Z (un cluster al 93-99% dei soggetti)
- Il lato lesionale non è stato trattato: l'input è invariato, non riflesso. I cluster puri per lato sono attesi (il lato è calcolato dalla maschera) e non confermano nulla di indipendente

##### Note
- I parametri di ogni run sono scritti in `config.md` e `runs.csv` (`Params used`), ma `params_file` nel `config.md` punta a un file temporaneo, non a `config/registry/params_clustering.json`: il registro del repo non è stato modificato
- Ogni run ADP copia `matrix.npy` (1.2 GB): `production/adp` pesa 4.8 GB

---

## 03-09-2026 — s1.2-vol

### Stesso schema (A-C/E-F) su coorte estesa, parametri da s1_tuning.md

##### Input
- s1.2-vol
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `28-08_s1.2-vol_m_euclidean_nc2`
- Dati originali: `data/derived/lesion_matrix/25-08_s1.2-vol`
- 5269 soggetti
##### Metodi
kmeans, gmm, agglomerative, spectral, hdbscan

##### Obiettivo
- Stesso schema di esplorazione di s1.1-vol (opzioni k4/k5/k6 in parallelo su kmeans/gmm/agglomerative, spectral piegato dentro B/C, due candidati hdbscan), applicato ai parametri emersi dal tuning s1.2-vol ([`s1_tuning.md`](s1_tuning.md))
- Nessuna opzione D: a differenza di s1.1-vol (dove il miglior silhouette assoluto di spectral cadeva isolato a k=8), qui il picco assoluto della griglia spectral (`rbf, k=5, gamma=1.0`, 0.426) cade già dentro l'opzione B

##### Risultati

| Opzione | Metodo | Parametri | Cluster trovati | Link |
| --- | --- | --- | --- | --- |
| A (k4) | kmeans | — | 4 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/03-09_s1.2-vol_m_euclidean_nc2_k4/config.md) |
| A (k4) | gmm | `covariance_type=full` | 4 | [config.md](../../../results/lesion/clustering/production/gmm/umap/03-09_s1.2-vol_m_euclidean_nc2_n_comp4_cov_full/config.md) |
| A (k4) | agglomerative | `linkage=average` | 4 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/03-09_s1.2-vol_m_euclidean_nc2_k4_link_average/config.md) |
| B (k5) | kmeans | — | 5 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/03-09_s1.2-vol_m_euclidean_nc2_k5/config.md) |
| B (k5) | gmm | `covariance_type=full` | 5 | [config.md](../../../results/lesion/clustering/production/gmm/umap/03-09_s1.2-vol_m_euclidean_nc2_n_comp5_cov_full/config.md) |
| B (k5) | agglomerative | `linkage=average` | 5 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/03-09_s1.2-vol_m_euclidean_nc2_k5_link_average/config.md) |
| B (k5) | spectral | `affinity=rbf, gamma=1.0` | 5 | [config.md](../../../results/lesion/clustering/production/spectral/umap/03-09_s1.2-vol_m_euclidean_nc2_k5_aff_rbf/config.md) |
| C (k6) | kmeans | — | 6 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/03-09_s1.2-vol_m_euclidean_nc2_k6/config.md) |
| C (k6) | gmm | `covariance_type=full` | 6 | [config.md](../../../results/lesion/clustering/production/gmm/umap/03-09_s1.2-vol_m_euclidean_nc2_n_comp6_cov_full/config.md) |
| C (k6) | agglomerative | `linkage=average` | 6 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/03-09_s1.2-vol_m_euclidean_nc2_k6_link_average/config.md) |
| C (k6) | spectral | `affinity=rbf, gamma=0.1` | 6 | [config.md](../../../results/lesion/clustering/production/spectral/umap/03-09_s1.2-vol_m_euclidean_nc2_k6_aff_rbf/config.md) |
| E (hdbscan A) | hdbscan | `min_cluster_size=100, min_samples=20` | 15 (+1289 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/03-09_s1.2-vol_m_euclidean_nc2_mcs100_ms20/config.md) |
| F (hdbscan B) | hdbscan | `min_cluster_size=75, min_samples=20` | 19 (+1216 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/03-09_s1.2-vol_m_euclidean_nc2_mcs75_ms20/config.md) |
| G (hdbscan C) | hdbscan | `min_cluster_size=200, min_samples=5` | 7 (+1443 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/03-09_s1.2-vol_m_euclidean_nc2_mcs200_ms5/config.md) |

- **G**: terzo punto di vista complementare a E/F, per avvicinarsi allo spirito esplorativo multi-opzione di s1.1-vol — granularità molto più grossolana (7 cluster contro 15/19), silhouette leggermente più bassa (0.429 vs. 0.464/0.449) ma comunque solida. Non sostituisce E/F, li affianca. Verificato ad-hoc su tutta la riga `min_samples`∈{5,10,20} a `mcs=200` prima di scegliere `ms=5`: `ms=10`/`ms=20` collassano a 2-3 cluster con silhouette molto più debole (0.18/0.08, probabile artefatto `lesion_side` a `ms=10`).
- **E/F rifatte lo stesso giorno** (03-09-2026): la prima versione (`mcs=5,ms=10` → 143 cluster; `mcs=30,ms=5` → 53 cluster) era scelta alla cieca sul numero di cluster risultante, mai calcolato durante il tuning. Corretto aggiungendo `n_clusters_found` a `METHOD_METRIC_COLUMNS["hdbscan"]` (`src/analysis/clustering_tuning.py`) e rifacendo il tuning con `min_cluster_size`∈{10,20,30,50,75,100} (vedi `s1_tuning.md`, sezione 03-09-2026) — i due nuovi candidati sopra sono a una granularità comparabile a s1.1-vol (8-20 cluster) e hanno la migliore/seconda migliore silhouette dell'intera griglia rifatta. Le directory di output e le righe `runs.csv` dei due run originali (`mcs5_ms10`/`mcs30_ms5`) sono state rimosse, non lasciate come residuo.

##### Decisioni

**Stessa decisione di s1.1-vol: nessun k unico, si tengono aperte le granularità in parallelo.** Le ragioni non cambiano con la coorte estesa — nessun criterio interno converge su un k solo, e k va deciso insieme a `n_components`, a valle.

Rispetto a s1.1-vol cambiano due cose, entrambe conseguenza dei dati e non di un cambio di criterio:

- **niente opzione D**: su s1.1-vol il miglior silhouette di spectral cadeva isolato a k=8, fuori dalle tre granularità; qui il picco assoluto della griglia (`rbf, k=5, gamma=1.0`) cade già dentro l'opzione B, quindi non serve un'opzione a parte per rappresentarlo
- **tre candidati hdbscan invece di due** (E/F/G): G a granularità molto più grossolana (7 cluster contro 15/19) affianca gli altri due per coprire lo stesso spettro esplorativo che su s1.1-vol era coperto da E/F più D

---

## 01-09-2026 — s1.1-vol

### 6 opzioni di k in esplorazione 

##### Input
- s1.1-vol
- Embedding: UMAP `euclidean`, n_components=2
- Path Embedding: `11-08_s1.1-vol_m_euclidean_nc2` 
- Dati originali: `data/derived/lesion_matrix/21-07_s1.1-vol`
- 1150 soggetti
##### Metodi
agglomerative, gmm, kmeans, hdbscan, spectral

##### Obiettivo
- Produrre 6 opzioni di k 
	- A/B/C variano k (4/5/6) in parallelo su più metodi per confrontare la struttura; 
	- D isola spectral a k=8 (miglior silhouette assoluto del tuning, 0.502); 
	- E/F esplorano hdbscan a due combinazioni `min_cluster_size`/`min_samples`

##### Risultati

| Opzione | Metodo | Parametri | Cluster trovati | Link |
| --- | --- | --- | --- | --- |
| A (k4) | agglomerative | `linkage=average` | 4 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1-vol_m_euclidean_nc2_k4_link_average/config.md) |
| A (k4) | gmm | `covariance_type=full` | 4 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1-vol_m_euclidean_nc2_n_comp4_cov_full/config.md) |
| A (k4) | kmeans | — | 4 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1-vol_m_euclidean_nc2_k4/config.md) |
| B (k5) | agglomerative | `linkage=average` | 5 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1-vol_m_euclidean_nc2_k5_link_average/config.md) |
| B (k5) | gmm | `covariance_type=full` | 5 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1-vol_m_euclidean_nc2_n_comp5_cov_full/config.md) |
| B (k5) | kmeans | — | 5 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1-vol_m_euclidean_nc2_k5/config.md) |
| B (k5) | spectral | `affinity=nearest_neighbors, n_neighbors=30` | 5 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1-vol_m_euclidean_nc2_k5_aff_nearest_neighbors/config.md) |
| C (k6) | agglomerative | `linkage=average` | 6 | [config.md](../../../results/lesion/clustering/production/agglomerative/umap/01-09_s1.1-vol_m_euclidean_nc2_k6_link_average/config.md) |
| C (k6) | gmm | `covariance_type=full` | 6 | [config.md](../../../results/lesion/clustering/production/gmm/umap/01-09_s1.1-vol_m_euclidean_nc2_n_comp6_cov_full/config.md) |
| C (k6) | kmeans | — | 6 | [config.md](../../../results/lesion/clustering/production/kmeans/umap/01-09_s1.1-vol_m_euclidean_nc2_k6/config.md) |
| C (k6) | spectral | `affinity=rbf, gamma=1.0` | 6 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1-vol_m_euclidean_nc2_k6_aff_rbf/config.md) |
| D (k8, solo spectral) | spectral | `affinity=rbf, gamma=1.0` | 8 | [config.md](../../../results/lesion/clustering/production/spectral/umap/01-09_s1.1-vol_m_euclidean_nc2_k8_aff_rbf/config.md) |
| E (hdbscan A) | hdbscan | `min_cluster_size=20, min_samples=10` | 8 (+95 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/01-09_s1.1-vol_m_euclidean_nc2_mcs20_ms10/config.md) |
| F (hdbscan B) | hdbscan | `min_cluster_size=15, min_samples=5` | 20 (+107 noise) | [config.md](../../../results/lesion/clustering/production/hdbscan/umap/01-09_s1.1-vol_m_euclidean_nc2_mcs15_ms5/config.md) |

##### Decisioni

**Non si sceglie un k unico: portare avanti più granularità in parallelo è la decisione.**

Nessun criterio interno indica un k solo. La silhouette premia k alti per costruzione, CH cresce quasi sempre con k e l'inertia non ha un gomito netto (vedi [`s1_tuning.md`](s1_tuning.md)) — restringere a un valore significherebbe far scegliere a una metrica di comodo qualcosa che la metrica non sa decidere.

In più k non è separabile da `n_components` dell'embedding: il k migliore non converge tra n2/n3/n10, quindi i due vanno decisi insieme e a valle, non qui.

Restano quindi valide tutte le opzioni prodotte, ognuna come una lettura diversa della stessa struttura:

- **A/B/C (k=4/5/6)** — le tre granularità plausibili, ognuna su più metodi, così una differenza tra opzioni si distingue da una differenza tra algoritmi
- **D (spectral k=8)** — il miglior silhouette assoluto del tuning (0.502), tenuto come estremo di riferimento, non come candidato alla pari
- **E/F (hdbscan)** — granularità non imposta a priori, con rumore esplicito: il controllo indipendente rispetto ai metodi che il k lo ricevono in input

Il confronto tra queste opzioni avviene in [`notebooks/post-results_analysis/clustering_comparison.ipynb`](../../../notebooks/post-results_analysis/clustering_comparison.ipynb), che ne carica un sottoinsieme alla volta in `SELECTED_RUNS` — è lì che si guarda cosa cambia davvero tra un k e l'altro, non in una scelta fatta a questo stadio.
