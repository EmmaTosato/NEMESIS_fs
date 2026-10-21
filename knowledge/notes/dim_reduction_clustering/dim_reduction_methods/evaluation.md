# Come si valuta un embedding

Nota comune ai metodi di [README.md](README.md). Spiega le misure di qualità che la letteratura usa per un embedding, con le formule, e dice quali calcola oggi il repo. Per come si leggono i numeri del tuning nel progetto: [`../dim_reduction_tuning_guide.md`](../dim_reduction_tuning_guide.md).

## Il problema

Un embedding non ha un "valore vero" con cui confrontarsi. Si può solo misurare quanto conserva una proprietà dei dati originali: i vicini, i ranghi delle distanze, le distanze stesse, la varianza. Misure diverse premiano metodi diversi: nel confronto di de Bodt et al. 2025 t-SNE ha la qualità locale più alta e PCA/MDS la qualità globale più alta, su tutti e quattro i dataset [1, §4 e Tabella 2]. Gli stessi autori notano che i valori assoluti sono difficili da interpretare, perché il massimo raggiungibile su un dato dataset non è noto [1, §6.3].

Notazione: *n* soggetti, $\delta_{ij}$ distanza nello spazio originale, $d_{ij}$ distanza nell'embedding, $\nu_i^k$ e $n_i^k$ gli insiemi dei *k* vicini più prossimi di *i* nello spazio originale e nell'embedding, $r(i,j)$ il rango di *j* tra i vicini di *i* nello spazio originale, $\hat r(i,j)$ lo stesso rango nell'embedding.

## Misure locali: chi è vicino a chi

### Trustworthiness

Penalizza le **intrusioni**: punti che sono tra i *k* vicini nell'embedding ma non lo erano nello spazio originale, in proporzione a quanto erano lontani [2, 3]:

$$
T(k) = 1 - \frac{2}{nk(2n-3k-1)} \sum_{i=1}^{n} \sum_{j \in n_i^k \setminus \nu_i^k} \big(r(i,j) - k\big)
$$

Vale 1 quando non ci sono intrusioni. `sklearn.manifold.trustworthiness` la implementa con `n_neighbors=5` di default e richiede $k < n/2$ perché il valore resti in [0, 1] [3]; il suo argomento `metric` decide come si calcolano i ranghi $r(i,j)$ nello spazio originale (anche `"precomputed"`) [3].

### Continuity

È la misura simmetrica: penalizza le **omissioni**, punti vicini nello spazio originale che l'embedding ha allontanato [2, 4]:

$$
C(k) = 1 - \frac{2}{nk(2n-3k-1)} \sum_{i=1}^{n} \sum_{j \in \nu_i^k \setminus n_i^k} \big(\hat r(i,j) - k\big)
$$

scikit-learn non la implementa; si ottiene dalla stessa funzione scambiando i due spazi, cioè chiamando `trustworthiness` con l'embedding come "spazio originale" e i dati come "embedding" (deduzione dalla definizione, non una funzione della libreria). Trustworthiness alta e continuity bassa vuol dire: quello che si vede vicino è affidabile, ma alcuni vicini veri sono stati separati. È esattamente il caso delle "false tears" di UMAP e t-SNE (vedi le note dei singoli metodi).

### Conservazione dei *k* vicini (kNN preservation)

La quota media di vicini condivisi tra i due spazi [1, §8; 5]:

$$
Q(k) = \frac{1}{n} \sum_{i=1}^{n} \frac{|\nu_i^k \cap n_i^k|}{k}
$$

Con $k = 10$ è la misura "KNN" di Kobak & Berens 2019, che la usano per la struttura locale [5], e l'asse *x* della Figura 7 di de Bodt et al. [1]. Un embedding casuale dà in media $k/(n-1)$; la versione riscalata

$$
R(k) = \frac{(n-1)\,Q(k) - k}{n-1-k}
$$

vale 0 al caso e 1 per una conservazione perfetta (de Bodt et al. seguono Lee et al. 2015) [1, §8]. L'area sotto $R(k)$ con l'asse *k* in scala logaritmica riassume tutte le scale in un numero ("AUC" di [1, §8]).

**Ordine di grandezza.** In de Bodt et al. la conservazione dei 10 vicini in 2D va da 0,02-0,04 per PCA a 0,20-0,46 per t-SNE [1, Tabella 2]. Chari & Pachter 2023 riportano, su dati single-cell, distanze di Jaccard tra gli insiemi dei 30 vicini nei due spazi quasi sempre sopra 0,7 [7]. In 2D la maggior parte dei vicini veri si perde comunque: un valore basso è la norma, non un errore.

## Misure globali: le distanze

- **Correlazione delle distanze**: correlazione (di Pearson in [1], di Spearman per la "CPD" di [5]) tra tutte le $\delta_{ij}$ e le $d_{ij}$, o tra un campione. Misura la struttura globale [1, §8; 5].
- **σ-distortion**: varianza dei rapporti $\rho_{ij} = d_{ij}/\delta_{ij}$ normalizzati per la loro media; non dipende dalla scala dell'embedding [1, §8].
- **KNC** (Kobak & Berens): quota dei 10 centroidi di classe più vicini conservata. Richiede classi note [5]; nel nostro caso le classi non ci sono.

## Varianza spiegata (solo PCA)

Per la PCA la misura nativa è la quota di varianza delle prime *k* componenti, $\sum_{j \le k} \lambda_j / \sum_j \lambda_j$ [8]. Non ha equivalente per t-SNE, UMAP e PaCMAP, che non sono decomposizioni [1, §6.1]. Una rotazione ortogonale non cambia la varianza totale delle *k* componenti tenute (vedi [pca_varimax.md](pca_varimax.md)).

## Cosa calcola il repo

| Metodo | Misura nel tuning (`tuning_results.csv`) | Spazio originale usato per i ranghi |
|---|---|---|
| `umap`, `tsne` | trustworthiness, `trustworthiness_n_neighbors: 10` | la stessa matrice di distanze precalcolata usata per l'embedding (`dice` o `euclidean`) |
| `pacmap` | trustworthiness, `trustworthiness_n_neighbors: 10` | euclidea sulla matrice grezza |
| `pca` | varianza cumulata spiegata | — |

Implementazione: `src/analysis/tuning.py` (`evaluate_umap`, `evaluate_tsne`, `evaluate_pacmap`, `evaluate_pca`). Scelte del progetto:

- `k = 10` è una scelta del progetto (il default di scikit-learn è 5 [3]).
- La continuity, la conservazione dei vicini $Q(k)$/$R(k)$ e la correlazione delle distanze **non** sono calcolate. Una trustworthiness alta non dice quindi nulla sulle omissioni.
- Per `pacmap` i ranghi originali sono euclidei sulla matrice grezza, mentre PaCMAP costruisce i suoi vicini su una proiezione a 100 componenti (vedi [pacmap.md](pacmap.md)): il punteggio è coerente nella metrica ma misura i vicini di uno spazio leggermente diverso da quello che PaCMAP ha visto.
- La trustworthiness cresce con le dimensioni dell'embedding: si confronta solo a parità di `n_components` ([`../dim_reduction_tuning_guide.md`](../dim_reduction_tuning_guide.md)).

## Fonti

1. de Bodt, C., Diaz-Papkovich, A., Kobak, D. et al. (2025). *Low-dimensional embeddings of high-dimensional data.* arXiv:2508.15929 (in `knowledge/papers/methods/`).
2. Venna, J., Kaski, S. (2001). *Neighborhood preservation in nonlinear projection methods: an experimental study.* In: ICANN 2001, Springer, pp. 485-491 (riferimento [1] della documentazione di `trustworthiness` di scikit-learn).
3. scikit-learn 1.8, `sklearn.manifold.trustworthiness`. https://scikit-learn.org/stable/modules/generated/sklearn.manifold.trustworthiness.html
4. Venna, J., Kaski, S. (2006). *Local multidimensional scaling.* Neural Networks 19(6-7): 889-899. https://doi.org/10.1016/j.neunet.2006.05.014
5. Kobak, D., Berens, P. (2019). *The art of using t-SNE for single-cell transcriptomics.* Nature Communications 10: 5416. https://doi.org/10.1038/s41467-019-13056-x
6. Lee, J. A., Verleysen, M. (2009). *Quality assessment of dimensionality reduction: rank-based criteria.* Neurocomputing 72(7-9): 1431-1443. https://doi.org/10.1016/j.neucom.2008.12.017
7. Chari, T., Pachter, L. (2023). *The specious art of single-cell genomics.* PLoS Computational Biology 19(8): e1011288. https://doi.org/10.1371/journal.pcbi.1011288
8. Jolliffe, I. T., Cadima, J. (2016). *Principal component analysis: a review and recent developments.* Phil. Trans. R. Soc. A 374: 20150202. https://doi.org/10.1098/rsta.2015.0202
