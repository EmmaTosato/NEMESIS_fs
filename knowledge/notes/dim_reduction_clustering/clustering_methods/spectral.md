# Spectral clustering

> Metodo a grafo: `"spectral"` in `CLUSTERING_METHODS` (`src/analysis/clustering.py`), implementato con `sklearn.cluster.SpectralClustering` (scikit-learn 1.8.0 nell'ambiente `nemesis`). Parametri in `config/registry/params_clustering.json`, voce `"spectral"`.
>
> Indice di tutti i metodi: [`README.md`](README.md). Metriche condivise (silhouette, Calinski-Harabasz, Davies-Bouldin, ARI, NMI): [`evaluation_metrics.md`](evaluation_metrics.md). L'eigengap, specifico di questo metodo, è definito qui.

## 1. Cosa fa

Trasforma i soggetti nei nodi di un **grafo di similarità** (un arco pesato tra soggetti simili), calcola alcuni autovettori del **Laplaciano** del grafo e usa quegli autovettori come nuove coordinate. In queste coordinate i gruppi ben connessi del grafo diventano gruppi compatti, che si separano facilmente con un passo finale di assegnazione (K-means o, nel progetto, `cluster_qr`) [1, 2, 3, 4].

Il vantaggio rispetto a K-means: conta come i soggetti sono **collegati** tra loro attraverso i vicini, non la loro distanza da un centro. Può quindi trovare gruppi non convessi, purché siano connessi al loro interno e poco connessi tra loro [3].

## 2. Perché lo fa: grafo, Laplaciano, autovettori

### Grafo di similarità

Sia $W$ la matrice $n \times n$ delle affinità ($w_{ij} \ge 0$, simmetrica) e $D$ la matrice diagonale dei gradi, $d_i = \sum_j w_{ij}$. scikit-learn costruisce $W$ in due modi tra quelli usati dal progetto [5, 6]:

- **`rbf`** (kernel Gaussiano):
$$
w_{ij} = \exp\!\left(-\gamma\, \lVert x_i - x_j \rVert^2\right),
$$
equivalente all'affinità di Ng, Jordan & Weiss $\exp(-\lVert x_i-x_j\rVert^2 / 2\sigma^2)$ con $\gamma = 1/(2\sigma^2)$ [2, 5]. Grafo completo: ogni coppia ha un peso, che decade con la distanza.
- **`nearest_neighbors`**: matrice di connettività dei `n_neighbors` vicini più vicini, $C_{ij} = 1$ se $j$ è tra i vicini di $i$, resa simmetrica come $W = \tfrac{1}{2}(C + C^\top)$ [5]. Nel codice di scikit-learn 1.8.0 il grafo include il punto stesso (`include_self=True`). I pesi valgono quindi 0, 0.5 (vicinanza in una sola direzione) o 1 (reciproca).

### Il taglio normalizzato (Shi & Malik)

Shi & Malik [1] definiscono il **normalized cut** di una divisione dei nodi in $A$ e $B$:

$$
\mathrm{Ncut}(A,B) = \frac{\mathrm{cut}(A,B)}{\mathrm{assoc}(A,V)} + \frac{\mathrm{cut}(A,B)}{\mathrm{assoc}(B,V)},
\qquad
\mathrm{cut}(A,B) = \sum_{i\in A,\, j \in B} w_{ij},
\quad
\mathrm{assoc}(A,V) = \sum_{i \in A,\, j \in V} w_{ij}.
$$

Minimizzarlo vuol dire tagliare pochi archi tra i gruppi **e** non isolare gruppetti piccoli (il denominatore penalizza un gruppo con poca connessione totale). Il problema esatto è NP-completo; il suo rilassamento continuo è un problema agli autovalori generalizzato, $(D - W)\,y = \lambda D\, y$ [1].

### Laplaciani

Von Luxburg [3] definisce:

$$
L = D - W, \qquad
L_{\mathrm{sym}} = I - D^{-1/2} W D^{-1/2}, \qquad
L_{\mathrm{rw}} = I - D^{-1} W .
$$

Proprietà chiave [3]: la molteplicità dell'autovalore 0 di $L$ (e dei due Laplaciani normalizzati) è uguale al **numero di componenti connesse** del grafo. Se il grafo è fatto di $k$ blocchi senza archi tra loro, i primi $k$ autovalori valgono esattamente 0 e i loro autovettori indicano i blocchi. Se tra i blocchi ci sono pochi archi deboli, i primi $k$ autovalori sono piccoli ma non nulli: la teoria delle perturbazioni dice che gli autovettori restano vicini a quelli ideali [3].

### L'algoritmo di Ng, Jordan & Weiss

Quello implementato, nella sostanza, da scikit-learn [2, 5]:

1. costruisci $W$ e calcola $D^{-1/2} W D^{-1/2}$ (equivalentemente $L_{\mathrm{sym}}$);
2. prendi i $k$ autovettori corrispondenti ai $k$ autovalori più piccoli di $L_{\mathrm{sym}}$ e mettili come colonne di $U \in \mathbb{R}^{n \times k}$;
3. normalizza ogni riga di $U$ a norma 1 (in Ng-Jordan-Weiss);
4. clusterizza le righe con K-means: la riga $i$ è il soggetto $i$.

scikit-learn usa `spectral_embedding` con il Laplaciano normalizzato e tiene anche il primo autovettore (`drop_first=False`, letto nel codice installato). Il passo 4 è scelto da `assign_labels` [5]:

- `kmeans` (default): K-means sugli autovettori, sensibile all'inizializzazione;
- `discretize`: discretizzazione di Yu & Shi, meno sensibile all'inizializzazione;
- `cluster_qr`: estrae i cluster direttamente dagli autovettori con una fattorizzazione QR con pivoting (Damle, Minden & Ying [7]); **nessun parametro, nessuna iterazione**.

### Eigengap

La regola di von Luxburg [3, sez. 8.3]: scegliere $k$ tale che i primi $k$ autovalori $\lambda_1, \dots, \lambda_k$ siano piccoli e $\lambda_{k+1}$ sia relativamente grande:

$$
\hat{k} = \arg\max_{k} \; (\lambda_{k+1} - \lambda_k), \qquad 0 = \lambda_1 \le \lambda_2 \le \dots
$$

La giustificazione è la proprietà delle componenti connesse sopra. Von Luxburg avverte che la regola funziona bene quando i gruppi sono ben separati, e diventa poco affidabile quando sono rumorosi o sovrapposti [3].

## 3. Il nostro contesto

- **Input**: embedding UMAP (2, 3, 10 componenti) o score PCA, circa 1570-5845 soggetti. Le run di tuning registrate in `results/{lesion,sdc}/clustering/tuning/spectral/runs_tuning.csv` sono tutte su embedding UMAP (metrica UMAP `euclidean`; per le lesioni anche `dice`); lo spectral lavora comunque in distanza euclidea sulle coordinate dell'embedding.
- **`gamma` dipende dalla scala dell'embedding.** Misura fatta per questa nota sull'UMAP a 2 componenti di `s2.2-vol` (1570 soggetti, `results/sdc/dim_reduction/production/umap/07-09_s2.2-vol_m_euclidean_nc2`): la distanza al quadrato mediana tra due soggetti è circa 25.9. Quota di coppie con affinità sotto $10^{-6}$: 7% con $\gamma=0.1$, 66% con $\gamma=1$, 89% con $\gamma=5$. Lo stesso $\gamma$ su uno spazio PCA, con scala diversa, costruisce un grafo diverso: i valori della griglia non sono trasferibili tra embedding.
- **Memoria**: `rbf` costruisce una matrice densa $n \times n$ in `float64`, circa 273 MB a 5845 soggetti; `nearest_neighbors` una matrice sparsa.
- **Embedding UMAP e connettività**: UMAP può creare false separazioni dentro un gruppo vero [9]. Con un grafo `nearest_neighbors` a `n_neighbors` piccolo, isole separate dell'embedding diventano componenti connesse distinte, e lo spectral le separa per costruzione. scikit-learn avvisa quando il grafo non è connesso.
- **Determinismo**: con `assign_labels="cluster_qr"` e il solutore di default (`arpack`), `random_state` fissa solo il vettore di partenza di ARPACK (letto nel codice installato), che non cambia gli autovettori a cui si converge. Il risultato è in pratica deterministico. In una prova su dati sintetici per questa nota (2000 punti, 4 gruppi, `nearest_neighbors`, 50 vicini) sei semi hanno dato partizioni identiche (ARI 1.0). Conseguenza: le diagnostiche basate su ripetizioni a semi diversi (RSC) non vedono variabilità ([`evaluation_metrics.md`](evaluation_metrics.md), sezione 7).

## 4. Parametri

Default verificati con `inspect.signature(SpectralClustering)` su scikit-learn 1.8.0. "Progetto" è il valore in `params_clustering.json` (scelta del progetto).

| Parametro | Significato [5] | Range | Default sklearn | Progetto |
|---|---|---|---|---|
| `n_clusters` | Dimensione del sottospazio di proiezione (numero di cluster). | intero $\ge 2$ | 8 | base 6; griglia 2-30 |
| `affinity` | Come costruire $W$: `rbf`, `nearest_neighbors`, `precomputed`, `precomputed_nearest_neighbors`, o un kernel di `pairwise_kernels`. | stringa o callable | `rbf` | base `rbf`; griglia `nearest_neighbors`, `rbf` |
| `gamma` | Coefficiente del kernel `rbf`; ignorato con `nearest_neighbors`. | float $>0$ | 1.0 | base 1.0; griglia 0.1, 1.0, 5.0 |
| `n_neighbors` | Vicini del grafo `nearest_neighbors`; ignorato con `rbf`. | intero | 10 | griglia 10, 30, 50 |
| `assign_labels` | Assegnazione finale: `kmeans`, `discretize`, `cluster_qr`. | 3 stringhe | `kmeans` | `cluster_qr` |
| `n_components` | Numero di autovettori; se `None` vale `n_clusters`. | intero o `None` | `None` | default |
| `eigen_solver` | `arpack`, `lobpcg`, `amg`; `None` usa `arpack`. | stringa o `None` | `None` | default |
| `n_init` | Inizializzazioni del K-means finale; usato solo con `assign_labels="kmeans"`. | intero | 10 | non usato |
| `random_state` | Seme per l'inizializzazione di `lobpcg`/`amg` e del K-means finale. | intero o `None` | `None` | 0 |

La sweep è *affinity-aware* (`run_spectral_affinity_aware_sweep`, `src/analysis/clustering_tuning.py`): `n_neighbors` si prova solo con `nearest_neighbors` e `gamma` solo con `rbf`, perché scikit-learn ignora in silenzio il parametro che non si applica. Totale: $29 \times (3 + 3) = 174$ fit.

## 5. Come si fa il tuning

1. **Prima il grafo, poi $k$.** La scelta di `affinity` e del suo iperparametro decide quale struttura lo spectral può vedere. Von Luxburg raccomanda il grafo $k$-nearest-neighbor come prima scelta, con un numero di vicini dell'ordine di $\log n$ come punto di partenza ($\log 5845 \approx 8.7$), e di controllare che il grafo sia connesso [3]. Per il kernel Gaussiano suggerisce una $\sigma$ dell'ordine della distanza media di un punto dal suo $k$-esimo vicino [3].
2. **Eigengap** (`eigengap_affinity=<affinity>.png`, un pannello per valore di `n_neighbors` o `gamma`): $\hat k$ è dove cade il salto più grande tra autovalori consecutivi. Lettura: `clustering_tuning_guide.md`, "Spectral - eigengap".
3. **Indici geometrici per `n_clusters`**: silhouette, CH, DB in `tuning_plot.png`, una linea per combinazione (`affinity`, iperparametro). Definizioni: [`evaluation_metrics.md`](evaluation_metrics.md).
4. **Self-tuning** (Zelnik-Manor & Perona [8]), funzione post-hoc `compute_self_tuning_eigengap`, non collegata alla pipeline: ogni punto ha la sua scala $\sigma_i$, la distanza dal suo 7° vicino, e
$$
w_{ij} = \exp\!\left(-\frac{\lVert x_i - x_j\rVert^2}{\sigma_i\,\sigma_j}\right).
$$
Toglie `gamma` dalla sweep: se l'eigengap self-tuning indica lo stesso $k$ della griglia, la scelta di `gamma` non era decisiva.
5. **Stabilità del numero di cluster** (opzionale, blocco `"consensus"`): [`evaluation_metrics.md`](evaluation_metrics.md), sezione 7. Con `cluster_qr` la stabilità rispetto al seme è quasi sempre perfetta per costruzione (sezione 3): è informativa solo la versione su sottocampioni (Monti).

## 6. Come si valuta l'output

- **Eigengap** come criterio interno del metodo: riflette la connettività del grafo che lo spectral usa davvero [3].
- **Indici geometrici**: `compute_clustering_metrics` li calcola in distanza euclidea su $X$ (accetta `rbf` e `nearest_neighbors` come compatibili). Lo spectral però raggruppa per connettività nel grafo: un gruppo allungato ma ben connesso può avere una silhouette euclidea bassa pur essendo un buon cluster per il metodo. Gli indici vanno letti come confronto tra combinazioni, non come giudizio assoluto ([`evaluation_metrics.md`](evaluation_metrics.md)).
- **Connettività**: un avviso "graph is not fully connected" significa che parte dei cluster è determinata da componenti già separate nel grafo.
- **Dimensioni dei cluster**: il normalized cut penalizza gruppi molto piccoli [1]; cluster tutti di dimensione simile sono un effetto atteso del criterio, non necessariamente dei dati.

## 7. Quando usarlo

- Quando i gruppi sono **connessi ma non convessi** (forme allungate o curve), dove K-means e GMM falliscono [3].
- Quando si vuole un criterio interno per $k$ legato alla struttura del grafo (eigengap) [3].
- Non quando la scala è difficile da fissare e il grafo cambia molto con `gamma`/`n_neighbors`, o quando molti soggetti dovrebbero restare non assegnati: lì [`hdbscan.md`](hdbscan.md) o [`adp.md`](adp.md).

## 8. Pro e contro

**Pro**
- Trova gruppi non convessi, purché connessi [3].
- Fondamento chiaro: rilassamento del normalized cut [1], proprietà degli autovalori del Laplaciano [3].
- Con `cluster_qr` l'assegnazione finale è deterministica e senza parametri [7].
- L'eigengap dà un'indicazione su $k$ interna al metodo [3].

**Contro**
- Dipende molto dalla costruzione del grafo (`gamma`, `n_neighbors`) [3], e quei valori dipendono dalla scala dei dati.
- $k$ va comunque fissato in anticipo.
- Costo in memoria del grafo denso con `rbf` ($O(n^2)$).
- L'eigengap è affidabile solo con gruppi ben separati [3].
- Ogni soggetto riceve un'etichetta: nessuna classe "rumore".

## 9. Esempio semplice

Quattro soggetti in due coppie: $a$-$b$ con peso 1, $c$-$d$ con peso 1, e un solo arco debole $b$-$c$ con peso 0.1.

$$
W = \begin{pmatrix} 0 & 1 & 0 & 0 \\ 1 & 0 & 0.1 & 0 \\ 0 & 0.1 & 0 & 1 \\ 0 & 0 & 1 & 0 \end{pmatrix}
$$

Gli autovalori di $L_{\mathrm{sym}}$ (calcolati con `scipy.sparse.csgraph.laplacian(W, normed=True)`) sono $0,\; 0.091,\; 1.909,\; 2$. Il salto più grande è tra il secondo e il terzo: eigengap $\Rightarrow k=2$, le due coppie.

Senza l'arco $b$-$c$ il grafo ha due componenti connesse e gli autovalori diventano $0,\; 0,\; 2,\; 2$: lo zero ha molteplicità 2, esattamente il numero di componenti [3].

## 10. Insidie

- **`gamma` non è trasferibile** tra embedding o sessioni: con $\gamma=1$ su un UMAP 2D due terzi delle coppie hanno affinità praticamente nulla (sezione 3).
- **Un solo parametro del grafo per volta**: `n_neighbors` con `rbf`, o `gamma` con `nearest_neighbors`, vengono ignorati senza errore [5]. La sweep del progetto lo evita.
- **Grafo non connesso**: le componenti connesse diventano cluster per forza [3]. Su UMAP, se le isole sono false separazioni [9], lo spectral le conferma.
- **Eigengap del progetto e grafo di sklearn non coincidono del tutto**: `compute_eigengap` costruisce il grafo `nearest_neighbors` con `include_self=False`, mentre `SpectralClustering` usa `include_self=True` (codice di scikit-learn 1.8.0). La diagonale di $W$ cambia, quindi gli autovalori del plot sono di un grafo leggermente diverso da quello clusterizzato.
- **`cluster_qr` rende le ripetizioni identiche**: ripetere lo spectral a semi diversi non produce diversità tra ripetizioni, quindi l'RSC non dice nulla ([`evaluation_metrics.md`](evaluation_metrics.md), sezione 7).
- **Indici euclidei su un metodo a grafo**: possono sottovalutare cluster non convessi (sezione 6).

## Fonti

1. Shi, J., Malik, J. (2000). *Normalized cuts and image segmentation.* IEEE Transactions on Pattern Analysis and Machine Intelligence, 22(8), 888-905. doi:10.1109/34.868688.
2. Ng, A. Y., Jordan, M. I., Weiss, Y. (2001). *On spectral clustering: analysis and an algorithm.* Advances in Neural Information Processing Systems 14, 849-856. https://proceedings.neurips.cc/paper/2001/hash/801272ee79cfde7fa5960571fee36b9b-Abstract.html.
3. von Luxburg, U. (2007). *A tutorial on spectral clustering.* Statistics and Computing, 17(4), 395-416. doi:10.1007/s11222-007-9033-z.
4. Dinh, T., Hauchi, W., Lisik, D., et al. (2025). *Data clustering: an essential technique in data science.* Expert Systems with Applications; arXiv:2412.18760 (elenca spectral clustering tra le opzioni di selezione dell'algoritmo e cita Ng et al. 2001). Copia locale: `knowledge/papers/methods/Dinh et al - 2025 - Data clustering an essential technique in data science/`.
5. scikit-learn 1.8, `sklearn.cluster.SpectralClustering`. https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.SpectralClustering.html (default verificati con `inspect.signature`; costruzione del grafo `nearest_neighbors`, `drop_first=False` e seme di ARPACK letti nel codice installato).
6. scikit-learn 1.8, guida utente "Spectral clustering". https://scikit-learn.org/1.8/modules/clustering.html#spectral-clustering.
7. Damle, A., Minden, V., Ying, L. (2019). *Simple, direct and efficient multi-way spectral clustering.* Information and Inference, 8(1), 181-203. doi:10.1093/imaiai/iay008.
8. Zelnik-Manor, L., Perona, P. (2004). *Self-tuning spectral clustering.* Advances in Neural Information Processing Systems 17, 1601-1608. https://papers.nips.cc/paper/2619-self-tuning-spectral-clustering.
9. McInnes, L., et al. *UMAP documentation: Using UMAP for clustering.* https://umap-learn.readthedocs.io/en/latest/clustering.html (copia locale: `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`).
