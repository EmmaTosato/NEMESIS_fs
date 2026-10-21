# t-SNE (t-distributed Stochastic Neighbor Embedding)

Indice dei metodi: [README.md](README.md). Implementazione nel repo: `tsne_embed` in `src/analysis/reduction.py`, cioè `sklearn.manifold.TSNE(**params)` di scikit-learn 1.8.0 (Barnes-Hut). Parametri in `config/registry/params_reduction.json` (chiave `tsne`). Una sintesi più breve è in [`../employed_dim_reduction_methods.md`](../employed_dim_reduction_methods.md).

## 1. Cosa fa

Mette ogni soggetto in un piano (2D, raramente 3D) in modo che i soggetti vicini nello spazio originale restino vicini nel piano. Lo fa convertendo le distanze in probabilità di "essere vicini" in entrambi gli spazi e spostando i punti del piano finché le due distribuzioni si somigliano [1]. È pensato per la **visualizzazione** [1, 2].

## 2. Perché lo fa: l'obiettivo matematico

**Spazio originale.** Per ogni punto *i* una gaussiana centrata su $\mathbf x_i$ dà la probabilità condizionata che *i* scelga *j* come vicino [1]:

$$
p_{j|i} = \frac{\exp\!\big(-d(\mathbf x_i,\mathbf x_j)^2 / 2\sigma_i^2\big)}{\sum_{k\neq i} \exp\!\big(-d(\mathbf x_i,\mathbf x_k)^2 / 2\sigma_i^2\big)} .
$$

La larghezza $\sigma_i$ è scelta, punto per punto, in modo che la distribuzione abbia una **perplexity** fissata dall'utente,

$$
\mathrm{Perp}(P_i) = 2^{H(P_i)}, \qquad H(P_i) = -\sum_j p_{j|i}\log_2 p_{j|i},
$$

che si legge come "numero effettivo di vicini" [1]. Le condizionate si simmetrizzano: $p_{ij} = (p_{j|i} + p_{i|j})/2n$ [1].

**Spazio ridotto.** Si usa una t di Student con un grado di libertà (code pesanti) [1]:

$$
q_{ij} = \frac{\big(1 + \|\mathbf y_i - \mathbf y_j\|^2\big)^{-1}}{\sum_{k\neq l}\big(1 + \|\mathbf y_k - \mathbf y_l\|^2\big)^{-1}} .
$$

Le code pesanti risolvono il *crowding problem*: in 2D non c'è spazio per tenere a distanza media tutti i punti moderatamente lontani, e la t permette di allontanarli senza grande costo [1]. In scikit-learn i gradi di libertà sono $\max(\text{n\_components}-1, 1)$, quindi 1 in 2D (sorgente installato, che cita van der Maaten 2009).

**Funzione di costo.** Si minimizza la divergenza di Kullback-Leibler per discesa del gradiente [1]:

$$
C = \mathrm{KL}(P\,\|\,Q) = \sum_{i\neq j} p_{ij}\log\frac{p_{ij}}{q_{ij}}, \qquad
\frac{\partial C}{\partial \mathbf y_i} = 4\sum_j (p_{ij}-q_{ij})(\mathbf y_i - \mathbf y_j)\big(1+\|\mathbf y_i-\mathbf y_j\|^2\big)^{-1}.
$$

Il termine $p_{ij}$ attrae i vicini, il termine $q_{ij}$ respinge tutti gli altri. KL è asimmetrica: mettere lontani due punti vicini costa molto, mettere vicini due punti lontani costa poco, per questo t-SNE conserva soprattutto il locale [1]. Il costo non è convesso: run diversi possono fermarsi in minimi diversi [1].

**Barnes-Hut** (van der Maaten 2014 [3]). Due approssimazioni portano il costo da $O(n^2)$ a $O(n\log n)$: $P$ si calcola solo sui vicini più prossimi (in scikit-learn $\min(n-1,\ \lfloor 3\cdot\text{perplexity}+1\rfloor)$), e le forze repulsive dei punti lontani si raggruppano con un quadtree, controllato dall'angolo $\theta$ [3, 4].

**Early exaggeration.** Nelle prime iterazioni le $p_{ij}$ sono moltiplicate per un fattore $\alpha$ (12 di default): i gruppi si formano e si separano prima della rifinitura [1, 4]. In scikit-learn questa fase dura 250 iterazioni (costante `_EXPLORATION_MAX_ITER` nel sorgente installato). Linderman & Steinerberger 2019 mostrano che in questa fase t-SNE si comporta come un clustering spettrale sul grafo dei vicini e separa i cluster ben distinti nei dati [5].

## 3. Il nostro contesto

- **Dati.** Matrici voxel-wise con $n \approx 5000$-5800 e $p \approx$ 220-260 mila; in tuning `metric` ∈ {`dice`, `euclidean`} (lesioni binarie) o solo `euclidean` (`params_reduction_sdc.json`, disconnettoma continuo).
- **Distanze precalcolate.** Il repo calcola una volta la matrice $n\times n$ delle distanze e passa `metric="precomputed"` (`src/analysis/distances.py`, `reduction.py::embed`); in quel caso forza `init="random"`, perché scikit-learn non accetta `init="pca"` su una matrice di distanze [4].
- **Le distanze vengono elevate al quadrato.** Nel percorso Barnes-Hut scikit-learn eleva al quadrato le distanze dei vicini qualunque sia la metrica (`distances_nn.data **= 2`, con il commento "Not sure of the implication of using a different metric"; sorgente installato). Per `euclidean` è la definizione del paper; per `dice` la gaussiana lavora su $d_\text{Dice}^2$. L'insieme dei vicini non cambia (trasformazione monotona), cambia la forma delle $p_{j|i}$.
- **Riferimento.** Thiebaut de Schotten et al. 2020 usano t-SNE in 2D con perplexity 30, exaggeration 12, learning rate 200 e 1000 iterazioni (scikit-learn 0.23) [6]; il materiale supplementare replica la figura a perplexity 40, 60 e 80 [6, Supplementary Figure 1]. Il repo fissa gli stessi valori e varia solo `perplexity` (scelta del progetto).
- **Solo 2D.** `n_components` è fisso a 2: Barnes-Hut non accetta più di 3 dimensioni [4]. Quindi un clustering a valle di t-SNE lavora su un embedding 2D, esattamente ciò che de Bodt et al. sconsigliano [7, §5 punto 10] (vedi §10).

## 4. I parametri

| Parametro | Cosa fa | Range tipico | Default scikit-learn 1.8 [4] | Nel repo |
|---|---|---|---|---|
| `perplexity` | numero effettivo di vicini; fissa $\sigma_i$ | 5-50 [1, 4]; con molti punti anche $n/100$ [8] | 30 | griglia 5, 15, 30, 50, 75, 100, 200; base 30 |
| `early_exaggeration` | fattore $\alpha$ della prima fase | "not very critical" [4]; fino a ~4 anche dopo la prima fase per dati molto grandi [8] | 12 | 12 |
| `learning_rate` | passo della discesa del gradiente | [10, 1000] [4] | `"auto"` = $\max(N/\alpha/4,\ 50)$ [4, 9] | 200 |
| `max_iter` | iterazioni totali | "almeno 250" [4] | 1000 | 1000 |
| `init` | posizione iniziale | `"pca"` o `"random"` | `"pca"` | `"random"` (forzato con le distanze precalcolate) |
| `metric` | distanza nello spazio originale | — | `"euclidean"` (interpretata come euclidea al quadrato) | `dice`, `euclidean`, sempre via `"precomputed"` |
| `method`, `angle` | Barnes-Hut e sua precisione $\theta$ | $\theta$ 0,2-0,8 [4] | `"barnes_hut"`, 0,5 | default |
| `random_state` | seed | — | `None` | 0 |

**Il learning rate del repo è circa il doppio dell'automatico.** Con $N = 5269$ e $\alpha = 12$, `"auto"` darebbe $5269/12/4 \approx 110$. Belkina et al. 2019 propongono $\eta = N/\alpha$ [9]; scikit-learn divide per 4 perché la sua definizione di learning rate è 4 volte quella di openTSNE/FIt-SNE ("our learning_rate=200 corresponds to learning_rate=800 in those other implementations") [4]. Kobak & Berens 2019 usano $\eta = n/12$ quando supera 200 [8]. Il valore 200 viene dal paper di riferimento [6], non da queste regole.

## 5. Come si fa il tuning

- **Perplexity**: l'unico parametro concettuale. Va provato più di un valore; nessuno è "quello giusto" [1, 2]. Il paper originale indica 5-50 come tipico [1]; Kobak & Berens, per dataset grandi, combinano 30 con $n/100$ (circa 50 per noi) [8]. La perplexity deve restare sotto il numero di punti [2, 4].
- **Learning rate e iterazioni**: se il costo resta alto o la mappa è una "palla" o una nube compressa, il learning rate è sbagliato [4, 9]. Wattenberg et al.: "iterate until reaching a stable configuration" [2].
- **Inizializzazione**: un'inizializzazione informata (PCA, scalata a deviazione standard piccola) conserva meglio la struttura globale di una casuale [8, 10].
- Il repo varia solo `perplexity`, nidificata per `metric`, e lascia fissi gli altri (`docs/dev/models.md`, `../dim_reduction_tuning_guide.md`).

## 6. Come si valuta l'output

- **Trustworthiness** a `k = 10` sulla stessa matrice di distanze usata per l'embedding (il punteggio del tuning; [evaluation.md](evaluation.md)).
- **Conservazione dei 10 vicini** e **correlazione delle distanze** sono le misure di [7, 8]; il repo non le calcola. Nei benchmark t-SNE ha la conservazione dei vicini più alta (0,20-0,46) e una correlazione delle distanze inferiore a PCA [7, Tabella 2].
- **`kl_divergence_`** (attributo di scikit-learn) è il costo finale: si confronta solo a parità di perplexity, perché $P$ cambia con la perplexity (conseguenza della definizione).
- **Stabilità**: stessa forma con seed diversi e a perplexity vicine [2].
- **Colori per metadati** (lato, volume, dataset) per riconoscere i confondenti [7, §5 punto 8].

## 7. Quando usarlo

- Per **vedere** i vicinati locali e gruppi discreti in 2D: è il metodo con la qualità locale più alta nei benchmark [7].
- Non come ingresso di un clustering (solo 2D, densità non conservate) né per leggere distanze tra gruppi [2, 7].
- Non per proiettare soggetti nuovi: il t-SNE non parametrico non ha una funzione di proiezione [7, §3.6].

## 8. Pro e contro

| Pro | Contro |
|---|---|
| Ottima conservazione dei vicini locali [7] | Distanze tra gruppi e dimensioni dei gruppi non hanno significato [2] |
| Separa bene cluster distinti [5] | Costo non convesso, risultato dipende da seed e inizializzazione [1, 10] |
| Un solo parametro concettuale (perplexity) [7, §5 punto 6] | Al massimo 3 dimensioni con Barnes-Hut [4] |
| Teoria della fase di exaggeration [5] | Struttura globale debole con inizializzazione casuale [10] |
| | Più lento di UMAP con molti punti e molte dimensioni [11] |

## 9. Un esempio semplice

Sei soggetti: tre con lesione nel territorio dell'arteria cerebrale media sinistra, tre in quello della destra. Con perplexity 2 ogni soggetto "vede" circa due vicini, che sono i due dello stesso lato: le $p_{ij}$ tra lati opposti sono quasi zero. t-SNE disegna due gruppetti separati. Se un lato avesse lesioni molto più simili tra loro (gruppo più denso), $\sigma_i$ si stringerebbe per tenere comunque due vicini effettivi: in 2D i due gruppetti avrebbero dimensioni simili anche se nei dati uno è molto più compatto. È la lezione "cluster sizes in a t-SNE plot mean nothing" [2].

## 10. Insidie note

Le sei lezioni di Wattenberg, Viégas & Johnson 2016 [2], con le conseguenze per il clustering:

1. **Gli iperparametri contano**: fuori dal range di perplexity "things get a little weird"; si guardano più valori [2].
2. **Le dimensioni dei cluster non significano nulla**: t-SNE adatta $\sigma_i$ alla densità locale, quindi espande i gruppi densi e contrae quelli radi [1, 2]. Un algoritmo a densità (HDBSCAN) sull'output vede densità **equalizzate**, non quelle dei dati.
3. **Le distanze tra cluster possono non significare nulla** [2]; de Bodt et al.: "in neighbor embeddings, between-cluster distances are not indicative of the high-dimensional between-cluster distances" [7, §5 punto 9]. K-means o un agglomerativo sull'output usano proprio quelle distanze.
4. **Il rumore non sempre sembra rumore**: dati casuali possono formare grumi a perplexity bassa [2]. Un cluster che compare a un solo valore di perplexity è sospetto.
5. **Le forme si leggono solo a volte** [2].
6. **Per la topologia servono più plot** [2].

Altre insidie documentate:

- **Separazione come conseguenza dei parametri.** Più repulsione (exaggeration bassa) dà cluster più discreti e separati, più attrazione dà strutture continue: la "netta separazione" di un t-SNE è in parte una scelta del punto sullo spettro attrazione-repulsione [12].
- **Inizializzazione.** Con `init="random"` (sempre il caso nel repo, per via delle distanze precalcolate) la struttura globale è meno affidabile; Kobak & Linderman mostrano che con la stessa inizializzazione informata t-SNE e UMAP conservano il globale in modo simile [10].
- **2D distorce comunque.** Chari & Pachter mostrano che ridurre a 2 dimensioni distorce inevitabilmente vicinati e distanze [13]; de Bodt et al.: "Do not perform downstream analysis on 2D embeddings" [7, §5 punto 10].
- **Clustering dopo t-SNE**: il dibattito e i controesempi sono in [`../challenge_of_clustering_after_dim_reduction.md`](../challenge_of_clustering_after_dim_reduction.md).

## Fonti

1. van der Maaten, L., Hinton, G. (2008). *Visualizing data using t-SNE.* Journal of Machine Learning Research 9: 2579-2605. https://jmlr.org/papers/v9/vandermaaten08a.html
2. Wattenberg, M., Viégas, F., Johnson, I. (2016). *How to Use t-SNE Effectively.* Distill. https://doi.org/10.23915/distill.00002
3. van der Maaten, L. (2014). *Accelerating t-SNE using tree-based algorithms.* Journal of Machine Learning Research 15: 3221-3245. https://jmlr.org/papers/v15/vandermaaten14a.html
4. scikit-learn 1.8, `sklearn.manifold.TSNE`. https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html (default e comportamento verificati anche sul sorgente installato).
5. Linderman, G. C., Steinerberger, S. (2019). *Clustering with t-SNE, provably.* SIAM Journal on Mathematics of Data Science 1(2): 313-332. https://doi.org/10.1137/18M1216134
6. Thiebaut de Schotten, M., Foulon, C., Nachev, P. (2020). *Brain disconnections link structural connectivity with function and behaviour.* Nature Communications 11. https://doi.org/10.1038/s41467-020-18920-9 (Methods, "Spatial embedding"; Supplementary Figure 1).
7. de Bodt, C., Diaz-Papkovich, A., Kobak, D. et al. (2025). *Low-dimensional embeddings of high-dimensional data.* arXiv:2508.15929 (in `knowledge/papers/methods/`).
8. Kobak, D., Berens, P. (2019). *The art of using t-SNE for single-cell transcriptomics.* Nature Communications 10: 5416. https://doi.org/10.1038/s41467-019-13056-x
9. Belkina, A. C., Ciccolella, C. O., Anno, R., Halpert, R., Spidlen, J., Snyder-Cappione, J. E. (2019). *Automated optimized parameters for T-distributed stochastic neighbor embedding improve visualization and analysis of large datasets.* Nature Communications 10: 5415. https://doi.org/10.1038/s41467-019-13055-y
10. Kobak, D., Linderman, G. C. (2021). *Initialization is critical for preserving global data structure in both t-SNE and UMAP.* Nature Biotechnology 39: 156-157. https://doi.org/10.1038/s41587-020-00809-z
11. McInnes, L., Healy, J., Melville, J. (2018). *UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction.* arXiv:1802.03426 (sezione sulle prestazioni e la scalabilità).
12. Böhm, J. N., Berens, P., Kobak, D. (2022). *Attraction-Repulsion Spectrum in Neighbor Embeddings.* Journal of Machine Learning Research 23(95): 1-32. https://jmlr.org/papers/v23/21-0055.html
13. Chari, T., Pachter, L. (2023). *The specious art of single-cell genomics.* PLoS Computational Biology 19(8): e1011288. https://doi.org/10.1371/journal.pcbi.1011288
