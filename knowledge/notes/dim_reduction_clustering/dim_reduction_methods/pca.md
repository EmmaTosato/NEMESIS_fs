# PCA (analisi delle componenti principali)

Indice dei metodi: [README.md](README.md). La spiegazione passo per passo (pesi e punteggi, scree plot, metodo degli snapshot, covarianza o correlazione) è in [`../employed_dim_reduction_methods.md`](../employed_dim_reduction_methods.md), sezione "PCA e rotazione varimax": qui non si ripete, si richiama. La rotazione è in [pca_varimax.md](pca_varimax.md).

## 1. Cosa fa

Trova nuovi assi ortogonali, le componenti principali, ordinati per quanta variabilità dei soggetti catturano; ogni soggetto si riassume con le sue coordinate (i punteggi) sulle prime *k* componenti [1, 2, 3]. Ogni componente è una combinazione lineare esplicita delle variabili originali (qui: i voxel), quindi si può riportare sul cervello come mappa [3].

## 2. Perché lo fa: l'obiettivo matematico

Sia $X_c$ la matrice $n \times p$ con le colonne centrate. Due formulazioni equivalenti:

- **Massima varianza** (Hotelling 1933 [2]): la prima componente è il vettore unitario che massimizza la varianza dei punteggi,

$$
\mathbf{w}_1 = \arg\max_{\|\mathbf{w}\|=1} \mathbf{w}^\top C\, \mathbf{w}, \qquad C = \frac{X_c^\top X_c}{n-1},
$$

  le successive fanno lo stesso con il vincolo di essere ortogonali alle precedenti. La soluzione sono gli autovettori di $C$, ordinati per autovalore $\lambda_1 \ge \lambda_2 \ge \dots$; $\lambda_j$ è la varianza della componente *j* [3].

- **Miglior sottospazio approssimante** (Pearson 1901 [1]): le prime *k* componenti definiscono il sottospazio di dimensione *k* che minimizza l'errore quadratico di ricostruzione,

$$
\min_{W \in \mathbb{R}^{p\times k},\ W^\top W = I} \ \big\| X_c - X_c W W^\top \big\|_F^2 .
$$

Con la SVD $X_c = U S V^\top$ le componenti sono le colonne di $V$, i punteggi sono $T = X_c V = U S$ e $\lambda_j = s_j^2/(n-1)$ [3]. La quota di varianza spiegata dalle prime *k* è

$$
\frac{\sum_{j=1}^{k} \lambda_j}{\sum_{j} \lambda_j}.
$$

Il problema agli autovalori ha un **ottimo globale** e non dipende da inizializzazioni: a parità di dati il risultato è unico, a meno del segno di ogni componente (e di rotazioni dentro autovalori ripetuti) [3].

**Matrici più larghe che alte.** Con $p > n$ gli autovalori non nulli di $X_c^\top X_c$ ($p \times p$) e di $X_c X_c^\top$ ($n \times n$, la matrice di Gram) coincidono, e $V = X_c^\top U S^{-1}$: basta decomporre la matrice piccola. È il metodo degli snapshot di Sirovich 1987 [4]; il dettaglio è in `employed_dim_reduction_methods.md` e in [`docs/dev/covariance_pca.md`](../../../../docs/dev/covariance_pca.md). Dopo il centraggio le componenti con varianza non nulla sono al massimo $n-1$ [3].

## 3. Il nostro contesto

- **Dimensioni.** Le matrici voxel-wise hanno $n \approx 5000$-5800 e $p \approx$ 220-290 mila: la covarianza $p \times p$ (circa 413 GB in float64 per $p = 227.235$) non entra in memoria, quindi il repo usa la via duale ($n \times n$) con `solver: "blocks"` (`src/analysis/covariance_pca.py`). Le matrici parcellate o per tratto ($p$ = 87 o 232) usano la covarianza tra variabili (`dual: false`). Scelta e numeri: [`docs/guides/dim_reduction.md`](../../../../docs/guides/dim_reduction.md), "Il metodo `pca`".
- **Disconnettoma (continuo, [0, 1]).** Si usa la covarianza, non la correlazione: tutte le variabili sono probabilità sulla stessa scala, e standardizzando i voxel quasi sempre a zero peserebbero quanto gli altri. È anche la scelta di Thiebaut de Schotten et al. 2020 ("a PCA using a covariance matrix") [5]; la motivazione è del progetto.
- **Lesioni (binarie).** La PCA si applica, ma su dati 0/1 la varianza di un voxel è $q(1-q)$, con $q$ la frequenza di lesione in quel voxel: le componenti sono dominate dai voxel colpiti più spesso e, poiché lesioni grandi coprono molti voxel insieme, la prima componente tende a misurare il volume (osservazione da verificare caso per caso con l'R² con il volume, come fa Thiebaut de Schotten et al. 2020 [5]; vedi `employed_dim_reduction_methods.md`, "Quanto dipende dal volume della lesione").
- **Uso a valle.** I punteggi PCA sono l'ingresso del clustering; per quello scopo il progetto usa le componenti non ruotate (`employed_dim_reduction_methods.md`, "Quando usare cosa").

## 4. I parametri

Il metodo `pca` del repo ha un suo contratto (`src/analysis/pca_method.py`), con due solutori.

| Parametro (`params_reduction.json`) | Significato | Valori nel repo | Riferimento in libreria |
|---|---|---|---|
| `solver` | `"blocks"`: PCA propria a blocchi di colonne; `"sklearn"`: `sklearn.decomposition.PCA(svd_solver="full")` su una copia in memoria | `"blocks"` | default di sklearn: `svd_solver="auto"` (sceglie tra `covariance_eigh`, `randomized` e `full` in base alla forma di X) [6] |
| `standardize` | `false`: covarianza (solo centraggio); `true`: correlazione (divide per la deviazione standard) | `false` | sklearn non standardizza: serve `StandardScaler` a monte [6] |
| `dual` | solo `blocks`: `true` decompone la matrice $n\times n$, `false` quella $p\times p$; stessi risultati [4] | `true` sulle voxel-wise | — |
| `n_components` o `variance_share` | quante componenti tenere: un numero, o il minimo che raggiunge una quota di varianza | `150` (lesione), `12` (SDC, con varimax) | sklearn: `n_components=None` tiene tutte le componenti [6] |
| `rotation` | `"none"` qui; le rotazioni sono in [pca_varimax.md](pca_varimax.md) | `"none"` | — |
| `chunk_columns`, `max_matrix_gib` | solo memoria: colonne per blocco (16384) e soglia della matrice quadrata (8 GiB) | default del modulo | — |

`whiten` di sklearn (default `False`) riscala i punteggi a varianza 1 e toglie l'informazione sulla varianza relativa delle componenti [6]; il repo non lo usa.

## 5. Come si fa il tuning

L'unico iperparametro di sostanza è **quante componenti tenere**; la decomposizione è una sola e non cambia con *k* (il repo la calcola una volta per sweep, `model_cache`).

- **Soglia di varianza cumulata**: si tengono le componenti fino a una quota fissata. Per Jolliffe & Cadima il 70% è "a common, if subjective, cut-off point" [3]. Thiebaut de Schotten et al. 2020 usano "più del 90%" [5]; nel repo è `variance_share: 0.9` o la griglia su `n_components`.
- **Scree plot** (Cattell 1966 [7]): si cerca il gomito dove la curva degli autovalori si appiattisce. È una lettura visiva, non un numero.
- **Criterio di Kaiser** (Kaiser 1960 [13]: autovalore maggiore di 1 sulla matrice di correlazione) e **parallel analysis** (Horn 1965 [8]: si tengono le componenti con autovalore superiore a quello di dati casuali delle stesse dimensioni) sono le alternative classiche. Il repo non le implementa.
- Nel repo la griglia è su `n_components` (da 2 a 150 per le lesioni) e lo spettro intero è salvato (`eigenvalues.npz`), da cui `notebooks/post-results_analysis/pca_evaluation.ipynb` disegna lo scree plot. Nessuna scelta automatica.

## 6. Come si valuta l'output

- **Varianza spiegata** cumulata delle componenti tenute: la misura del tuning (`cumulative_explained_variance`) [3]. Vedi [evaluation.md](evaluation.md).
- **Dipendenza da variabili note**: R² delle componenti con volume e lato della lesione (`employed_dim_reduction_methods.md`).
- **Riproducibilità**: correlazione delle mappe stimate su due metà dei soggetti, come in [5].
- Come visualizzazione in 2D la PCA è forte sul globale e debole sul locale: nel confronto di de Bodt et al. t-SNE ha la qualità locale più alta, PCA e MDS la qualità globale più alta [9, §4].

## 7. Quando usarla

- Quando servono componenti **interpretabili** (mappe di pesi) e un risultato **deterministico** [3].
- Come primo passo di **riduzione del rumore** prima di un metodo non lineare: è la prassi indicata da scikit-learn per t-SNE ("e.g. 50" componenti) [10] e dalla FAQ di `umap-learn` [11]; de Bodt et al. avvertono che scartare molta varianza in questo passo cambia il risultato [9, §5 punto 4].
- Quando conta la **struttura globale** (distanze grandi, gradienti continui) più dei vicinati fini [9].
- Non quando la struttura è non lineare (varietà curve, cluster non separabili linearmente) [3, 9].

## 8. Pro e contro

| Pro | Contro |
|---|---|
| Ottimo globale, deterministica, nessun seed [3] | Solo relazioni lineari [3] |
| Componenti ordinate per varianza: le prime *k* sono un riassunto legittimo (a differenza di UMAP/t-SNE, `lessons_learned.md` #16) | Sensibile a valori estremi ("a few outlying observations may have a disproportionate effect") e alle unità di misura delle variabili (con la covarianza) [3] |
| Pesi interpretabili come mappe | Ogni componente mescola molte variabili: per leggerle si ruota ([pca_varimax.md](pca_varimax.md)) |
| Proietta soggetti nuovi con gli stessi pesi | Componenti ortogonali per costruzione (definizione), non necessariamente processi distinti nei dati |
| Costo controllabile anche con $p \gg n$ (snapshot) [4] | Con *k* piccolo in 2D si perde quasi tutta la struttura locale [9] |

## 9. Un esempio semplice

Tre soggetti, due voxel (già centrati): (2, 2), (0, 0), (−2, −2). Tutta la variabilità sta lungo la diagonale: la prima componente è $\mathbf{w}_1 = (1/\sqrt2, 1/\sqrt2)$ con $\lambda_1 = (8+0+8)/2 = 8$, la seconda è $(1/\sqrt2, -1/\sqrt2)$ con $\lambda_2 = 0$. Una sola componente spiega il 100% della varianza; i punteggi sono $2\sqrt2$, 0, $-2\sqrt2$. Un esempio numerico con pesi e punteggi su tre voxel è in `employed_dim_reduction_methods.md`, "I passi".

## 10. Insidie note

- **Il segno è arbitrario**: "the signs of all loadings (and scores) are arbitrary" [3]; il repo fissa una convenzione per le mappe.
- **La varianza non è rilevanza**: una componente con molta varianza può misurare un confondente (il volume) [5].
- **Autovalori uguali**: l'ordine e la scelta delle componenti sono unici solo se i valori singolari sono distinti [3].
- **Clustering sui punteggi**: le distanze euclidee tra punteggi PCA non ruotati sono quelle del sottospazio, quindi le componenti con più varianza pesano di più. Con `whiten` o con i punteggi ruotati (varianza 1) tutte pesano uguale, anche quelle di poca varianza [6] (vedi [pca_varimax.md](pca_varimax.md)).
- **PCA prima di un metodo a densità**: nell'esempio della documentazione `umap-learn` su MNIST, HDBSCAN dopo una PCA a 50 componenti classifica solo il 17% dei punti, il resto è rumore [12]. La densità in decine di dimensioni è rada.
- **Autovalori piccoli** calcolati per la via duale sono meno precisi; non si usano oltre la soglia di varianza (`employed_dim_reduction_methods.md`, "Limite numerico").

## Fonti

1. Pearson, K. (1901). *On lines and planes of closest fit to systems of points in space.* The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science 2(11): 559-572. https://doi.org/10.1080/14786440109462720
2. Hotelling, H. (1933). *Analysis of a complex of statistical variables into principal components.* Journal of Educational Psychology 24(6): 417-441. https://doi.org/10.1037/h0071325
3. Jolliffe, I. T., Cadima, J. (2016). *Principal component analysis: a review and recent developments.* Phil. Trans. R. Soc. A 374: 20150202. https://doi.org/10.1098/rsta.2015.0202
4. Sirovich, L. (1987). *Turbulence and the dynamics of coherent structures. Part I: Coherent structures.* Quarterly of Applied Mathematics 45(3): 561-571. https://doi.org/10.1090/qam/910462
5. Thiebaut de Schotten, M., Foulon, C., Nachev, P. (2020). *Brain disconnections link structural connectivity with function and behaviour.* Nature Communications 11. https://doi.org/10.1038/s41467-020-18920-9 (Methods, "Data compression").
6. scikit-learn 1.8, `sklearn.decomposition.PCA`. https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html
7. Cattell, R. B. (1966). *The scree test for the number of factors.* Multivariate Behavioral Research 1(2): 245-276. https://doi.org/10.1207/s15327906mbr0102_10
8. Horn, J. L. (1965). *A rationale and test for the number of factors in factor analysis.* Psychometrika 30: 179-185. https://doi.org/10.1007/BF02289447
9. de Bodt, C., Diaz-Papkovich, A., Kobak, D. et al. (2025). *Low-dimensional embeddings of high-dimensional data.* arXiv:2508.15929 (in `knowledge/papers/methods/`).
10. scikit-learn 1.8, `sklearn.manifold.TSNE` (descrizione della classe). https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
11. umap-learn, *Frequently Asked Questions*. https://umap-learn.readthedocs.io/en/latest/faq.html
12. umap-learn, *Using UMAP for Clustering*. https://umap-learn.readthedocs.io/en/latest/clustering.html (copia in `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`).
13. Kaiser, H. F. (1960). *The application of electronic computers to factor analysis.* Educational and Psychological Measurement 20(1): 141-151. https://doi.org/10.1177/001316446002000116
