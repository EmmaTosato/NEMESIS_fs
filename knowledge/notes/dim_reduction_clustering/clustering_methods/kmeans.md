# K-means

> Metodo partizionale: `"kmeans"` in `CLUSTERING_METHODS` (`src/analysis/clustering.py`), implementato con `sklearn.cluster.KMeans` (scikit-learn 1.8.0 nell'ambiente `nemesis`). Parametri in `config/registry/params_clustering.json`, voce `"kmeans"`.
>
> Indice di tutti i metodi: [`README.md`](README.md). Metriche condivise (silhouette, Calinski-Harabasz, Davies-Bouldin, ARI, NMI): [`evaluation_metrics.md`](evaluation_metrics.md).

## 1. Cosa fa

Divide gli $n$ soggetti in $k$ gruppi scelti in anticipo. Ogni gruppo è rappresentato dal suo **centroide**, la media dei punti che contiene, e ogni soggetto va al centroide più vicino in distanza euclidea [1, 2, 6]. Nella tassonomia di Dinh et al. è il metodo di riferimento del clustering **partizionale hard**: una sola partizione, $k$ fissato, ogni punto in un solo cluster [4].

L'algoritmo standard (Lloyd) alterna due passi finché le assegnazioni non cambiano più [1, 6]:

1. **Assegnazione**: ogni punto va al centroide più vicino.
2. **Aggiornamento**: ogni centroide diventa la media dei punti che gli sono stati assegnati.

Il nome "k-means" viene da MacQueen [2], che descrive una versione in cui i centroidi si aggiornano un punto alla volta. Lloyd [1] descrive la versione "a lotti" (prima tutte le assegnazioni, poi tutte le medie), nata per la quantizzazione di un segnale: è quella che scikit-learn chiama `algorithm="lloyd"` [6].

## 2. Perché lo fa: l'obiettivo

K-means minimizza la **somma dei quadrati entro i cluster** (*within-cluster sum of squares*), che scikit-learn chiama **inertia** [6]:

$$
J(C_1,\dots,C_k) \;=\; \sum_{j=1}^{k} \sum_{x_i \in C_j} \lVert x_i - \mu_j \rVert^2,
\qquad
\mu_j = \frac{1}{|C_j|}\sum_{x_i \in C_j} x_i .
$$

Perché i due passi funzionano:

- a centroidi fissi, assegnare ogni punto al centroide più vicino è la scelta che minimizza $J$;
- ad assegnazioni fisse, la media è il punto che minimizza la somma dei quadrati delle distanze dai punti del gruppo.

Ogni passo quindi non fa mai crescere $J$. Le partizioni possibili sono finite, quindi l'algoritmo si ferma, ma in un **minimo locale**, non necessariamente nel migliore [1, 5, 6]. Per questo l'inizializzazione conta.

### Inizializzazione k-means++

Arthur & Vassilvitskii [3] propongono di scegliere i centroidi iniziali così:

1. il primo è un punto dei dati scelto a caso, con probabilità uniforme;
2. ogni centroide successivo è un punto $x$ scelto con probabilità
$$
P(x) = \frac{D(x)^2}{\sum_{x'} D(x')^2},
$$
dove $D(x)$ è la distanza di $x$ dal centroide più vicino tra quelli già scelti;
3. poi si esegue Lloyd normalmente.

La probabilità è proporzionale alla distanza **al quadrato**, non alla distanza semplice. Con questa scelta il valore atteso dell'obiettivo è garantito entro un fattore $O(\log k)$ dall'ottimo: $\mathbb{E}[J] \le 8(\ln k + 2)\,J_{\text{OPT}}$ [3]. Il ciclo di Lloyd successivo può solo migliorarlo.

scikit-learn implementa una variante *greedy* di k-means++: a ogni passo valuta più candidati e tiene quello che riduce di più l'inertia [6].

### Legame con le misture di Gaussiane

K-means si può leggere come la decomposizione dei dati in una mistura di Gaussiane sferiche [9]. È il motivo per cui dà cluster convessi e "tondeggianti": si veda [`gmm.md`](gmm.md) per la versione con covarianze libere.

## 3. Il nostro contesto

- **Input**: un embedding, non la matrice grezza. Le run esistenti usano UMAP a 2, 3 o 10 componenti (sessioni `s1.1-vol`, `s1.2-vol`, `s2.1-schaefer-200-tian-s2`, `s2.2-vol`) e, in produzione, la matrice SDC streamline a 87 colonne (sessione `s2.3-stream`). Su score PCA non è stato lanciato. Il numero di soggetti va da circa 1100 a circa 5800.
- **Distanza**: sempre euclidea (K-means non ne accetta altre). Sugli score PCA la distanza euclidea è quella dello spazio delle componenti. Su UMAP la documentazione ufficiale avverte che l'embedding non conserva del tutto la densità e può creare false separazioni (*false tears*) dentro un cluster vero [10]: K-means prende le distanze dell'embedding così come sono.
- **Scala**: K-means pesa ogni dimensione per la sua varianza. Negli score PCA le prime componenti hanno varianza maggiore e quindi contano di più nella distanza. Se questo sia voluto è una scelta del progetto, non una proprietà del metodo.
- **Costo**: la complessità media è $O(k\,n\,T)$ ($T$ iterazioni) [6]: con $n \approx 5000$, $k \le 30$ e poche dimensioni un fit richiede frazioni di secondo. È il metodo più economico della pipeline.

## 4. Parametri

Default verificati con `inspect.signature(KMeans)` su scikit-learn 1.8.0. "Progetto" è il valore in `params_clustering.json` (scelta del progetto).

| Parametro | Significato | Range | Default sklearn | Progetto |
|---|---|---|---|---|
| `n_clusters` | Numero di cluster e di centroidi [6]. | intero $\ge 1$ (per gli indici serve $\ge 2$) | 8 | base 6; griglia 2-30 |
| `init` | Inizializzazione: `"k-means++"` (sez. 2) o `"random"` ($k$ righe dei dati a caso) [6]. | `"k-means++"`, `"random"`, array, callable | `"k-means++"` | non impostato, quindi `"k-means++"` |
| `n_init` | Quante inizializzazioni diverse; si tiene quella con l'inertia più bassa [6]. | intero $\ge 1$ o `"auto"` | `"auto"` | `"auto"` |
| `max_iter` | Iterazioni massime di Lloyd per inizializzazione [6]. | intero | 300 | default |
| `tol` | Tolleranza relativa sullo spostamento dei centroidi (norma di Frobenius) per dichiarare convergenza [6]. | float | 1e-4 | default |
| `algorithm` | `"lloyd"` (classico) o `"elkan"` (usa la disuguaglianza triangolare, più memoria) [6]. | `"lloyd"`, `"elkan"` | `"lloyd"` | default |
| `random_state` | Seme dell'inizializzazione [6]. | intero o `None` | `None` | 0 |

**Attenzione a `n_init="auto"`**: con `init="k-means++"` vale **1** sola inizializzazione; con `init="random"` vale 10 [6]. Con la configurazione attuale ogni fit è quindi un solo k-means++. La verifica che questo basti è la *stability analysis* (blocco `"stability"`, sezione 5).

## 5. Come si fa il tuning

1. **Stabilità dell'inizializzazione prima di tutto** (blocco `"stability"` in `params_clustering.json`, scelta del progetto): per 3 valori rappresentativi di `n_clusters` (minimo, mediana e massimo della griglia) ripete il fit con `init` in `["k-means++", "random"]`, `n_init` in `[1, 5, 10, 15, 20]` e 5 semi, e registra l'inertia. Se l'inertia varia molto tra semi a `n_init=1`, i valori della sweep principale dipendono dal seme. Lettura: `clustering_tuning_guide.md`, "Stabilità dell'inizializzazione".
2. **Sweep di `n_clusters`** da 2 a 30: per ogni $k$ si calcolano silhouette, Calinski-Harabasz e Davies-Bouldin ([`evaluation_metrics.md`](evaluation_metrics.md)) e l'inertia.
3. **Curva dell'inertia ("gomito")**: $J$ scende sempre al crescere di $k$ (con $k=n$ vale 0), quindi non si cerca il minimo ma il punto in cui la discesa rallenta. È un criterio visivo, senza una regola formale.
4. **Gap statistic** (Tibshirani, Walther & Hastie [7]), disponibile come funzione post-hoc `compute_gap_statistic` in `src/analysis/clustering_tuning.py`, non collegata alla pipeline. Confronta $\log W_k$ dei dati con il suo valore atteso su dati di riferimento senza struttura:
$$
\mathrm{Gap}(k) = \frac{1}{B}\sum_{b=1}^{B}\log W_{kb}^{*} - \log W_k,
$$
dove $W_k$ è l'inertia a $k$ cluster e $W^*_{kb}$ quella del $b$-esimo dataset di riferimento. La regola di scelta di [7] è il più piccolo $k$ con $\mathrm{Gap}(k) \ge \mathrm{Gap}(k+1) - s_{k+1}$, dove $s_{k+1}$ è la deviazione standard dei riferimenti moltiplicata per $\sqrt{1+1/B}$. Il codice usa come riferimento la distribuzione uniforme nel box delle feature, la più semplice delle due proposte in [7] (l'altra allinea il box alle componenti principali).
5. **Stabilità del numero di cluster** (opzionale, blocco `"consensus"`): co-occorrenza tra ripetizioni a semi diversi (RSC) o su sottocampioni (Monti et al. [8]); si veda [`evaluation_metrics.md`](evaluation_metrics.md), sezione 7.

Il tuning non sceglie $k$ da solo (regola del progetto, `clustering_tuning_guide.md`).

## 6. Come si valuta l'output

- **Indici interni** (silhouette, Calinski-Harabasz, Davies-Bouldin): definizioni e limiti in [`evaluation_metrics.md`](evaluation_metrics.md). Silhouette e Calinski-Harabasz premiano cluster convessi e compatti, cioè proprio ciò che K-means costruisce: un valore alto conferma in parte l'assunzione del metodo, non la struttura dei dati.
- **Inertia**: utile solo per confrontare valori di $k$ sullo **stesso** input. Non si confronta tra embedding diversi (scala diversa).
- **Dimensioni dei cluster** e **profili dei centroidi**: un centroide è un punto dell'embedding, interpretabile tornando ai soggetti vicini (nell'Embedding Explorer, `docs/guides/embedding_app.md`).
- **Riproducibilità**: ARI tra le partizioni di semi diversi ([`evaluation_metrics.md`](evaluation_metrics.md)). Un ARI basso tra semi dice che la partizione è uno dei tanti minimi locali.

## 7. Quando usarlo

- Come **baseline** veloce: se un metodo più complesso non fa meglio di K-means, la complessità non è giustificata.
- Quando ci si aspettano gruppi **compatti, convessi e di dimensione simile** [5, 9].
- Non quando i gruppi hanno forme allungate o non convesse, densità molto diverse, o quando molti soggetti dovrebbero restare non assegnati (lì servono HDBSCAN o ADP, [`hdbscan.md`](hdbscan.md), [`adp.md`](adp.md)).

## 8. Pro e contro

**Pro**
- Semplice, veloce, lineare nel numero di punti [5, 6].
- Obiettivo esplicito ($J$), facile da interpretare.
- k-means++ dà una garanzia teorica sulla qualità dell'inizializzazione [3].

**Contro**
- $k$ va fissato in anticipo [5].
- Converge a un minimo locale; l'inizializzazione è cruciale [5, 6].
- Produce solo cluster convessi (celle di Voronoi) [5, 9].
- Solo dati vettoriali numerici e distanza euclidea [5].
- Ogni soggetto viene assegnato, anche un outlier, che sposta il centroide.
- Soffre dell'alta dimensionalità [5]: in pratica si usa su un embedding.

## 9. Esempio semplice

Sei valori in una dimensione: $\{1, 2, 3, 10, 11, 12\}$, $k=2$, centroidi iniziali $\mu_1 = 1$, $\mu_2 = 2$ (una cattiva inizializzazione, due punti vicini).

| Iterazione | Assegnazione | Nuovi centroidi |
|---|---|---|
| 1 | $C_1=\{1\}$, $C_2=\{2,3,10,11,12\}$ | $\mu_1=1$, $\mu_2=7.6$ |
| 2 | $C_1=\{1,2,3\}$ ($3$ dista 2 da $\mu_1$ e 4.6 da $\mu_2$), $C_2=\{10,11,12\}$ | $\mu_1=2$, $\mu_2=11$ |
| 3 | invariata: convergenza | |

Inertia finale: $(1+0+1) + (1+0+1) = 4$. Con k-means++ il secondo centroide sarebbe stato quasi certamente uno dei valori 10-12: per esempio $D(10)^2 = 81$ contro $D(2)^2 = 1$ se il primo centroide è 1.

## 10. Insidie

- **`n_init="auto"` vuol dire 1 fit** con k-means++ [6]: un singolo minimo locale per ogni $k$ della sweep, se la stability analysis non mostra che basta.
- **L'inertia scende sempre**: non indica mai da sola il $k$ giusto.
- **K-means trova sempre $k$ cluster**, anche su dati senza struttura [5]. La domanda "i cluster esistono?" richiede altri controlli (per esempio la gap statistic [7]).
- **Scala delle dimensioni**: dimensioni con varianza grande dominano la distanza (sezione 3).
- **Embedding UMAP**: la densità non è conservata del tutto e possono comparire false separazioni [10]; K-means può spezzare un gruppo vero lungo una di queste.
- **Le etichette non hanno ordine**: il cluster 0 di un seme può essere il cluster 3 di un altro. Per confrontare partizioni si usa l'ARI, mai il confronto diretto delle etichette.
- **Indici che favoriscono il metodo**: silhouette e Calinski-Harabasz premiano la stessa geometria convessa che K-means impone (sezione 6).

## Fonti

1. Lloyd, S. P. (1982). *Least squares quantization in PCM.* IEEE Transactions on Information Theory, 28(2), 129-137. doi:10.1109/TIT.1982.1056489.
2. MacQueen, J. (1967). *Some methods for classification and analysis of multivariate observations.* Proceedings of the 5th Berkeley Symposium on Mathematical Statistics and Probability, vol. 1, 281-297. https://projecteuclid.org/euclid.bsmsp/1200512992.
3. Arthur, D., Vassilvitskii, S. (2007). *k-means++: the advantages of careful seeding.* Proceedings of the 18th ACM-SIAM Symposium on Discrete Algorithms (SODA), 1027-1035. https://dl.acm.org/doi/10.5555/1283383.1283494.
4. Dinh, T., Hauchi, W., Lisik, D., et al. (2025). *Data clustering: an essential technique in data science.* Expert Systems with Applications; arXiv:2412.18760. Copia locale: `knowledge/papers/methods/Dinh et al - 2025 - Data clustering an essential technique in data science/`.
5. Bicego, M. (2021). *Il clustering, parte 2* (dispense del corso "Riconoscimento e Recupero dell'informazione per Bioinformatica", Università di Verona), sezioni "K-means" e "Varianti del K-means". Copia locale: `knowledge/papers/methods/Slides_Bicego/`.
6. scikit-learn 1.8, `sklearn.cluster.KMeans`. https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.KMeans.html (default verificati anche con `inspect.signature` sulla versione installata).
7. Tibshirani, R., Walther, G., Hastie, T. (2001). *Estimating the number of clusters in a data set via the gap statistic.* Journal of the Royal Statistical Society B, 63(2), 411-423. doi:10.1111/1467-9868.00293.
8. Monti, S., Tamayo, P., Mesirov, J., Golub, T. (2003). *Consensus clustering: a resampling-based method for class discovery and visualization of gene expression microarray data.* Machine Learning, 52, 91-118. doi:10.1023/A:1023949509487.
9. Fred, A. L. N., Jain, A. K. (2002). *Data clustering using evidence accumulation.* Proceedings of the 16th International Conference on Pattern Recognition (ICPR), vol. 4, 276-280. doi:10.1109/ICPR.2002.1047450. Copia locale: `knowledge/papers/methods/Fred et al - 2002 - Data clustering using evidence accumulation/`.
10. McInnes, L., et al. *UMAP documentation: Using UMAP for clustering.* https://umap-learn.readthedocs.io/en/latest/clustering.html (copia locale: `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`).
