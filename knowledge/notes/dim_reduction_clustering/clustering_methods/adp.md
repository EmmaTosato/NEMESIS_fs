# ADP: Advanced Density Peaks (DADApy)

Metodo `adp` di `CLUSTERING_METHODS`, implementato in `src/analysis/adp.py` sopra `dadapy.Clustering` (DADApy 0.3.4, ambiente conda `nemesis_fallback`). Come si lancia: [`docs/guides/clustering.md`](../../../../docs/guides/clustering.md), sezione "ADP". Metriche: [`evaluation_metrics.md`](evaluation_metrics.md).

**In breve**
- Stima la densità attorno a ogni soggetto, trova i **picchi** di densità e assegna ogni soggetto al picco che raggiunge salendo.
- Due picchi restano cluster separati solo se la "valle" (il punto di sella) tra loro è **significativamente** più bassa di entrambi. La soglia è `Z`, l'unico parametro libero [3].
- Il numero di cluster non si sceglie. Nel progetto gira sulla matrice **grezza** (voxel o tratti), con distanza `dice` o `euclidean`.

---

## 1. Cosa fa

ADP (d'Errico, Facco, Laio & Rodriguez 2021) è un'evoluzione del *density peak clustering* di Rodriguez & Laio (2014) [1, 3]. I passi, nell'ordine in cui il progetto li chiama (`_AdpSession` in `src/analysis/adp.py`):

1. **Distanze e vicini**: per ogni soggetto, i `maxk` vicini più prossimi e le loro distanze.
2. **Dimensione intrinseca** con lo stimatore 2NN (`compute_id_2NN`) [4].
3. **Densità** con lo stimatore PAk (`compute_density_PAk`): un logaritmo della densità per soggetto e il suo errore [5].
4. **Clustering** (`compute_clustering_ADP(Z)`): picchi, assegnazione, punti di sella, fusione dei picchi non significativi [3].

I passi 2 e 3 non dipendono da `Z`: lo sweep su `Z` rifà solo il passo 4.

---

## 2. Perché lo fa: le formule

### 2.1 Il punto di partenza: density peaks (Rodriguez & Laio 2014)

Per ogni punto $i$ si calcolano due numeri [1]:

$$
\rho_i = \sum_{j} \chi(d_{ij} - d_c), \quad \chi(x) = \begin{cases} 1 & x < 0 \\ 0 & \text{altrimenti} \end{cases}
\qquad\qquad
\delta_i = \min_{j:\ \rho_j > \rho_i} d_{ij}
$$

- $\rho_i$ è la densità locale (quanti punti entro il raggio $d_c$); $\delta_i$ è la distanza dal punto più vicino **più denso** (per il punto più denso di tutti, la distanza massima).
- I **centri** sono i punti con $\rho$ e $\delta$ entrambi alti: densi e lontani da qualunque punto più denso. Si scelgono guardando il grafico $\rho$-$\delta$ (*decision graph*).
- Ogni altro punto va nel cluster del suo vicino più prossimo con densità maggiore.
- Un **halo** facoltativo marca come rumore i punti con densità sotto quella del bordo del loro cluster [1].

Due scelte restano a mano: il raggio $d_c$ e i centri dal grafico. ADP le sostituisce entrambe con stime statistiche [3].

### 2.2 Dimensione intrinseca: 2NN (Facco et al. 2017)

Per ogni punto, $\mu_i = r_{i,2}/r_{i,1}$, il rapporto tra le distanze dal secondo e dal primo vicino. Se la densità è circa costante sulla scala dei primi due vicini, $\mu$ segue una distribuzione di Pareto che dipende solo dalla dimensione intrinseca $d$ [4]:

$$
F(\mu) = 1 - \mu^{-d} \quad\Longrightarrow\quad -\log\big(1 - F(\mu)\big) = d \log \mu
$$

$d$ è la pendenza della retta per l'origine tra $\log \mu$ e $-\log(1 - F_{\text{emp}}(\mu))$. DADApy scarta una quota dei $\mu$ più grandi (`mu_fraction`, default 0,9 = usa il 90%) [6]. Nel progetto il valore è salvato come `id_2nn` in `tuning_results.csv`, uno per `metric` (non dipende da `maxk`: usa solo i primi due vicini).

La dimensione intrinseca serve perché il volume di un intorno di raggio $r$ cresce come $r^d$: la densità stimata dai vicini dipende da $d$, non dal numero di colonne della matrice [3, 4].

### 2.3 Densità: PAk (Rodriguez et al. 2018)

Per ogni punto $i$:

- **Un intorno adattivo** $\hat k_i$: il più grande $k$ (fino a `maxk`) per cui un test di rapporto di verosimiglianza non rifiuta l'ipotesi che la densità sia costante nell'intorno. La severità del test è `alpha` (default DADApy $10^{-6}$) [5, 6].
- **La densità** con un modello in cui $\log \rho$ varia linearmente con l'indice del vicino, $\log \rho_l = F + a\, l$, stimato per massima verosimiglianza sui volumi $v_l$ dei gusci tra vicini consecutivi (volumi calcolati con la dimensione $d$):

$$
\mathcal{L}(F, a) = k F + a \frac{k(k+1)}{2} - \sum_{l=1}^{k} v_l\, e^{F + a l}, \qquad \log \rho_i = \hat F
$$

- **L'errore** $\sigma_i$ sulla stima di $\log \rho_i$: diminuisce quando $\hat k_i$ cresce, cioè dove l'intorno a densità costante è grande [5].

### 2.4 Picchi, sella e test di significatività (d'Errico et al. 2021)

Con $\log \rho_i$ e $\sigma_i$ [3]:

1. **Picchi candidati**: $i$ è un picco se $g_i = \log \rho_i - \sigma_i$ è il massimo nel suo intorno di $\hat k_i$ vicini (DADApy: `_find_density_modes`, codice 0.3.4). Usare $g$ invece di $\log \rho$ penalizza i picchi stimati male.
2. **Assegnazione**: ogni punto va al cluster del picco raggiunto passando per vicini sempre più densi, come in Rodriguez & Laio [1, 3].
3. **Punto di sella** tra i cluster $a$ e $b$: tra i punti di confine (un punto di $a$ con un vicino in $b$), quello con densità massima; ha densità $\log \rho_{ab}$ ed errore $\sigma_{ab}$ (docstring di `_find_borders_between_clusters`, DADApy 0.3.4).
4. **Test**: i due picchi restano separati solo se **entrambi** superano la sella di più di `Z` volte l'incertezza:

$$
\log \rho_a - \log \rho_{ab} \ \ge\ Z\,(\sigma_a + \sigma_{ab})
\qquad\text{e}\qquad
\log \rho_b - \log \rho_{ab} \ \ge\ Z\,(\sigma_b + \sigma_{ab})
$$

5. **Fusione**: se una coppia non supera il test, si fonde; si comincia dalla sella più alta, si ripete il test dopo ogni fusione, e sparisce il picco con il margine normalizzato $(\log \rho_c - \log \rho_{ab})/(\sigma_c + \sigma_{ab})$ più piccolo (DADApy 0.3.4, `_multimodality_test`).

Il risultato è una "topografia" dei dati: i picchi significativi e le selle che li separano [3].

**Cosa vuol dire `Z`.** È una soglia in unità di errore standard sulla differenza di log-densità: più è alta, più una valle deve essere profonda per tenere separati due picchi, quindi meno cluster [3, 6]. Il default di DADApy è 1,65, che coincide con il quantile 95% unilaterale della normale standard; che sia stato scelto per questo è un'interpretazione nostra, non dichiarata nella documentazione. `Z` non è un p-value calibrato: il test somma due errori standard (non le varianze) e si ripete su molte coppie. Anche questa è un'osservazione nostra sulla formula.

---

## 3. Il nostro contesto

- **Input**: matrici **grezze**, non embedding: lesione binaria (circa 220-270 mila voxel per soggetto), disconnettoma SDC voxelwise (circa 230-290 mila), SDC streamline (87 tratti) (`docs/guides/clustering.md`, `docs/guides/evaluation.md`). Circa 1500-5850 soggetti secondo la matrice.
- **Distanza**: `dice`, `jaccard` o `euclidean` (`ADP_METRICS`). Su una matrice continua ≥ 0 (SDC) `dice`/`jaccard` sono le versioni pesate (Czekanowski/Ruzicka), che su matrici 0/1 coincidono con le classiche (`docs/guides/clustering.md`).
- **Distanze esatte**: la matrice $N \times N$ intera è calcolata dal progetto (`pairwise_distance`) e a DADApy arrivano solo i `maxk` vicini (`Clustering(distances=(distanze, indici), maxk=...)`). Memoria: una matrice `float64` $N \times N$ per metrica, circa 270 MB a 5800 soggetti.
- **Righe a zero**: `dice`/`jaccard` non sono definite; quei soggetti prendono `-1` per ogni metrica. **Righe duplicate**: clusterizzate una volta, il gemello eredita l'etichetta (DADApy divide per la distanza dal primo vicino, che sarebbe 0).
- **Griglia attuale** (`params_clustering.json`, voce `adp`): `metric` ∈ {dice, euclidean} × `Z` ∈ {0,25 ... 16} (18 valori) = 36 combinazioni; `maxk = 100` fisso.
- **Ambiente**: `dadapy` dipende da `jax` e vive in `nemesis_fallback` (Python 3.11, `dadapy` 0.3.4, scikit-learn 1.9.1); l'import è lazy.

---

## 4. I parametri

Default verificati con `inspect.signature` su DADApy 0.3.4.

| Parametro | Dove | Significato | Default DADApy | Nel progetto |
|---|---|---|---|---|
| `Z` | `compute_clustering_ADP` | soglia di significatività per tenere separati due picchi (§2.4) | `1.65` | sweep 0,25-16; base 1,65 |
| `maxk` | `Clustering(...)` | numero massimo di vicini per soggetto: tetto di $\hat k_i$, quindi dell'intorno in cui si cercano picchi e bordi. Non entra nel 2NN, che usa solo i primi due vicini | `min(100, N-1)` (`base.py`) | `100`; deve essere minore del numero di righe distinte |
| `halo` | `compute_clustering_ADP` | marca come rumore i punti sotto la densità di bordo del loro cluster | `False` | `False` fisso |
| `v2` | `compute_clustering_ADP` | implementazione con meno memoria, più lenta | `False` | default |
| `alpha` | `compute_density_PAk` | severità del test che sceglie $\hat k_i$ | `1e-6` | default |
| `algorithm`, `mu_fraction` | `compute_id_2NN` | metodo del fit 2NN, quota dei $\mu$ usata | `"base"`, `0.9` | default |
| `metric` | progetto | distanza tra soggetti | — | `dice`, `euclidean` (anche `jaccard`) |

Fonti: documentazione e docstring di DADApy [6]; la pagina di `compute_clustering_ADP` descrive `Z` ("the higher the Z, the more aggressive the merging, the smaller the number of clusters"), non `maxk`, che è documentato nel docstring di `dadapy.base` [6].

**Conseguenza di `halo=False`**: ADP assegna ogni soggetto con distanza definita. Il `-1` nelle etichette del progetto viene solo dalle righe a zero, non da una decisione di densità.

---

## 5. Come si fa il tuning

`Z` è l'unica manopola, e la letteratura non fissa un valore giusto per un dato reale [3]. Il progetto quindi non cerca un ottimo ma la **dipendenza da `Z`**:

- `n_clusters_found` e `largest_cluster_share` (quota nel cluster più grande) al variare di `Z`, in scala logaritmica;
- `ari_vs_prev_z`: ARI [8] con la partizione al `Z` immediatamente più basso, sui soggetti clusterizzati. Un tratto vicino a 1 con `n_clusters_found` fisso è un **plateau**: lì la partizione non dipende dalla soglia;
- la tabella dei plateau: per ogni numero di cluster, il `Z` minimo e massimo che lo producono (nessuno script la produce: si ricava da `tuning_results.csv`);
- `n_small_clusters`: cluster con meno di 10 soggetti (`SMALL_CLUSTER_SIZE = 10` è una scelta del progetto, senza fonte);
- `metric` nella stessa run: le due partizioni si confrontano con l'ARI e con variabili esterne (es. `lesion_side`), non con la silhouette.

Il criterio del plateau è una scelta del progetto, coerente con l'idea che un cluster reale non debba dipendere da una piccola variazione della soglia. Guida ai grafici: [`clustering_tuning_guide.md`](../clustering_tuning_guide.md), "ADP".

---

## 6. Come si valuta l'output

- **Silhouette sulla stessa distanza** del clustering (`dice` o `euclidean`) [7]. Si legge **dopo** `pairs_at_distance_1`, la quota di coppie a distanza dice esattamente 1: sulle lesioni è l'84% e la silhouette resta vicina a 0 qualunque sia la struttura; sulle mappe SDC è lo 0,0015% e si legge normalmente (`docs/guides/evaluation.md`).
- **Purezza dei k vicini** (`knn_purity`): la quota dei vicini più prossimi nello stesso cluster, accanto al valore atteso per caso $(n_c - 1)/(n - 1)$. Usa solo l'ordine delle distanze, quindi non risente della saturazione. È in parte circolare: ADP costruisce i cluster proprio sui vicini.
- **CH e DB** solo con `euclidean` ([`evaluation_metrics.md`](evaluation_metrics.md), §3-4).
- **Nessuna statistica propria del modello** nel notebook di valutazione (sezione 3 saltata). La topografia di DADApy (densità dei picchi e delle selle) esiste nell'oggetto (`log_den_bord`) ma il progetto non la salva.

---

## 7. Quando usarlo

| Situazione | ADP |
|---|---|
| Matrice grezza ad alta dimensione, con una distanza non euclidea significativa (sovrapposizione `dice`) | sì: lavora sulle sole distanze e stima la densità con la dimensione intrinseca [3, 4] |
| Non si sa quanti cluster aspettarsi | sì, k emerge |
| Si vuole un criterio di fusione con un significato statistico | sì, `Z` è una soglia in unità di errore [3] |
| Servono soggetti di rumore | solo con `halo=True` (non usato dal progetto) |
| Embedding UMAP a poche dimensioni | possibile, ma la densità dell'embedding non è quella dei dati (§10) |
| Decine di migliaia di soggetti con distanze esatte | la matrice $N \times N$ pesa |

---

## 8. Pro e contro

**Pro**
- Un solo parametro, con un'interpretazione statistica [3].
- Non richiede coordinate: basta una distanza [6, 2].
- Densità stimata con un intorno adattivo e un errore per punto [5].
- Deterministico.
- Restituisce anche la dimensione intrinseca e la gerarchia dei picchi [2, 3].

**Contro**
- Una sola dimensione intrinseca per tutto il dataset: se sottogruppi hanno dimensioni diverse, la stima è un compromesso (lo stimatore 2NN assume $d$ costante [4]).
- PAk assume densità circa costante nell'intorno $\hat k_i$ [5].
- Con `halo=False` assegna tutti, anche i soggetti isolati.
- Distanze esatte $N \times N$: memoria e tempo quadratici (nel progetto).
- Ambiente separato per la dipendenza da `jax`.
- Poca letteratura applicativa rispetto ad agglomerativo e HDBSCAN; nessuna esperienza pubblicata nota al progetto su maschere di lesione.

---

## 9. Esempio

Due picchi $a$ e $b$ separati da una sella:

| | $\log \rho$ | $\sigma$ |
|---|---|---|
| picco $a$ | 5,0 | 0,3 |
| picco $b$ | 4,2 | 0,3 |
| sella $ab$ | 3,6 | 0,4 |

Margini: per $a$, $5{,}0 - 3{,}6 = 1{,}4$; per $b$, $4{,}2 - 3{,}6 = 0{,}6$. Incertezza di riferimento: $\sigma + \sigma_{ab} = 0{,}7$ per entrambi.

- **`Z = 0,5`**: soglia $0{,}35$. $1{,}4 \ge 0{,}35$ e $0{,}6 \ge 0{,}35$: **due cluster**.
- **`Z = 1,65`** (default): soglia $1{,}155$. $b$ non la supera ($0{,}6 < 1{,}155$): **un cluster**, $b$ è assorbito in $a$ (ha il margine normalizzato più piccolo, $0{,}6/0{,}7 = 0{,}86$ contro $2$).
- Il passaggio da due a un cluster avviene a $Z = 0{,}6/0{,}7 \approx 0{,}86$. In uno sweep, se il numero di cluster resta lo stesso tra 0,25 e 0,75 e poi cambia, il plateau è lì.

---

## 10. Insidie

1. **Distanza saturata.** Con `dice` sulle lesioni l'84% delle coppie è a distanza 1. Un soggetto che si sovrappone a meno di `maxk` altri ha, tra i suoi `maxk` vicini, molti soggetti a distanza esattamente 1, tutti a pari merito: i pareggi entrano nel rapporto $\mu$ del 2NN ($\mu = 1$ se primo e secondo vicino sono entrambi a 1) e nei volumi del PAk. Effetto sulla stima non verificato: è un ragionamento del progetto da controllare, non un risultato pubblicato.
2. **Silhouette inutilizzabile sulle lesioni** per la stessa saturazione (§6).
3. **`Z` letto come un p-value.** Non è calibrato (§2.4); va letto come una scala di severità e studiato per plateau.
4. **Silhouette tra metriche diverse.** Non si confrontano (`dice` ed `euclidean` hanno scale diverse).
5. **Il rumore non è rumore di densità.** Con `halo=False` il `-1` sono solo le righe a zero (§4).
6. **`maxk` vicino alla taglia dei cluster piccoli.** L'intorno $\hat k_i$ di un soggetto di un cluster piccolo può includere soggetti di altri cluster; con `maxk` alto la densità si liscia. Il progetto non lo sweepa: è un'osservazione nostra, non un risultato della fonte.
7. **ADP su un embedding.** UMAP non preserva del tutto la densità e può creare false fratture nei cluster [9]: una densità stimata in un embedding UMAP descrive l'embedding. Il progetto usa ADP sulle matrici grezze anche per questo; le etichette ADP proiettate su un UMAP 2D servono solo a vederle (`clustering_tuning_guide.md`, "ADP").
8. **La dimensione intrinseca su `dice`.** 2NN e PAk sono definiti su qualunque distanza, ma l'interpretazione di $d$ come dimensione di una varietà richiede che la distanza sia localmente euclidea [4]. Per `dice` su maschere binarie questo non è dimostrato: `id_2nn` va letto come un parametro della stima, non come una proprietà anatomica.

---

## Fonti

1. Rodriguez, A., Laio, A. (2014). Clustering by fast search and find of density peaks. *Science*, 344(6191), 1492-1496. doi:10.1126/science.1242072
2. Glielmo, A., Macocco, I., Doimo, D., Carli, M., Zeni, C., Wild, R., d'Errico, M., Rodriguez, A., Laio, A. (2022). DADApy: Distance-based analysis of data-manifolds in Python. *Patterns*, 3(10), 100589. doi:10.1016/j.patter.2022.100589
3. d'Errico, M., Facco, E., Laio, A., Rodriguez, A. (2021). Automatic topography of high-dimensional data sets by non-parametric density peak clustering. *Information Sciences*, 560, 476-492. doi:10.1016/j.ins.2021.01.010
4. Facco, E., d'Errico, M., Rodriguez, A., Laio, A. (2017). Estimating the intrinsic dimension of datasets by a minimal neighborhood information. *Scientific Reports*, 7, 12140. doi:10.1038/s41598-017-11873-y
5. Rodriguez, A., d'Errico, M., Facco, E., Laio, A. (2018). Computing the free energy without collective variables. *Journal of Chemical Theory and Computation*, 14(3), 1206-1215. doi:10.1021/acs.jctc.7b00916
6. Documentazione DADApy, *Clustering* e API: https://dadapy.readthedocs.io/en/latest/clustering.html; codice e docstring di DADApy 0.3.4 (`dadapy/clustering.py`, `dadapy/base.py`, `dadapy/density_estimation.py`, `dadapy/kstar.py`), ambiente `nemesis_fallback`
7. Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65. doi:10.1016/0377-0427(87)90125-7
8. Hubert, L., Arabie, P. (1985). Comparing partitions. *Journal of Classification*, 2(1), 193-218. doi:10.1007/BF01908075
9. Documentazione `umap-learn` (0.5), *Using UMAP for Clustering*: https://umap-learn.readthedocs.io/en/latest/clustering.html (copia in `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`)
