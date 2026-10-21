# PaCMAP (Pairwise Controlled Manifold Approximation)

Indice dei metodi: [README.md](README.md). Fonte del metodo: Wang et al. 2021 [1]; libreria [github.com/YingfanWang/PaCMAP](https://github.com/YingfanWang/PaCMAP) [2], versione installata nel repo: 0.9.1. Implementazione nel repo: `pacmap_embed` in `src/analysis/reduction.py` (`pacmap.PaCMAP(**params).fit_transform(X)`), parametri in `config/registry/params_reduction.json` (chiave `pacmap`). Dove la documentazione e il codice installato differiscono, vale il codice, e la differenza è segnalata.

## 1. Cosa fa

- Metodo di riduzione dimensionale pensato per la visualizzazione in 2D o 3D [1, 2].
- Scopo dichiarato: preservare **insieme struttura locale e globale**. UMAP e t-SNE tendono a privilegiare la prima [1].
- Invece di un grafo pesato di tutti i vicini usa tre insiemi di **coppie di punti**, ognuno con un ruolo:
  - *neighbor pairs*: i vicini più prossimi, per la struttura locale;
  - *mid-near pairs*: punti a distanza intermedia, per la struttura globale;
  - *further pairs*: punti scelti a caso e lontani, che vengono respinti [1, 2].

## 2. Perché lo fa: l'obiettivo matematico

Wang et al. 2021 analizzano t-SNE, UMAP e TriMap come sistemi di forze tra coppie e ricavano i principi che una funzione di costo deve rispettare per conservare sia il locale sia il globale; PaCMAP è costruito su quei principi [1].

**Le coppie** (verificato sul sorgente 0.9.1):

- *neighbor*: tra i `n_neighbors + 50` vicini euclidei di *i* si tengono i `n_neighbors` con la distanza scalata più piccola,
$$
d^{\,2,\text{sel}}_{ij} = \frac{\|\mathbf x_i - \mathbf x_j\|^2}{\sigma_i\,\sigma_j}, \qquad \sigma_i = \text{distanza media di } i \text{ dal 4°, 5° e 6° vicino},
$$
  una normalizzazione per la densità locale simile a quella di UMAP e t-SNE;
- *mid-near*: per ognuna delle `round(n_neighbors · MN_ratio)` coppie si estraggono 6 punti a caso e si prende il secondo più vicino;
- *further*: `round(n_neighbors · FP_ratio)` punti estratti a caso, esclusi i vicini.

**Il costo.** Con $\tilde d_{ij} = \|\mathbf y_i - \mathbf y_j\|^2 + 1$ nell'embedding [1, sorgente]:

$$
\mathcal L = w_{NB}\!\!\sum_{(i,j)\in NB}\!\frac{\tilde d_{ij}}{10 + \tilde d_{ij}} \;+\; w_{MN}\!\!\sum_{(i,j)\in MN}\!\frac{\tilde d_{ij}}{10000 + \tilde d_{ij}} \;+\; w_{FP}\!\!\sum_{(i,j)\in FP}\!\frac{1}{1 + \tilde d_{ij}} .
$$

I primi due termini crescono con la distanza (attrazione), il terzo decresce (repulsione). La costante 10000 rende l'attrazione mid-near quasi lineare su un raggio ampio: agisce a scala globale.

**I pesi cambiano in tre fasi** (`num_iters=(100, 100, 250)`, `find_weight` nel sorgente):

| Fase | Iterazioni | $w_{MN}$ | $w_{NB}$ | $w_{FP}$ | Ruolo |
|---|---|---|---|---|---|
| 1 | 0-100 | da 1000 a 3, lineare | 2 | 1 | fissare la struttura globale |
| 2 | 100-200 | 3 | 3 | 1 | bilanciare |
| 3 | 200-450 | 0 | 1 | 1 | rifinire il locale |

**Ottimizzatore.** Il sorgente 0.9.1 aggiorna l'embedding con **Adam** (`update_embedding_adam`, $\beta_1 = 0{,}9$, $\beta_2 = 0{,}999$) e il log verboso stampa `opt_method='adam'`; il README descrive `lr` come "learning rate of the AdaGrad optimizer" [2]. Vale il codice.

**Altre tecniche** [2]:

- **Inizializzazione con PCA** (`init="pca"` di default, passato a `fit_transform`, non al costruttore).
- **Ricerca dei vicini con FAISS** (`knn_backend="faiss"` di default; Annoy non è più mantenuto).
- **PCA preliminare** (`apply_pca=True`): se le variabili sono più di 100 e `distance` non è `hamming`, i dati vengono centrati e ridotti con `TruncatedSVD(n_components=100)` prima di cercare i vicini (sorgente, `preprocess_X`). "Using PCA to preprocess the data can largely accelerate the DR process without losing too much accuracy" [2].

## 3. Il nostro contesto

- **Dati.** `data/derived/lesion_matrix/25-08_s1.2-vol`: 5269 × 264274, `uint8` (binaria). Non c'è ancora una run di PaCMAP nel repo (nessuna cartella `pacmap` sotto `results/`, nessuna menzione in `docs/experiments/`).
- **Cosa vede davvero PaCMAP.** Con `apply_pca: true` e 264274 colonne, i vicini, le coppie e l'inizializzazione si calcolano sulle prime **100** componenti della SVD troncata, non sui voxel. È un metodo "PCA → neighbor embedding" (la pipeline ibrida di `../dim_reduction_literature_survey.md`, §5).
- **Distanza.** `PaCMAP.__init__` accetta `distance` ∈ {`euclidean`, `manhattan`, `angular`, `hamming`, `dot`} (elenco `VALID_METRICS` nel sorgente 0.9.1); il repo non lo passa, quindi è euclidea. Non c'è un'opzione Dice o `precomputed`, quindi il confronto `dice`/`euclidean` fatto per UMAP e t-SNE qui non è possibile.
- **Ipotesi annotata in precedenza** ("per lesioni binarie la distanza di Hamming potrebbe essere più adatta dell'euclidea"): su vettori 0/1 la distanza di Hamming di PaCMAP (il numero di posizioni diverse, `hamming_dist` nel sorgente) è uguale all'euclidea al quadrato, quindi ordina i vicini allo stesso modo. Le differenze pratiche sarebbero due: con `hamming` la PCA preliminare viene saltata (vicini sui voxel grezzi) e la distanza scalata cambia forma. Non dà la proprietà che Dice ha e l'euclidea no (normalizzare per i volumi).
- **Uso a valle.** `n_components` è fisso a 2: un clustering su PaCMAP lavorerebbe su un embedding 2D (vedi §10).

## 4. I parametri

| Parametro | Default libreria [2] | Nel repo | Effetto |
|---|---|---|---|
| `n_neighbors` | 10; con `None` si sceglie da solo: 10 se $n \le 10000$, altrimenti $10 + 15(\log_{10} n - 4)$ [2] | base 5; griglia `[5, 10, 20, 50]` | dimensione dell'insieme delle coppie vicine |
| `MN_ratio` | 0,5 | 0,5, fisso | coppie mid-near per vicino |
| `FP_ratio` | 2,0 | 2,0, fisso | coppie further per vicino |
| `distance` | `"euclidean"` | non passato, quindi euclidea | metrica dei vicini (§3) |
| `apply_pca` | `True` | `true` | SVD troncata a 100 componenti prima dei vicini |
| `lr` | 1,0 | default | passo dell'ottimizzatore |
| `num_iters` | `(100, 100, 250)`, 450 in tutto; "450 iterations is enough for most dataset to converge" [2] | default | durata delle tre fasi |
| `init` (di `fit_transform`) | `"pca"` | default | inizializzazione |
| `n_components` | 2 | 2 | dimensioni dell'embedding |
| `random_state` | `None` | 0 | seed |
| `knn_backend` | `"faiss"` | default | libreria per i vicini |

Default verificati sulla firma installata di `pacmap.PaCMAP.__init__`. L'adattamento automatico di `n_neighbors` sopra i 10.000 punti avviene **solo** con `n_neighbors=None`; il repo passa sempre un numero, e comunque le coorti hanno meno di 10.000 soggetti.

## 5. Come si fa il fine-tuning

- `n_neighbors` è il parametro concettuale, come per UMAP: controlla quanto locale è la struttura conservata [1, 2]. Nel repo è l'unico in griglia.
- `MN_ratio` e `FP_ratio` bilanciano locale e globale: più mid-near spinge verso il globale, più further separa di più i gruppi [1, 2]. Nel repo sono fissi ai default.
- `lr`, `num_iters`, `init`, `apply_pca`: di solito poco effetto; de Bodt et al. raccomandano di lasciare i parametri tecnici ai default [3, §5 punto 6].
- Qualità dell'embedding nel tuning: trustworthiness (`trustworthiness_n_neighbors: 10`), nessuna selezione automatica.

## 6. Come si valuta l'output

- **Trustworthiness** a `k = 10`, euclidea sulla matrice grezza (`tuning.py::evaluate_pacmap`). I vicini di PaCMAP vengono però dalla proiezione a 100 componenti (§3): il punteggio misura anche quanto quella proiezione ha cambiato i vicini. Vedi [evaluation.md](evaluation.md).
- Wang et al. valutano la struttura locale con l'accuratezza di un classificatore kNN e SVM sull'embedding e la globale con misure su triplette casuali e centroidi di classe [1]; richiedono etichette, che qui non ci sono.
- Confronto qualitativo con UMAP e t-SNE alla stessa `n_neighbors`: se un gruppo compare in tutti e tre è meno probabile che sia un artefatto di uno solo [3, §5 punto 5].

## 7. Quando usarlo

- Come **terzo metodo** di controllo accanto a UMAP e t-SNE: un obiettivo diverso (coppie mid-near) che dichiara di conservare meglio il globale [1].
- Quando servono embedding 2D veloci su molti punti: la PCA preliminare e il numero fisso di coppie lo rendono rapido [2].
- Non con una metrica non euclidea specifica (Dice, distanze precalcolate): non è supportata (§3).

## 8. Pro e contro

| Pro | Contro |
|---|---|
| Obiettivo esplicito per locale e globale [1] | Su dati molto larghi lavora sulle prime 100 componenti, non sui dati (§3) |
| Pochi parametri, default stabili [2] | Nessuna metrica Dice/Jaccard né `precomputed` |
| Inizializzazione PCA di default, deterministica a parità di seed | Letteratura indipendente molto più ridotta di UMAP e t-SNE |
| Veloce [1, 2] | Stesse cautele dei neighbor embedding su distanze e densità (§10) |

## 9. Un esempio semplice

Con `n_neighbors = 5`, `MN_ratio = 0,5`, `FP_ratio = 2`: ogni soggetto ha 5 coppie vicine, `round(2,5)` = 2 coppie mid-near e 10 coppie further. Nelle prime 100 iterazioni il peso delle mid-near parte da 1000: il layout si organizza prima per "da che parte del cervello" e solo nelle ultime 250, quando quel peso è 0, ogni soggetto si avvicina ai suoi 5 vicini veri. Su `25-08_s1.2-vol` sono circa 5269 × 17 ≈ 90 mila coppie in tutto, contro i 13,9 milioni di coppie di una matrice di distanze completa.

## 10. Insidie note

- **Vale tutto ciò che vale per i neighbor embedding.** Distanze tra cluster e dimensioni dei cluster non vanno interpretate [3, §5 punto 9]; un'analisi a valle su un embedding 2D è sconsigliata [3, §5 punto 10].
- **Il globale dichiarato non è il globale dei dati grezzi.** Con `apply_pca` il riferimento sono le prime 100 componenti; su lesioni binarie molto sparse la quota di varianza che tengono non è stata misurata.
- **Stocasticità.** Il campionamento delle coppie mid-near e further è casuale: seed diversi danno coppie diverse [2].
- **Clustering a valle**: [`../challenge_of_clustering_after_dim_reduction.md`](../challenge_of_clustering_after_dim_reduction.md).

## Fonti

1. Wang, Y., Huang, H., Rudin, C., Shaposhnik, Y. (2021). *Understanding How Dimension Reduction Tools Work: An Empirical Approach to Deciphering t-SNE, UMAP, TriMap, and PaCMAP for Data Visualization.* Journal of Machine Learning Research 22(201): 1-73. http://jmlr.org/papers/v22/20-1061.html
2. PaCMAP, README e sorgente della versione 0.9.1. https://github.com/YingfanWang/PaCMAP
3. de Bodt, C., Diaz-Papkovich, A., Kobak, D. et al. (2025). *Low-dimensional embeddings of high-dimensional data.* arXiv:2508.15929 (in `knowledge/papers/methods/`).
