# UMAP (Uniform Manifold Approximation and Projection)

Indice dei metodi: [README.md](README.md). Implementazione nel repo: `umap_embed` in `src/analysis/reduction.py`, cioè `umap.UMAP(**params)` di `umap-learn` 0.5.12. Parametri in `config/registry/params_reduction.json` e `params_reduction_sdc.json` (chiave `umap`). Il criterio con cui il progetto legge le griglie `n_neighbors` × `min_dist` è in [`../employed_dim_reduction_methods.md`](../employed_dim_reduction_methods.md), "Scegliere `n_neighbors` e `min_dist` di UMAP guardando le griglie": qui non si ripete.

## 1. Cosa fa

Costruisce un grafo pesato dei *k* vicini più prossimi di ogni soggetto, poi cerca una disposizione in poche dimensioni il cui grafo equivalente somigli il più possibile a quello originale: punti collegati si attraggono, gli altri si respingono [1, 2]. A differenza di t-SNE scala bene con il numero di dimensioni dell'embedding, quindi si usa anche per produrre 5-10 coordinate da dare a un clustering [2, 3].

## 2. Perché lo fa: l'obiettivo matematico

La giustificazione del paper viene dalla teoria dei *fuzzy simplicial set* [1]; in pratica l'algoritmo ha tre passi.

**Grafo nello spazio originale.** Per ogni punto *i*, con i suoi *k* = `n_neighbors` vicini $i_1,\dots,i_k$ e la distanza $d$ scelta (`metric`) [1]:

$$
\rho_i = \min_{j} d(\mathbf x_i, \mathbf x_{i_j}), \qquad
\sum_{j=1}^{k} \exp\!\left(-\frac{\max\big(0,\ d(\mathbf x_i,\mathbf x_{i_j}) - \rho_i\big)}{\sigma_i}\right) = \log_2 k ,
$$

dove $\rho_i$ garantisce che ogni punto sia collegato almeno al primo vicino e $\sigma_i$ normalizza la scala locale (è risolto per bisezione, `smooth_knn_dist` nel sorgente). Il peso dell'arco orientato è $v_{j|i} = \exp\!\big(-\max(0, d_{ij}-\rho_i)/\sigma_i\big)$, e i due versi si uniscono con l'unione fuzzy [1]:

$$
v_{ij} = v_{j|i} + v_{i|j} - v_{j|i}\, v_{i|j}.
$$

**Grafo nell'embedding.** La somiglianza tra due punti dell'embedding è [1]

$$
w_{ij} = \big(1 + a\,\|\mathbf y_i - \mathbf y_j\|^{2b}\big)^{-1},
$$

con $a, b$ stimati in modo che la curva approssimi 1 fino a `min_dist` e un decadimento esponenziale con scala `spread` oltre (`find_ab_params` nel sorgente). Con $a = b = 1$ è il nucleo di Cauchy di t-SNE.

**Costo.** La cross-entropia tra i due insiemi di pesi [1]:

$$
\mathcal L = \sum_{i \neq j} \left[ v_{ij}\log\frac{v_{ij}}{w_{ij}} + (1-v_{ij})\log\frac{1-v_{ij}}{1-w_{ij}} \right].
$$

Il primo termine è l'attrazione tra vicini, il secondo la repulsione tra non vicini. Si ottimizza con discesa del gradiente stocastica: gli archi sono campionati in proporzione al peso, e la repulsione è stimata su pochi punti presi a caso (*negative sampling*, `negative_sample_rate`) [1]. L'inizializzazione di default è lo spectral embedding del grafo (`init="spectral"`) [1, 4].

**Cosa ottimizza davvero.** Damrich & Hamprecht 2021 mostrano che, per via del negative sampling, UMAP non minimizza la cross-entropia scritta sopra ma un costo effettivo diverso, con una repulsione molto più debole [5]. Böhm, Berens & Kobak 2022 arrivano alla stessa conclusione da un'altra strada: UMAP si comporta come un t-SNE con exaggeration elevata (più attrazione), cioè sta in un altro punto dello stesso spettro attrazione-repulsione [6].

## 3. Il nostro contesto

- **Dati.** Lesioni binarie voxel-wise ($n$ = 5269-5845, $p \approx$ 220-260 mila) con `metric` ∈ {`dice`, `euclidean`}; disconnettoma continuo con `euclidean` (`params_reduction_sdc.json`).
- **Distanze precalcolate.** Il repo calcola una volta la matrice $n\times n$ e passa `metric="precomputed"`: così il grafo dei vicini è **esatto**. Senza, sopra 4096 punti `umap-learn` passa alla ricerca approssimata (NN-descent); la soglia è nel sorgente (`X[index].shape[0] < 4096`), non nella documentazione. Misure e motivazione: [`docs/dev/models.md`](../../../../docs/dev/models.md), `embed`.
- **Euclidea su maschere binarie misura il volume.** Per due maschere $A, B$ la distanza euclidea al quadrato è il numero di voxel in cui differiscono, $|A| + |B| - 2|A\cap B|$ (identità algebrica sui vettori 0/1): due lesioni piccole sono vicine anche se non si toccano, due lesioni grandi nello stesso posto restano lontane. Dice attenua ma non elimina la dipendenza dal volume (`employed_dim_reduction_methods.md`, "Il bias-volume di jaccard/dice").
- **Uso a valle.** L'embedding (2, 3 o 10 componenti) è l'ingresso di `clustering.py`. La documentazione `umap-learn` indica proprio questo uso come possibile, "somewhat controversial", da fare "with care" [3].
- **Riferimento.** Talozzi et al. 2023 usano UMAP con i parametri di default ("an approximation of 15 neighbours and a minimum 0.1 Euclidean distance") per un embedding 2D dei disconnettomi [7].

## 4. I parametri

| Parametro | Cosa fa | Range indicato | Default `umap-learn` 0.5.12 | Nel repo (lesione / SDC) |
|---|---|---|---|---|
| `n_neighbors` | dimensione del vicinato: basso = dettaglio locale, alto = struttura più globale [2] | la documentazione esplora 2-200 [2] | 15 [2] | base 5 / 15; griglia 5, 15, 30, 50, 100 |
| `min_dist` | quanto stretti possono stare i punti nell'embedding; agisce solo sul layout [2] | 0,0-0,99 [2]; deve essere ≤ `spread` (controllo nel sorgente) | 0,1 [2] | base 0,0; griglia 0,0, 0,01, 0,05, 0,1, 0,5, 1,0 |
| `n_components` | dimensioni dell'embedding | 2-3 per vedere; "10, or 50" per clustering o machine learning [2] | 2 | griglia 2, 3, 10 |
| `metric` | distanza nello spazio originale | euclidean, manhattan, cosine, hamming, ..., `precomputed` [2] | `"euclidean"` | `dice`, `euclidean`, sempre via `precomputed` |
| `n_epochs` | epoche di ottimizzazione | — | `None`: 500 se $n \le 10000$, altrimenti 200 (sorgente) | default (quindi 500) |
| `init` | inizializzazione | `spectral`, `pca`, `random`, `tswspectral` | `"spectral"` | default |
| `spread`, `learning_rate`, `negative_sample_rate`, `local_connectivity`, `set_op_mix_ratio`, `repulsion_strength` | scala del layout, passo, campioni negativi, connettività locale, unione/intersezione fuzzy, peso della repulsione | — | 1,0; 1,0; 5; 1,0; 1,0; 1,0 | default |
| `densmap` | aggiunge un termine che conserva la densità locale [8] | — | `False` | non usato |
| `random_state` | seed; impostarlo spegne il multithreading [9] | — | `None` | 0 |

Default verificati sulla firma installata di `umap.UMAP.__init__`. La riproducibilità esatta richiede `random_state`: "by setting a `random_state` we are effectively turning off any of the multi-threading" [9].

## 5. Come si fa il tuning

- **`n_neighbors`** è il parametro più importante: bilancia locale e globale [2]. Per il clustering la documentazione consiglia valori più alti di quelli da visualizzazione, perché valori piccoli producono strutture fini che possono essere rumore (nell'esempio MNIST usa 30) [3].
- **`min_dist`** per il clustering va tenuto basso (l'esempio usa 0) perché si vuole impacchettare i punti densamente [3]. Un `min_dist` basso rende però i gruppi netti per costruzione: nel progetto si accetta solo se la stessa struttura resta a `min_dist` vicini (criterio del plateau, `employed_dim_reduction_methods.md`).
- **`n_components`**: "in general you should explore different embedding dimension options" [3]. de Bodt et al. considerano il clustering su embedding a 5-10 dimensioni una pratica emergente che richiede ancora validazione [10, §6.1]. Nel repo `n_components` è nidificato perché la trustworthiness non si confronta tra dimensioni diverse ([`../dim_reduction_tuning_guide.md`](../dim_reduction_tuning_guide.md), "guadagno marginale").
- **`metric`**: scelta di dominio [10, §5 punto 3]; nel repo `dice` contro `euclidean` sulle lesioni.
- **Seed**: più seed per la stessa combinazione, perché il costo non è convesso [10, §6.1].

## 6. Come si valuta l'output

- **Trustworthiness** a `k = 10` sulla stessa matrice di distanze dell'embedding (punteggio del tuning; [evaluation.md](evaluation.md)). Non confrontabile tra `n_components` diversi.
- **`plot_hdbscan`**: numero di cluster e quota di rumore di HDBSCAN su ogni combinazione, letti come sonda di stabilità tra celle vicine della griglia (`../dim_reduction_tuning_guide.md`).
- **Gemello 2D**: un embedding a più componenti si guarda solo con un fit separato a `n_components=2` con gli stessi iperparametri, mai con le prime due colonne (`lessons_learned.md` #16).
- **Non calcolati nel repo**: continuity, conservazione dei *k* vicini, correlazione delle distanze. Nei benchmark di de Bodt et al. UMAP in 2D ha una conservazione dei 10 vicini (0,14-0,25) inferiore a t-SNE e superiore a PCA [10, Tabella 2].

## 7. Quando usarlo

- Per un **embedding a più di 2-3 dimensioni** da dare a un clustering a densità: è il caso d'uso che la documentazione tratta esplicitamente, con le cautele del §10 [3, 4].
- Per la **visualizzazione**, accanto a t-SNE: UMAP forma cluster più compatti e grandi, t-SNE più piccoli e numerosi [10, §4].
- Per una **metrica non euclidea** (Dice, precomputata): UMAP accetta qualunque distanza [2].
- Non per leggere distanze tra gruppi o densità relative (§10).

## 8. Pro e contro

| Pro | Contro |
|---|---|
| Scala bene con `n_components` e con *n* [2, 4] | Non conserva la densità [3, 4] |
| Qualunque metrica, anche precomputata [2] | Può creare "false tears": cluster più fini di quelli presenti nei dati [3] |
| Inizializzazione spettrale di default, che aiuta la struttura globale [11] | Costo non convesso e stocastico [10, §6.1] |
| Può proiettare punti nuovi (`transform`) [4] | Il costo ottimizzato non è quello dichiarato [5] |
| | Con `random_state` fissato è single-thread [9] |

## 9. Un esempio semplice

Quattro soggetti su una retta, alle posizioni 0, 1, 2 e 10, con `n_neighbors = 2` (ogni punto e il suo vicino più prossimo). Per il punto 0: $\rho_0 = 1$ (distanza da 1), quindi l'arco 0-1 ha peso $\exp(0) = 1$. Per il punto 10 il vicino più prossimo è 2, a distanza 8: anche lì $\rho_{10} = 8$ e l'arco 10-2 ha peso 1. Nel grafo il punto isolato è collegato con la stessa forza dei punti fitti: UMAP **normalizza la scala locale**, e nell'embedding il 10 non resta "lontano 8 volte" ma vicino al 2. È il meccanismo per cui UMAP non conserva la densità [3, 4].

## 10. Insidie note

- **Densità non conservata.** La costruzione del grafo uniforma la densità locale (§9); "UMAP, like t-SNE, does not completely preserve density" [3]. Un algoritmo a densità sull'output (HDBSCAN) vede le densità del layout, non quelle dei dati. densMAP è la variante pensata per correggerlo [8].
- **False tears.** UMAP "can also create false tears in clusters, resulting in a finer clustering than is necessarily present in the data" [3]. Un cluster spezzato a `n_neighbors` basso e unito a valori più alti è il segnale tipico.
- **Distanze tra cluster.** La FAQ di `umap-learn` dichiara come obiettivo che la distanza tra cluster sia significativa [4]; de Bodt et al., con McInnes tra gli autori, scrivono invece che nei neighbor embedding "between-cluster distances are not indicative of the high-dimensional between-cluster distances" [10, §5 punto 9]. Nel progetto vale la lettura prudente: le distanze tra gruppi non si interpretano. Le dimensioni dei gruppi nemmeno [12].
- **La struttura globale viene dall'inizializzazione.** Kobak & Linderman 2021: il vantaggio di UMAP su t-SNE nel conservare il globale dipende dall'inizializzazione spettrale, non dal costo; con `init="random"` UMAP perde la struttura globale come t-SNE [11].
- **Compattezza come conseguenza dei parametri.** UMAP sta dal lato "attrazione forte" dello spettro: cluster compatti e separati sono in parte effetto del metodo, non solo dei dati [6].
- **Circolarità con `min_dist` basso.** Gruppi più netti danno indici di validazione migliori al clustering a valle, senza che la struttura sia più vera (`../challenge_of_clustering_after_dim_reduction.md`, §4 e §7).
- **K-means sull'output.** La FAQ: "Since UMAP does not necessarily produce clean spherical clusters something like K-Means is a poor choice"; consiglia HDBSCAN [4].
- **2D per analisi a valle.** de Bodt et al.: "Do not perform downstream analysis on 2D embeddings" [10, §5 punto 10]; Chari & Pachter documentano distorsioni inevitabili in 2D [13].
- **Mai le prime colonne.** Le dimensioni di UMAP non hanno un ordine di importanza (`lessons_learned.md` #16).

## Fonti

1. McInnes, L., Healy, J., Melville, J. (2018). *UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction.* arXiv:1802.03426. https://arxiv.org/abs/1802.03426
2. umap-learn, *Basic UMAP Parameters*. https://umap-learn.readthedocs.io/en/latest/parameters.html
3. umap-learn, *Using UMAP for Clustering*. https://umap-learn.readthedocs.io/en/latest/clustering.html (copia in `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`).
4. umap-learn, *Frequently Asked Questions* e *How UMAP Works*. https://umap-learn.readthedocs.io/en/latest/faq.html, https://umap-learn.readthedocs.io/en/latest/how_umap_works.html
5. Damrich, S., Hamprecht, F. A. (2021). *On UMAP's true loss function.* Advances in Neural Information Processing Systems 34 (NeurIPS 2021). arXiv:2103.14608. https://arxiv.org/abs/2103.14608
6. Böhm, J. N., Berens, P., Kobak, D. (2022). *Attraction-Repulsion Spectrum in Neighbor Embeddings.* Journal of Machine Learning Research 23(95): 1-32. https://jmlr.org/papers/v23/21-0055.html
7. Talozzi, L. et al. (2023). *Latent disconnectome prediction of long-term cognitive-behavioural symptoms in stroke.* Brain 146(5). https://doi.org/10.1093/brain/awad013 (in `knowledge/papers/stroke_core/`), Methods.
8. Narayan, A., Berger, B., Cho, H. (2021). *Assessing single-cell transcriptomic variability through density-preserving data visualization.* Nature Biotechnology 39: 765-774. https://doi.org/10.1038/s41587-020-00801-7
9. umap-learn, *UMAP Reproducibility*. https://umap-learn.readthedocs.io/en/latest/reproducibility.html
10. de Bodt, C., Diaz-Papkovich, A., Kobak, D. et al. (2025). *Low-dimensional embeddings of high-dimensional data.* arXiv:2508.15929 (in `knowledge/papers/methods/`).
11. Kobak, D., Linderman, G. C. (2021). *Initialization is critical for preserving global data structure in both t-SNE and UMAP.* Nature Biotechnology 39: 156-157. https://doi.org/10.1038/s41587-020-00809-z
12. Wattenberg, M., Viégas, F., Johnson, I. (2016). *How to Use t-SNE Effectively.* Distill. https://doi.org/10.23915/distill.00002 (scritto per t-SNE; la documentazione `umap-learn` rimanda allo stesso tipo di cautele [3]).
13. Chari, T., Pachter, L. (2023). *The specious art of single-cell genomics.* PLoS Computational Biology 19(8): e1011288. https://doi.org/10.1371/journal.pcbi.1011288
