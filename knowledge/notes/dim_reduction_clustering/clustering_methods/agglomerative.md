# Clustering agglomerativo (gerarchico)

Metodo `agglomerative` di `CLUSTERING_METHODS` (`src/analysis/clustering.py`), implementato con `sklearn.cluster.AgglomerativeClustering`. Le metriche di valutazione citate qui sono definite in [`evaluation_metrics.md`](evaluation_metrics.md).

**In breve**
- Parte da un cluster per soggetto e fonde, a ogni passo, i due cluster più vicini, fino a uno solo. Il risultato è un albero (dendrogramma); il numero di cluster si sceglie tagliandolo.
- Cosa vuol dire "più vicini" lo decide il **linkage** (ward, average, complete, single). È la scelta che conta di più.
- È deterministico: stessi dati, stessi parametri, stesso albero.

---

## 1. Cosa fa

Il metodo segue lo schema generale del clustering gerarchico agglomerativo [3, 4]:

1. ogni soggetto è un cluster;
2. si calcolano le distanze tra tutte le coppie di cluster;
3. si fondono i due cluster con la distanza minore;
4. si aggiornano le distanze del nuovo cluster da tutti gli altri;
5. si ripete finché resta un cluster.

Ogni fusione avviene a un'**altezza**, il valore del criterio di linkage per quella coppia. L'albero delle fusioni, con le altezze, è il dendrogramma. Tagliarlo a un'altezza dà una partizione; `n_clusters` dice a quale numero di cluster tagliare [10].

È un algoritmo **greedy**: una fusione fatta non si disfa più, quindi un errore all'inizio condiziona tutto l'albero [4].

---

## 2. Perché lo fa: i criteri di linkage

La distanza tra **due soggetti** è la `metric` (euclidea, coseno, manhattan...). La distanza tra **due cluster** $A$ e $B$ è il linkage [10]:

| Linkage | Distanza tra $A$ e $B$ | Effetto tipico |
|---|---|---|
| `single` | $\displaystyle \min_{a \in A,\, b \in B} d(a,b)$ | incatena gruppi distinti attraverso pochi punti-ponte (*chaining*); forme allungate [3, 4] |
| `complete` | $\displaystyle \max_{a \in A,\, b \in B} d(a,b)$ | cluster compatti, di diametro contenuto [3] |
| `average` (UPGMA) | $\displaystyle \frac{1}{|A|\,|B|} \sum_{a \in A} \sum_{b \in B} d(a,b)$ | compromesso tra i due [3, 4] |
| `ward` | aumento della somma dei quadrati dentro i cluster (sotto) | cluster compatti e di dimensioni regolari; vicino all'obiettivo di K-Means [1, 3, 10] |

**Ward.** Ward (1963) propone di fondere, a ogni passo, la coppia che peggiora meno una funzione obiettivo; l'esempio che rende celebre il metodo è la somma dei quadrati degli errori (ESS) [1]. Con $c_A$ il centroide di $A$ e $n_A$ la sua taglia, l'aumento di ESS fondendo $A$ e $B$ è

$$
\Delta(A, B) = \mathrm{ESS}(A \cup B) - \mathrm{ESS}(A) - \mathrm{ESS}(B) = \frac{n_A\, n_B}{n_A + n_B}\, \lVert c_A - c_B \rVert^2 .
$$

Ha senso solo con la distanza euclidea, perché usa centroidi e quadrati. Per questo scikit-learn accetta `ward` solo con `metric="euclidean"` [10].

**La formula di Lance-Williams.** Tutti e quattro i linkage si aggiornano con una sola ricorrenza: fondendo $i$ e $j$, la distanza del nuovo cluster da un terzo cluster $k$ è

$$
d(k, i \cup j) = \alpha_i\, d(k,i) + \alpha_j\, d(k,j) + \beta\, d(i,j) + \gamma\, \lvert d(k,i) - d(k,j) \rvert
$$

con i coefficienti [2, 4]:

| Linkage | $\alpha_i$ | $\beta$ | $\gamma$ |
|---|---|---|---|
| single | $1/2$ | $0$ | $-1/2$ |
| complete | $1/2$ | $0$ | $+1/2$ |
| average | $n_i/(n_i+n_j)$ | $0$ | $0$ |
| ward (sulle distanze **al quadrato**) | $(n_i+n_k)/(n_i+n_j+n_k)$ | $-n_k/(n_i+n_j+n_k)$ | $0$ |

**Ward1 e Ward2** (Murtagh & Legendre 2014) [5]. Ward si ottiene con Lance-Williams solo se la ricorrenza è applicata alle distanze euclidee **al quadrato**. Un'implementazione che la applica alle distanze non al quadrato ("Ward1", in R `hclust(method = "ward.D")`) non minimizza il criterio di Ward. "Ward2" (`ward.D2`) lo fa e riporta come altezza la radice. scikit-learn lavora sulle coordinate (non su una matrice di dissimilarità) e riporta come altezza $\sqrt{2\,\Delta}$ (codice di `sklearn/cluster/_agglomerative.py`, 1.8.0): per due soggetti singoli è la loro distanza euclidea, come in Ward2.

**Monotonia.** Single, complete, average e ward producono altezze che non diminuiscono mai da una fusione alla successiva (niente "inversioni"); centroid e median, che il progetto non usa, possono produrle [4].

**Costo** (Müllner 2011) [4]. Per questi quattro linkage esistono algoritmi in $O(n^2)$ tempo con la matrice delle distanze in memoria (*nearest-neighbor chain*; per single, l'albero di copertura minimo). scikit-learn usa un algoritmo sull'albero minimo per `single` e `scipy.cluster.hierarchy` per gli altri (codice di `_agglomerative.py`, 1.8.0). Con $n \approx 5800$ la matrice condensata ha circa 17 milioni di valori, circa 135 MB in `float64`.

---

## 3. Il nostro contesto

- **Input.** Embedding UMAP con `n_components` 2, 3 o 10 (metrica UMAP `euclidean` o `dice`), score PCA (anche varimax), la matrice SDC "stream" a 87 colonne (`docs/guides/evaluation.md`), oppure la matrice lesionale grezza. Circa 1100-5850 soggetti a seconda della matrice.
- **Griglia attuale** (`config/registry/params_clustering.json`, voce `agglomerative`): `n_clusters` da 2 a 30, `linkage` ∈ {ward, average, complete, single}, `metric` ∈ {euclidean, cosine, manhattan}. `ward` con metrica non euclidea è saltato con un avviso (`is_invalid_ward_metric_combo`): restano 10 coppie (linkage, metric) × 29 k = 290 combinazioni.
- **Distanze precalcolate.** Per `euclidean` (e `dice`/`jaccard`, supportate dal codice ma non nella griglia attuale) con linkage diverso da `ward`, la matrice delle distanze è calcolata una volta per metrica e riusata per fit e silhouette (`_agglomerative_fit_metric_aware`). È un'ottimizzazione: il risultato è lo stesso del fit diretto.
- **`params` di base**: `n_clusters: 3`, `linkage: ward`, `metric: euclidean`. Il file è stato condiviso da più run: va confrontato con la colonna `params` di `runs_tuning.csv` prima di rilanciare (`lessons_learned.md`, #36).

---

## 4. I parametri

Default verificati su scikit-learn 1.8.0 (ambiente `nemesis`, `inspect.signature`).

| Parametro | Significato | Valori | Default sklearn | Nel progetto |
|---|---|---|---|---|
| `n_clusters` | dove si taglia l'albero | intero ≥ 1, o `None` con `distance_threshold` | `2` | sweep 2-30 |
| `linkage` | distanza tra cluster (§2) | `ward`, `complete`, `average`, `single` | `"ward"` | tutti e quattro |
| `metric` | distanza tra soggetti | ogni metrica di `pairwise_distances`, o `"precomputed"`; con `ward` solo `euclidean` | `"euclidean"` | `euclidean`, `cosine`, `manhattan` |
| `distance_threshold` | taglio per altezza invece che per numero | float ≥ 0 | `None` | non usato nello sweep; `0` per avere l'albero intero (`compute_dendrogram_linkage`) |
| `connectivity` | vincola le fusioni a coppie vicine in un grafo | matrice o callable | `None` | non usato |
| `compute_full_tree` | costruisce l'albero intero o si ferma a `n_clusters` | `"auto"`, bool | `"auto"` | default |
| `compute_distances` | salva le altezze delle fusioni | bool | `False` | `True` solo per dendrogramma e cofenetica |
| `memory` | cache dell'albero su disco | path | `None` | non usato |

Fonte dei significati: documentazione di `AgglomerativeClustering` [10].

**La metrica.** scikit-learn indica `average` come alternativa a `ward` quando la distanza non è euclidea; `manhattan` è adatta a feature sparse e `cosine` è invariante alla scala globale del vettore [11]. Su un embedding UMAP le coordinate non sono sparse e la loro scala non ha un significato fisico: la scelta tra le tre metriche non ha una motivazione dalla letteratura per questo caso, ed è un'esplorazione del progetto.

---

## 5. Come si fa il tuning

Nessuna fonte dà una regola per scegliere linkage e k; le diagnostiche sotto sono quelle classiche più due del progetto.

1. **Il linkage, a metrica fissata.**
   - *Correlazione cofenetica* per (metric, linkage): quanto l'albero rispetta le distanze [6]. Si confronta solo dentro una metrica. Output: `cophenetic_correlation.csv` (`evaluate_clustering_tuning`).
   - *Accordo tra linkage*: ARI [9] tra le partizioni di due linkage allo stesso k (`linkage_agreement.csv`). Dove è vicino a 1 la scelta del linkage cambia poco. Scelta del progetto.
2. **Il numero di cluster.**
   - *Dendrogramma*: un taglio è naturale dove, salendo, c'è un salto grande tra due altezze consecutive. Il progetto lo riassume nel **salto del dendrogramma** (`dendrogram_jump.csv`): l'altezza della fusione da $k$ a $k-1$ cluster divisa per quella da $k+1$ a $k$, cioè con $h_1 \ge h_2 \ge \dots$ le altezze dalla più alta, $J(k) = h_{k-1}/h_k$. È una diagnostica del progetto, senza fasce di letteratura.
   - *Indici per k*: silhouette (con la stessa `metric`), e CH e DB solo per `euclidean` (colonne di `tuning_results.csv`). Le curve `k_curves_metric=<metric>.png` disegnano silhouette e DB (DB solo per `euclidean`), una linea per linkage. Si cerca un picco della silhouette e una valle di DB **stabili** tra linkage, non un massimo isolato. `single` non è disegnato (la sua silhouette scende molto sotto quella degli altri): i suoi valori sono nelle tabelle del report.
3. **La stabilità rispetto all'embedding.** Lo stesso k e linkage su UMAP con `n_components` diversi: ARI tra le partizioni e contingenza dei cluster (confronto tra più run: non è nel `report.md` di una singola run).

Guida operativa ai grafici: [`clustering_tuning_guide.md`](../clustering_tuning_guide.md), sezioni "Agglomerative".

---

## 6. Come si valuta l'output

- **Indici interni** ([`evaluation_metrics.md`](evaluation_metrics.md)): silhouette con la metrica del clustering; CH e DB solo con `euclidean` (`NaN` altrimenti). Nessun rumore: `noise_fraction` è sempre 0.
- **Del modello**: correlazione cofenetica [6] e salto del dendrogramma al k della run (`model_fit_metrics`, `src/analysis/clustering_evaluation.py`). Il fit viene ripetuto e accettato solo se riproduce le etichette salvate.
- **Silhouette per cluster** (tabella per cluster): un cluster con silhouette media bassa o molti valori negativi ha confini ambigui anche se la media globale è buona [7].

---

## 7. Quando usarlo

| Situazione | Agglomerativo | Alternativa |
|---|---|---|
| Interessa la struttura a più scale (come si dividono i gruppi grandi) | sì: l'albero mostra tutte le partizioni annidate [3] | — |
| Cluster attesi compatti, spazio euclideo | `ward` | K-Means (stesso obiettivo, non gerarchico) |
| Distanza non euclidea | `average` o `complete` [11] | — |
| Densità variabili, rumore, forme irregolari | no: ogni soggetto viene assegnato | HDBSCAN ([`hdbscan.md`](hdbscan.md)) |
| Decine di migliaia di soggetti o più | il costo $O(n^2)$ in memoria pesa [4, 3] | metodi non gerarchici |

---

## 8. Pro e contro

**Pro**
- Deterministico, nessuna inizializzazione casuale.
- Non serve fissare k per costruire l'albero: un solo albero dà tutti i k.
- Il dendrogramma è una diagnostica visiva diretta.
- Accetta qualunque dissimilarità con single, complete e average.

**Contro**
- Greedy: le fusioni non si disfano [4].
- Assegna ogni soggetto: nessun concetto di rumore.
- Il linkage impone una forma: ward e complete favoriscono cluster tondi e di dimensioni simili, single incatena [3, 10].
- Costo quadratico in memoria [4].
- La scelta di k resta esterna all'algoritmo.

---

## 9. Esempio

Cinque soggetti su una retta: A = 0, B = 1, C = 2, D = 6, E = 7. Altezze delle quattro fusioni (scipy 1.17.0):

| Linkage | Fusioni (in ordine) | Altezze |
|---|---|---|
| single | AB, DE, {AB}C (tutte a 1, in un ordine che dipende dai pareggi), {ABC}{DE} | 1, 1, 1, 4 |
| complete | AB, DE, {AB}C, {ABC}{DE} | 1, 1, 2, 7 |
| average | AB, DE, {AB}C, {ABC}{DE} | 1, 1, 1,5, 5,5 |
| ward | AB, DE, {AB}C, {ABC}{DE} | 1, 1, 1,73, 8,52 |

- **Ward a mano.** Fondere A e B: $\Delta = \tfrac{1 \cdot 1}{2} \cdot 1^2 = 0{,}5$, altezza $\sqrt{2 \cdot 0{,}5} = 1$. Fondere {AB} (centroide 0,5) con C: $\Delta = \tfrac{2 \cdot 1}{3}\, (1{,}5)^2 = 1{,}5$, altezza $\sqrt{3} = 1{,}73$. Ultima fusione: centroidi 1 e 6,5, $\Delta = \tfrac{3 \cdot 2}{5}\, (5{,}5)^2 = 36{,}3$, altezza 8,52.
- **Il taglio.** In tutti e quattro i casi il salto più grande è l'ultimo: tagliare sotto di esso dà {A, B, C} e {D, E}. Con ward, $J(2) = 8{,}52/1{,}73 = 4{,}9$.
- **Le altezze non si confrontano tra linkage**: 4 (single) e 8,52 (ward) dicono la stessa cosa, in unità diverse.
- **Cofenetica**: 0,935-0,938 per tutti e quattro ([`evaluation_metrics.md`](evaluation_metrics.md), §5).

---

## 10. Insidie

1. **Tagliare un albero che non ha un taglio naturale.** L'algoritmo produce un albero anche su dati senza gruppi. Se le altezze scendono gradualmente, nessun k è indicato dall'albero [3].
2. **Confrontare altezze o cofenetiche tra metriche o linkage diversi.** Sono in unità diverse (§2).
3. **Ward fuori dalla geometria euclidea.** Non ha senso; scikit-learn lo impedisce, R con `ward.D` no [5].
4. **Single linkage e rumore.** Pochi soggetti-ponte bastano a unire due gruppi; scikit-learn lo descrive come non robusto ai dati rumorosi e come la strategia che produce le dimensioni di cluster più squilibrate [11].
5. **Indici con il bias del linkage.** Silhouette, CH e DB premiano cluster compatti, quindi favoriscono `ward`: il confronto tra linkage con questi indici non è neutrale ([`evaluation_metrics.md`](evaluation_metrics.md), §11).
6. **Pareggi nelle distanze.** Con distanze uguali (frequenti su un embedding UMAP molto impacchettato, o con `dice` saturata a 1) più coppie hanno lo stesso valore e l'ordine delle fusioni dipende dall'implementazione. Osservazione del progetto, non verificata su una fonte.
7. **Clustering su un embedding 2D.** de Bodt et al. (2025) raccomandano di non fare analisi a valle su embedding 2D [8]; il progetto clusterizza anche su `n_components=2` e confronta con 3 e 10 proprio per questo (vedi [`challenge_of_clustering_after_dim_reduction.md`](../challenge_of_clustering_after_dim_reduction.md)).

---

## Fonti

1. Ward, J. H. Jr. (1963). Hierarchical grouping to optimize an objective function. *Journal of the American Statistical Association*, 58(301), 236-244. doi:10.1080/01621459.1963.10500845
2. Lance, G. N., Williams, W. T. (1967). A general theory of classificatory sorting strategies: 1. Hierarchical systems. *The Computer Journal*, 9(4), 373-380. doi:10.1093/comjnl/9.4.373
3. Dinh, T., Hauchi, W., Lisik, D. et al. (2025). Data clustering: an essential technique in data science. *Expert Systems with Applications*, Algorithm 4 e §4.2 - `knowledge/papers/methods/Dinh et al - 2025 - Data clustering an essential technique in data science/`; Bicego, M. (2021), *Il clustering, parte 2* (dispense, Università di Verona) - `knowledge/papers/methods/Slides_Bicego/`
4. Müllner, D. (2011). Modern hierarchical, agglomerative clustering algorithms. arXiv:1109.2378
5. Murtagh, F., Legendre, P. (2014). Ward's hierarchical agglomerative clustering method: which algorithms implement Ward's criterion? *Journal of Classification*, 31, 274-295. doi:10.1007/s00357-014-9161-z
6. Sokal, R. R., Rohlf, F. J. (1962). The comparison of dendrograms by objective methods. *Taxon*, 11(2), 33-40. doi:10.2307/1217208
7. Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65. doi:10.1016/0377-0427(87)90125-7
8. de Bodt, C. et al. (2025). Low-dimensional embeddings of high-dimensional data, §5 - `knowledge/papers/methods/de Bodt et al - 2025 - Low-dimensional embeddings of high-dimensional data/` (sintesi in `dim_reduction_literature_survey.md`)
9. Hubert, L., Arabie, P. (1985). Comparing partitions. *Journal of Classification*, 2(1), 193-218. doi:10.1007/BF01908075
10. scikit-learn 1.8.0, `sklearn.cluster.AgglomerativeClustering` (documentazione e docstring): https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html
11. scikit-learn, User Guide, *Hierarchical clustering* (sezioni "Different linkage type" e "Varying the metric"): https://scikit-learn.org/stable/modules/clustering.html#hierarchical-clustering
