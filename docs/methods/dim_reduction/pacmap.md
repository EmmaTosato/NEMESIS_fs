# PaCMAP in NEMESIS

- **Teoria:** [PaCMAP (Pairwise Controlled Manifold Approximation)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/pacmap.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/pacmap.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/pacmap.md) (derivata, non è una fonte)

Funzione `pacmap_embed` in `src/analysis/reduction.py` (`pacmap.PaCMAP(**params).fit_transform(X)`), libreria
[PaCMAP](https://github.com/YingfanWang/PaCMAP) versione 0.9.1 installata nel repo. Parametri: `config/registry/params_reduction.json` (chiave `pacmap`).
Dove la documentazione e il codice installato differiscono, vale il codice, e la differenza è segnalata. Altri metodi: [README](README.md).

## Su cosa lo applichiamo
- **Dati:** `data/derived/lesion_matrix/25-08_s1.2-vol`, 5269 × 264274, `uint8` (binaria).
  Non c'è ancora una run di PaCMAP nel repo (nessuna cartella `pacmap` sotto `results/`, nessuna menzione in `docs/experiments/`).
- **Cosa vede davvero:** con `apply_pca: true` e 264274 colonne, i vicini, le coppie e l'inizializzazione si calcolano sulle prime **100** componenti
  della SVD troncata, non sui voxel. È un metodo "PCA → neighbor embedding" (pipeline ibrida della
  [rassegna sulla riduzione](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/dim_reduction_literature_survey.md), §5).
- **Distanza:** `PaCMAP.__init__` accetta `distance` ∈ {`euclidean`, `manhattan`, `angular`, `hamming`, `dot`} (`VALID_METRICS` nel sorgente 0.9.1);
  il repo non la passa, quindi è euclidea. Con il backend `faiss` di default solo `euclidean`, `angular` e `manhattan` funzionano:
  `hamming` e `dot` sollevano `NotImplementedError` (provato su 0.9.1), e `annoy` non è installato nell'ambiente.
  Non c'è un'opzione Dice o `precomputed`, quindi il confronto `dice`/`euclidean` fatto per UMAP e t-SNE qui non è possibile.
- **Ipotesi "per lesioni binarie la distanza di Hamming potrebbe essere più adatta dell'euclidea":** su vettori 0/1 la distanza di Hamming di PaCMAP
  (numero di posizioni diverse, `hamming_dist` nel sorgente) è uguale all'euclidea al quadrato, quindi ordina i vicini allo stesso modo.
  Le differenze pratiche sarebbero due: con `hamming` la PCA preliminare viene saltata (vicini sui voxel grezzi) e la distanza scalata cambia forma.
  Non dà la proprietà che Dice ha e l'euclidea no (normalizzare per i volumi). Con il backend di default `hamming` non è comunque utilizzabile.
- **Uso a valle:** `n_components` è fisso a 2; un clustering su PaCMAP lavorerebbe su un embedding 2D.

## Parametri usati (significato: documentazione PaCMAP)
| Parametro | Nel progetto |
|---|---|
| `n_neighbors` | base 5; griglia `[5, 10, 20, 50]` |
| `MN_ratio` | 0,5, fisso |
| `FP_ratio` | 2,0, fisso |
| `distance` | non passato, quindi euclidea |
| `apply_pca` | `true` (SVD troncata a 100 componenti prima dei vicini) |
| `lr` | default (1,0) |
| `num_iters` | default (`(100, 100, 250)`, 450 in tutto) |
| `init` (di `fit_transform`) | default (`"pca"`) |
| `n_components` | 2 |
| `random_state` | 0 |
| `knn_backend` | default (`"faiss"`) |

Default verificati sulla firma installata di `pacmap.PaCMAP.__init__`. L'adattamento automatico di `n_neighbors` sopra i 10.000 punti avviene **solo**
con `n_neighbors=None`; il repo passa sempre un numero, e comunque le coorti hanno meno di 10.000 soggetti.

## Come lo ottimizziamo
1. **`n_neighbors`:** è l'unico parametro in griglia (`[5, 10, 20, 50]`).
2. **`MN_ratio` e `FP_ratio`:** fissi ai default.
3. **`lr`, `num_iters`, `init`, `apply_pca`:** `lr`, `num_iters` e `init` ai default; `apply_pca` attivo (default).
4. **Qualità dell'embedding:** trustworthiness (`trustworthiness_n_neighbors: 10`), nessuna selezione automatica.

## Come leggiamo l'output
- **Trustworthiness** a `k = 10`, euclidea sulla matrice grezza (`tuning.py::evaluate_pacmap`). I vicini di PaCMAP vengono però dalla proiezione
  a 100 componenti: il punteggio misura anche quanto quella proiezione ha cambiato i vicini
  ([teoria della valutazione](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/evaluation.md)).
- **Metriche di Wang et al.:** struttura locale con l'accuratezza di un classificatore kNN e SVM sull'embedding, globale con misure su triplette casuali
  e centroidi di classe; richiedono etichette, che qui non ci sono.
- **Confronto qualitativo** con UMAP e t-SNE alla stessa `n_neighbors`: se un gruppo compare in tutti e tre è meno probabile che sia un artefatto di uno solo.

## Attenzioni specifiche
- Il "globale" di PaCMAP non è quello dei dati grezzi: con `apply_pca` il riferimento sono le prime 100 componenti, e su lesioni binarie molto sparse
  la quota di varianza che tengono non è stata misurata.
- Il confronto `dice`/`euclidean` non è possibile; `hamming` e `dot` non funzionano con il backend `faiss`.
- Con `n_components` fisso a 2, un eventuale clustering lavorerebbe su un embedding 2D.
